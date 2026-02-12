from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.bank_account import BankAccount
from app.schemas.bank_account import BankAccountCreate, BankAccountResponse

router = APIRouter(prefix="/bank-accounts", tags=["bank_accounts"])

@router.post("/", response_model=BankAccountResponse, status_code=201)
def create_bank_account(account: BankAccountCreate, db: Session = Depends(get_db)):
    # Simulate tokenization - in real world, this would be a secure process
    db_account = BankAccount(**account.model_dump())
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account

@router.get("/user/{user_id}", response_model=List[BankAccountResponse])
def list_user_accounts(user_id: str, db: Session = Depends(get_db)):
    accounts = db.query(BankAccount).filter(BankAccount.user_id == user_id).all()
    return accounts

@router.patch("/{account_id}/set-primary", response_model=BankAccountResponse)
def set_primary_account(account_id: str, db: Session = Depends(get_db)):
    account = db.query(BankAccount).filter(BankAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Unset other primary accounts for this user
    db.query(BankAccount).filter(
        BankAccount.user_id == account.user_id,
        BankAccount.id != account_id
    ).update({"is_primary": False})
    
    account.is_primary = True
    db.commit()
    db.refresh(account)
    return account