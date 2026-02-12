from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid
from datetime import datetime

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    table_name = Column(String, nullable=False, index=True)
    record_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    action = Column(String, nullable=False)  # "CREATE", "UPDATE", "DELETE"
    
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    changed_by = Column(UUID(as_uuid=True), nullable=True)  # user_id
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)