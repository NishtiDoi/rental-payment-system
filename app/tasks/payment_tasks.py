from celery import Task
from app.celery_app import celery_app
from app.models.transaction import Transaction, TransactionStatus, PaymentRailType
from app.services.payment_service import PaymentService
from app.database import SessionLocal
import time 
import random
import logging

logger = logging.getLogger(__name__)

# This code is the "Engine Room" of your payment system.
# While FastAPI handles the customer talking to the app, this code handles the app talking to the bank.


# Custom celery base task that manages a SQLalchemy db session for each background job
class Database(Task):

    _db = None # Creates a placeholder for the database session
               # At the beginning of a task, there is no session and we dont want one immediately
               #    - Some tasks might not need a db session at all
               # This is called lazy initialization of the database session

    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None

@celery_app.task(base=Database, bind=True) # Celery bgrnd task , base= DatabaseTask means your task inherits the DBT class which gives it self.db, the lazy db session
def process_payment_async(self, transaction_id: str):
    """
    Simulate payment processing with different rail speeds
    
    Payment Rail Delays (simulated):
    - INSTANT: 1-2 seconds (like RTP/FedNow)
    - SAME_DAY_ACH: 30-60 seconds (simulated)
    - STANDARD_ACH: 2-3 minutes (simulated)
    - WIRE: 5-10 seconds
    """

    logger.info(f"Processing payment: {transaction_id}")

    db = self.db # Get the database session from the task's property

    # Get transaction from db
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id
    ).first()

    if not transaction:
        logger.error(f"Transaction {transaction_id} not found")
        return
    
    # Update transaction status to processing
    PaymentService.update_transaction_status(
        transaction_id, 
        TransactionStatus.PROCESSING,
        db
    )

    # Simulate different processing times based on payment rail
    # Simulate payment rail delays
    delay_map = {
        PaymentRailType.INSTANT: random.uniform(1, 2),
        PaymentRailType.SAME_DAY_ACH: random.uniform(30, 60),
        PaymentRailType.STANDARD_ACH: random.uniform(120, 180),
        PaymentRailType.WIRE: random.uniform(5, 10)
    }
    
    processing_time = delay_map.get(transaction.payment_rail_type, 5)
    logger.info(f"Simulating {transaction.payment_rail_type.value} processing: {processing_time}s")
    
    time.sleep(processing_time)
    
    # Simulate random failures (5% failure rate)
    if random.random() < 0.05:
        failure_reasons = [
            "Insufficient funds",
            "Account closed",
            "Invalid routing number",
            "Payment blocked by fraud detection"
        ]
        reason = random.choice(failure_reasons)
        
        PaymentService.update_transaction_status(
            transaction_id,
            TransactionStatus.FAILED,
            db,
            failure_reason=reason
        )
        
        logger.warning(f"Payment {transaction_id} failed: {reason}")
        
        # Auto-retry for certain failures
        if reason == "Insufficient funds":
            retry_delay = (2 ** self.request.retries) * 60  # 1min, 2min, 4min
            logger.info(f"Scheduled retry in {retry_delay}s")
            raise self.retry(countdown=retry_delay)
        
        return
    
    # Success!
    PaymentService.update_transaction_status(
        transaction_id,
        TransactionStatus.COMPLETED,
        db
    )
    
    logger.info(f"Payment {transaction_id} completed successfully")
    
    # Trigger post-payment tasks
    update_payment_schedule.delay(str(transaction.lease_id))

@celery_app.task(base=Database, bind=True)
def update_payment_schedule(self, lease_id: str):
    """
    Update payment schedule after successful payment
    Move next_due_date forward by one month
    """
    from app.models.payment_schedule import PaymentSchedule
    from dateutil.relativedelta import relativedelta
    
    db = self.db
    
    schedule = db.query(PaymentSchedule).filter(
        PaymentSchedule.lease_id == lease_id
    ).with_for_update().first()
    
    if schedule:
        schedule.next_due_date = schedule.next_due_date + relativedelta(months=1)
        db.commit()
        logger.info(f"Updated payment schedule for lease {lease_id}")