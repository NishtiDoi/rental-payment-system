from sqlalchemy import Column, String, ForeignKey, DateTime, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime

class TransactionEvent(Base):
    __tablename__ = "transaction_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False)
    
    event_type = Column(String, nullable=False)  # "status_change", "retry_attempted", etc.
    previous_status = Column(String, nullable=True)
    new_status = Column(String, nullable=True)
    
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="events")