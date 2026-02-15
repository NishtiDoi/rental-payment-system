from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.lease import Lease
from app.models.payment_schedule import PaymentSchedule
from app.schemas.lease import LeaseCreate, LeaseResponse
from app.models.property import Property
from app.models.user import User
from datetime import datetime
from dateutil.relativedelta import relativedelta

router = APIRouter()  # no prefix here, main.py handles it

@router.post("/", response_model=LeaseResponse, status_code=201)
def create_lease(lease: LeaseCreate, db: Session = Depends(get_db)):
    # Validate property exists
    property_obj = db.query(Property).filter(Property.id == lease.property_id).first()
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Validate renter exists
    renter_obj = db.query(User).filter(User.id == lease.renter_id, User.role == "renter").first()
    if not renter_obj:
        raise HTTPException(status_code=404, detail="Renter not found")
    
    # Create lease
    db_lease = Lease(**lease.model_dump())
    db.add(db_lease)
    db.commit()
    db.refresh(db_lease)
    
    # Create payment schedule
    first_payment_date = calculate_first_payment_date(lease.start_date, lease.due_day_of_month)
    payment_schedule = PaymentSchedule(
        lease_id=db_lease.id,
        next_due_date=first_payment_date,
        amount=lease.rent_amount
    )
    db.add(payment_schedule)
    db.commit()
    
    return db_lease

def calculate_first_payment_date(start_date: datetime, due_day: int) -> datetime:
    if start_date.day <= due_day:
        return start_date.replace(day=due_day)
    else:
        next_month = start_date + relativedelta(months=1)
        return next_month.replace(day=due_day)

@router.get("/renter/{renter_id}", response_model=List[LeaseResponse])
def list_renter_leases(renter_id: str, db: Session = Depends(get_db)):
    leases = db.query(Lease).filter(Lease.renter_id == renter_id).all()
    return leases
