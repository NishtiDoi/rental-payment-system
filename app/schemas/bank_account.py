from pydantic import BaseModel, UUID4, ConfigDict
from datetime import datetime

class BankAccountBase(BaseModel): # Common fields shared between create and response schemas
    account_number_token: str  # Last 4 digits only
    routing_number: str
    bank_name: str

class BankAccountCreate(BankAccountBase): #Input schema used when a client requests to link/add a new bank account.
    user_id: UUID4

class BankAccountResponse(BankAccountBase):  # Output schema returned by the API after successful creation, retrieval,or listing of bank accounts.
    id: UUID4
    user_id: UUID4
    is_verified: bool
    is_primary: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)