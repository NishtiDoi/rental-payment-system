from pydantic import BaseModel, EmailStr, UUID4, ConfigDict
from datetime import datetime
from app.models.user import UserRole #UserRole enumerable value hai

class UserBase(BaseModel): #shared schema guarenteeing user related schema reuse these feilds else error 422
    email: EmailStr
    full_name: str 
    role: UserRole

class UserCreate(UserBase): # allowed payload when creating a user(prevents future mess)
    pass

class UserResponse(UserBase): # what the api sends back to user after signuing up or when they view profile
    id: UUID4 # UserBase+ id+ created at  
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True) #Setting from_attributes = True tells Pydantic: "It's okay if the data isn't a dictionary. If you see an Object, just read the attributes (dot notation) automatically."