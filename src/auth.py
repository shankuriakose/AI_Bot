from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from src.models import User
from src.main import SessionLocal

import hashlib

class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


router = APIRouter()


def hash_password(password: str):
    # Use a proper hashing algorithm with salt in a real application
    # Example with hashlib.sha256 (not recommended for production)
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    return hashed_password


def verify_password(plain_password: str, hashed_password: str):
    return hash_password(plain_password) == hashed_password


# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", status_code=201)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_password = hash_password(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # Refresh to get the generated ID
    return {"username": new_user.username, "message": "User registered successfully"}


@router.post("/login", response_model=Token)
async def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    # In a real app, you would generate a JWT or similar token.
    return {"access_token": "fake_token", "token_type": "bearer"}

