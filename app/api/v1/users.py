from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse

# Create a dedicated router for all user-related endpoints
# All routes will be prefixed with /users and grouped under "users" tag in docs
router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.
    Checks for email uniqueness before creating the record.
    """
    # Check if email is already registered
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user instance from validated request data
    db_user = User(**user.model_dump()) # The expression User(**user.model_dump()) takes the validated data from the incoming HTTP request (held in a Pydantic UserCreate object), converts it to a dictionary, and passes every key-value pair as a named argument to the SQLAlchemy User model constructor — creating a new database entity in the most concise and maintainable way.

    db.add(db_user)     # Stage the new user for insertion
    db.commit()         # Execute the INSERT
    db.refresh(db_user) # Load any DB-generated values (e.g. id, created_at)

# So before commit() → object exists only in memory
# After commit() → object also exists as a real row in the database
    return db_user


@router.get("/", response_model=List[UserResponse])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a paginated list of users.
    Useful for admin interfaces or user management screens.
    """
    # Simple offset/limit pagination
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a single user by their ID.
    Returns 404 if the user does not exist.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user