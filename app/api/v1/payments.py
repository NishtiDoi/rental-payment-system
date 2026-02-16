from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.transaction import Transaction, TransactionStatus
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.services.payment_service import PaymentService
from uuid import uuid4

router = APIRouter()

@router.post("/", response_model=TransactionResponse, status_code=201)
def initiate_payment(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """
    Initiate a payment transaction
    
    Supports idempotency via:
    1. Idempotency-Key HTTP header (preferred): Standard professional APIs like Stripe use headers, the client sends te key in the background of the request 
    2. idempotency_key in request body : if the header is missing, the code falls back to the key inside the JSON body
            Logic: The transaction: TransactionCreate object already contains this field. If no header is present, it relies on this.
            Why both? It provides flexibility for different types of clients (web vs. mobile) while ensuring that some key is always provided (the code throws a 400 error if both are missing).

    If the same idempotency key is used twice, returns the original transaction
    without creating a duplicate.
    """
    
    # Use header if provided, otherwise use body value
    if idempotency_key:
        transaction.idempotency_key = idempotency_key
    
    # Validate idempotency key exists
    if not transaction.idempotency_key:
        raise HTTPException(
            status_code=400, 
            detail="Idempotency key required (header or body)"
        )
    
    try:
        result = PaymentService.initiate_payment(transaction, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Payment initiation failed")

@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    """Get transaction details"""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return transaction

@router.get("/{transaction_id}/history")
def get_transaction_history(transaction_id: str, db: Session = Depends(get_db)):
    """
    Get full event history for a transaction
    Demonstrates event sourcing pattern
    """
    try:
        events = PaymentService.get_transaction_history(transaction_id, db)
        return {
            "transaction_id": transaction_id,
            "event_count": len(events),
            "events": [
                {
                    "id": str(event.id),
                    "event_type": event.event_type,
                    "previous_status": event.previous_status,
                    "new_status": event.new_status,
                    "timestamp": event.timestamp.isoformat(),
                    "metadata": event.metadata
                }
                for event in events
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lease/{lease_id}", response_model=List[TransactionResponse])
def list_lease_transactions(
    lease_id: str, 
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all transactions for a lease"""
    transactions = db.query(Transaction).filter(
        Transaction.lease_id == lease_id
    ).order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()
    
    return transactions

@router.post("/{transaction_id}/retry")
def retry_failed_payment(transaction_id: str, db: Session = Depends(get_db)):
    """
    Retry a failed payment
    Demonstrates retry logic with exponential backoff consideration
    """
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if transaction.status != TransactionStatus.FAILED:
        raise HTTPException(
            status_code=400, 
            detail="Can only retry failed transactions"
        )
    
    MAX_RETRIES = 3
    if transaction.retry_count >= MAX_RETRIES:
        raise HTTPException(
            status_code=400, 
            detail=f"Maximum retry attempts ({MAX_RETRIES}) exceeded"
        )
    
    # Increment retry count
    transaction.retry_count += 1
    transaction.status = TransactionStatus.PENDING
    transaction.failed_at = None
    transaction.failure_reason = None
    
    # Log retry event
    from app.models.transaction_event import TransactionEvent
    event = TransactionEvent(
        transaction_id=transaction.id,
        event_type="retry_attempted",
        previous_status=TransactionStatus.FAILED.value,
        new_status=TransactionStatus.PENDING.value,
        metadata={"retry_count": transaction.retry_count}
    )
    db.add(event)
    
    db.commit()
    db.refresh(transaction)
    
    # Trigger async processing
    # process_payment_async.delay(str(transaction.id))
    
    return {
        "message": "Payment retry initiated",
        "transaction_id": str(transaction.id),
        "retry_count": transaction.retry_count
    }