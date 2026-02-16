from pydantic import BaseModel, UUID4, field_validator, ConfigDict
from decimal import Decimal
from typing import Optional
from datetime import datetime
from app.models.transaction import TransactionStatus, PaymentRailType

class TransactionCreate(BaseModel):
    idempotency_key: Optional[str] = None
    lease_id: UUID4
    payer_account_id: UUID4
    payee_account_id: UUID4
    amount: Decimal
    payment_rail_type: PaymentRailType = PaymentRailType.STANDARD_ACH
    
    @field_validator('amount', mode='after')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v

class TransactionResponse(BaseModel):
    id: UUID4
    idempotency_key: str
    lease_id: UUID4
    payer_account_id: UUID4
    payee_account_id: UUID4
    amount: Decimal
    status: TransactionStatus
    payment_rail_type: PaymentRailType
    initiated_at: datetime
    processing_at: datetime | None
    completed_at: datetime | None
    failed_at: datetime | None
    failure_reason: str | None
    retry_count: int
    
    model_config = ConfigDict(from_attributes=True)