from pydantic import BaseModel, UUID4, validator
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
    
    @validator('due  _day_of_month') # custom validators
    def validate_due_day(cls, v):
        if v < 1 or v > 28:  # Keep it safe
            raise ValueError('Due day must be between 1 and 28')
        return v
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

class LeaseCreate(LeaseBase):
    pass

class LeaseResponse(LeaseBase):
    id: UUID4
    status: LeaseStatus
    created_at: datetime
    
    class Config:
        from_attributes = True