from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime
import enum

class LeaseStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"

class Lease(Base):
    __tablename__ = "leases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    renter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    rent_amount = Column(Numeric(10, 2), nullable=False)
    due_day_of_month = Column(Integer, nullable=False)  # e.g., 1 for 1st of month
    
    status = Column(Enum(LeaseStatus), default=LeaseStatus.ACTIVE)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    property = relationship("Property", back_populates="leases")
    renter = relationship("User", back_populates="leases_as_renter")
    payment_schedule = relationship( #back_populates keeps both sides of the relationship synchronized automatically.
        "PaymentSchedule",
        back_populates="lease",
        uselist=False # One-to-one relationship
    )
    transactions = relationship("Transaction", back_populates="lease")
