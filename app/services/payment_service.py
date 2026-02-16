from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.transaction import Transaction, TransactionStatus, PaymentRailType
from app.models.transaction_event import TransactionEvent
from app.models.bank_account import BankAccount
from app.schemas.transaction import TransactionCreate
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class PaymentService:
# focus on two important concepts:
# 1. Idempotency: Ensure that if the same payment request is made multiple times (e.g., due to network retries), only one transaction is created and processed.
# 2. Event Sourcing: Instead of just updating the transaction record, we log every state change 
    @staticmethod
    def _utc_now():
        return datetime.now(timezone.utc)

    @staticmethod
    def initiate_payment(transaction_data: TransactionCreate, db: Session) -> Transaction:
        """
        Initiate a payment with idempotency handling.
        If idempotency_key already exists, return existing transaction.
        Otherwise, create new transaction, log event, and trigger async processing.
        """
        # 1. Check for existing transaction with this idempotency key
        existing_txn = db.query(Transaction).filter(
            Transaction.idempotency_key == transaction_data.idempotency_key
        ).first()
         
        if existing_txn: # user may click multiple times, return the same key veryt time they click
            logger.info(f"Idempotency key {transaction_data.idempotency_key} already exists. Returning existing transaction.")
            return existing_txn
        
        # 2. Validate bank accounts exist
        payer_account = db.query(BankAccount).filter(
            BankAccount.id == transaction_data.payer_account_id
        ).first()
        payee_account = db.query(BankAccount).filter(
            BankAccount.id == transaction_data.payee_account_id
        ).first()
        if not payer_account or not payee_account:
            raise ValueError("Invalid bank account(s)")

        # 3. Create transaction and log event
        # Transaction protection layer, either saved perfectly with full audit trail or not at all (rollback on failure)
        # Most important is that it never happens twice
        try:
            db_transaction = Transaction(
                **transaction_data.model_dump(),  # converts validated Pydantic model to dict and then to SQLAlchemy model
                status=TransactionStatus.PENDING,
                initiated_at=PaymentService._utc_now()
            )
            db.add(db_transaction) # This tells SQLAlchemy, "I want to save this, but don't tell the database to make it permanent yet."
            db.flush()  # sends data to the database but doesn't commit, so we get an ID for the transaction without finalizing it
            
            event = TransactionEvent( # Audit trail phase 
                transaction_id=db_transaction.id,
                event_type="payment_initiated",
                previous_status=None,
                new_status=TransactionStatus.PENDING.value,
                metadata={ # fixed values at the time of initiation, even if related records change later
                    "payer_account": str(transaction_data.payer_account_id),
                    "payee_account": str(transaction_data.payee_account_id),
                    "amount": str(transaction_data.amount),
                    "rail": transaction_data.payment_rail_type.value
                }
            )
            db.add(event)
            db.commit()
            db.refresh(db_transaction)
            
            logger.info(f"Payment initiated: {db_transaction.id}")
            # Trigger async processing (e.g., Celery) here if needed
            # process_payment_async.delay(str(db_transaction.id))
            return db_transaction

        except IntegrityError as e: # handles race condtions where two requests with the same idempotency key hit at the same time
            # loser of the race gets integrity error due to unique constraint on idempotency key
            db.rollback()
            logger.error(f"IntegrityError during payment initiation: {e}")
            # Return existing transaction in case of race condition
            existing_txn = db.query(Transaction).filter(
                Transaction.idempotency_key == transaction_data.idempotency_key
            ).first()
            if existing_txn:
                return existing_txn
            raise

    @staticmethod
    def update_transaction_status(
        transaction_id: str,
        new_status: TransactionStatus,
        db: Session,
        failure_reason: str | None = None
    ) -> Transaction:
        """
        Update transaction status with event logging
        """
        transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not transaction:
            raise ValueError("Transaction not found")

        old_status = transaction.status
        transaction.status = new_status

        # Update timestamp based on status, State machine logic to ensure correct timestamps are set for each status
        now = PaymentService._utc_now()

        if new_status == TransactionStatus.PROCESSING:
            transaction.processing_at = now
        elif new_status == TransactionStatus.COMPLETED:
            transaction.completed_at = now
        elif new_status == TransactionStatus.FAILED:
            transaction.failed_at = now
            transaction.failure_reason = failure_reason

        # Log event
        """
        Why do we do this instead of just updating the status?
            If a transaction goes from PENDING → PROCESSING → FAILED → PENDING (retry) → COMPLETED, the transactions table will only show the final state (COMPLETED). The TransactionEvent table, however, will show the entire journey. This is vital for:

            Auditing: Proving to a landlord or tenant exactly when a status changed.
            Debugging: Seeing if transactions are failing at a specific step in your pipeline.
        """
        event = TransactionEvent(
            transaction_id=transaction.id,
            event_type="status_change",
            previous_status=old_status.value,
            new_status=new_status.value,
            metadata={"failure_reason": failure_reason} if failure_reason else None
        )
        db.add(event)
        db.commit()
        db.refresh(transaction)

        logger.info(f"Transaction {transaction_id} status updated: {old_status} → {new_status}")
        return transaction

    @staticmethod
    def get_transaction_history(transaction_id: str, db: Session):
        """
        Get full event history for a transaction (event sourcing)
        """
        events = db.query(TransactionEvent).filter(
            TransactionEvent.transaction_id == transaction_id
        ).order_by(TransactionEvent.timestamp.asc()).all()
        return events
