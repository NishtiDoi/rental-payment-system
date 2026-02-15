from pydantic import BaseModel, UUID4
from decimal import Decimal
from datetime import datetime

class PropertyBase(BaseModel): # shared fields container, avoids repeatiton
    address: str
    city: str
    state: str
    zip_code: str
    monthly_rent: Decimal

class PropertyCreate(PropertyBase): # schema for incoming requests when creating a property
    landlord_id: UUID4

class PropertyResponse(PropertyBase): # schema for outgoing response
    id: UUID4
    landlord_id: UUID4
    created_at: datetime
    
    class Config:
        from_attributes = True #Allow this Pydantic model to read data directly from object attributes.



        #normally pydantic expcts a dictionary 
        # but when you fetch from database using sqlalchemy, you dont get a dictionary
        # you get an object