from fastapi import APIRouter
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone, timedelta
import uuid
from schemas import SignupRequest, UserLogin, OTPVerifyRequest
from database import get_db
import random
import string
import os
from jose import JWTError, jwt
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from assessment.email import send_email,templates_path

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def generate_unique_username(first_name: str, last_name: str, db: Session):
    while True:
        random_suffix = "".join(random.choices(string.digits, k=4))  
        username = f"{first_name.lower()}_{random_suffix}"

        query = text("SELECT EXISTS (SELECT 1 FROM users WHERE username = :username)")
        result = db.execute(query, {"username": username})
        exists = result.scalar()

        if not exists:
            return username

def generate_affiliate_id():
    characters = string.ascii_uppercase + string.digits  # A-Z and 0-9
    return ''.join(random.choices(characters, k=5))

@router.post("/signup", response_model=dict)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    pass

@router.post("/verify_otp", response_model=dict) 
async def verify_otp(request: OTPVerifyRequest, db: Session = Depends(get_db)):
    pass


def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):

    check_query = text("SELECT id, first_name, email, password FROM users WHERE email = :email")
    db_user = db.execute(check_query, {"email": user.email}).fetchone()

    if not db_user:
        return {"success": False, "message": "Invalid email or password"}

    user_id, first_name, email, hashed_password  = db_user

    # Verify password
    if not pwd_context.verify(user.password, hashed_password):
        return {"success": False, "message": "Invalid email or password"}

    # Update last login time
    update_query = text("UPDATE users SET last_login = :last_login WHERE id = :id")
    db.execute(update_query, {"last_login": datetime.now(timezone.utc), "id": user_id})
    db.commit()

    # Generate JWT Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": email}, expires_delta=access_token_expires)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": email,
            "first_name": first_name
        },
        "message": "Login successful",
    }