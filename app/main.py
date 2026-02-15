from fastapi import FastAPI
from app.api.v1 import users, bank_accounts
from app.database import engine, Base

# Create tables (in production, use Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DirectPay Rental Platform",
    description="Direct bank-to-bank rental payment system",
    version="1.0.0"
)

# Include routers
app.include_router(users.router, prefix="/api/v1")
app.include_router(bank_accounts.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "DirectPay API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}