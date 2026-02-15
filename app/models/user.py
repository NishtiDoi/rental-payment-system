from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship # <--- Add this import
from app.database import Base
import uuid
from datetime import datetime
import enum

class UserRole(str, enum.Enum):
    LANDLORD = "landlord"
    RENTER = "renter"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - These must match the 'back_populates' names in your other files
    bank_accounts = relationship("BankAccount", back_populates="user")
