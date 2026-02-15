from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.lease import Lease
from app.models.payment_schedule import PaymentSchedule
from app.schemas.lease import LeaseCreate, LeaseResponse
from datetime import datetime
from dateutil.relativedelta import relativedelta

router = APIRouter(prefix="/leases", tags=["leases"])

@router.post("/", response_model=LeaseResponse, status_code=201)
def create_lease(lease: LeaseCreate, db: Session = Depends(get_db)):
    # Verify property and renter exist
    # (add validation logic here)
    
    db_lease = Lease(**lease.model_dump())
    db.add(db_lease)
    db.commit()
    db.refresh(db_lease)
    
    # Create payment schedule
    first_payment_date = calculate_first_payment_date(
        lease.start_date, 
        lease.due_day_of_month
    )
    
    payment_schedule = PaymentSchedule(
        lease_id=db_lease.id,
        next_due_date=first_payment_date,
        amount=lease.rent_amount
    )
    db.add(payment_schedule)
    db.commit()
    
    return db_lease

def calculate_first_payment_date(start_date: datetime, due_day: int) -> datetime:
    """Calculate first payment due date based on lease start and due day"""
    if start_date.day <= due_day:
        # First payment this month
        return start_date.replace(day=due_day)
    else:
        # First payment next month
        next_month = start_date + relativedelta(months=1)
        return next_month.replace(day=due_day)

@router.get("/renter/{renter_id}", response_model=List[LeaseResponse])
def list_renter_leases(renter_id: str, db: Session = Depends(get_db)):
    leases = db.query(Lease).filter(Lease.renter_id == renter_id).all()
    return leases