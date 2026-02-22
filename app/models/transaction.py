from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, DateTime, Enum, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime
import enum

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentRailType(str, enum.Enum): # payment rails refer to the infrastruture that moves money between banks
    INSTANT = "instant"  # Like RTP(Real TIME payment network)/FedNow US FED Reserve's instant payment service  
    #URGRENT RENT PAYMENTS
    SAME_DAY_ACH = "same_day_ach" # automated clearing house
    STANDARD_ACH = "standard_ach" # 1-3 business day, very cheap, most common, can be reversed
    #FOR REGULAR RENT PAYMENTS
    WIRE = "wire" # same day, expensive, final (no reversals), good for large amounts

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # IDEMPOTENCY KEY - Critical for preventing duplicates
    idempotency_key = Column(String, unique=True, nullable=False, index=True)
    
    lease_id = Column(UUID(as_uuid=True), ForeignKey("leases.id"), nullable=False)
    
    payer_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False)
    payee_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False)
    
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    payment_rail_type = Column(Enum(PaymentRailType), default=PaymentRailType.STANDARD_ACH)
    
    # Timestamps for state tracking
    initiated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processing_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    
    # Error handling
    failure_reason = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Flexible metadata storage
    details  = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lease = relationship("Lease", back_populates="transactions")
    events = relationship("TransactionEvent", back_populates="transaction")

    payer_account = relationship("BankAccount", foreign_keys=[payer_account_id])
    payee_account = relationship("BankAccount", foreign_keys=[payee_account_id])
    
    # Indexes makes look ups faster, especially for common queries like "find all transactions for this lease"
    __table_args__ = (
        Index('idx_transaction_status_created', 'status', 'created_at'),
        Index('idx_transaction_lease', 'lease_id', 'created_at'),
    )
    #What is __table_args__?
#__table_args__ is where you define extra table-level configuration.
#“Stuff that applies to the whole table.”