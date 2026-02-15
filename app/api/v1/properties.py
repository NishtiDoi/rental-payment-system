from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.property import Property
from app.models.user import User, UserRole
from app.schemas.property import PropertyCreate, PropertyResponse

#APIRouter for manaing the properties, code acts as validation and persistence layer
router = APIRouter(tags=["properties"])
#Prefix is handled in main.py - don't add prefix here
#Creates a group of related endpoints. Every route will be grouped under "properties" in your Swagger documentation.

#Even though your database object (SQLAlchemy) might contain "messy" or "secret" internal data, the response_model (Pydantic) ensures the outside world only sees exactly what you want them to see.
@router.post("/", response_model=PropertyResponse, status_code=201)
def create_property(property: PropertyCreate, db: Session = Depends(get_db)):
    # Verify landlord exists and has correct role
    landlord = db.query(User).filter(User.id == property.landlord_id).first()
    if not landlord:
        raise HTTPException(status_code=404, detail="Landlord not found")
    if landlord.role != UserRole.LANDLORD:
        raise HTTPException(status_code=400, detail="User is not a landlord")
    
    db_property = Property(**property.model_dump())
    # property.model_dump() turns the Pydantic object into a Python dictionary.
    # ** (the "splat" operator) unpacks that dictionary into the SQLAlchemy Property model.
    
    db.add(db_property)
    db.commit()
    db.refresh(db_property)
    return db_property

@router.get("/landlord/{landlord_id}", response_model=List[PropertyResponse])
def list_landlord_properties(landlord_id: str, db: Session = Depends(get_db)):
    properties = db.query(Property).filter(Property.landlord_id == landlord_id).all()
    return properties