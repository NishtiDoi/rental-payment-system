from pydantic import BaseModel, UUID4, field_validator, ConfigDict
from decimal import Decimal
from datetime import datetime
from app.models.lease import LeaseStatus


#Pydantic schema is defined

class LeaseBase(BaseModel):#Shared template, put common fields here
    property_id: UUID4
    renter_id: UUID4
    start_date: datetime
    end_date: datetime 
    rent_amount: Decimal
    due_day_of_month: int
    
    @field_validator('due_day_of_month') # custom validators
    @classmethod
    def validate_due_day(cls, v):
        if v < 1 or v > 28:  # Keep it safe
            raise ValueError('Due day must be between 1 and 28')
        return v
    
    @field_validator('end_date', mode='after')
    @classmethod
    def validate_end_date(cls, v):
        return v

class LeaseCreate(LeaseBase):
    pass

class LeaseResponse(LeaseBase):
    id: UUID4
    status: LeaseStatus
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)