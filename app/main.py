from fastapi import FastAPI
from app.database import engine, Base
from app.api.v1 import users, bank_accounts, properties, leases
from app import models

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DirectPay Rental Platform",
    description="Direct bank-to-bank rental payment system",
    version="1.0.0"
)

# Include routers with proper prefixes
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(bank_accounts.router, prefix="/api/v1/bank-accounts", tags=["Bank Accounts"])
app.include_router(properties.router, prefix="/api/v1/properties", tags=["Properties"])
app.include_router(leases.router, prefix="/api/v1/leases", tags=["Leases"])

@app.get("/")
def root():
    return {"message": "DirectPay API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
