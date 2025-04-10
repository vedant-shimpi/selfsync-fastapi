from fastapi import APIRouter
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone, timedelta
import uuid
from schemas import SignupRequest, OTPVerifyRequest, UserLogin
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


@router.post("/signup", response_model=dict)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    try:
  
        check_query = text("SELECT id FROM users WHERE email = :email")
        existing_user = db.execute(check_query, {"email": request.email}).fetchone()

        if existing_user:
            return {"success": False, "message": "User with this email already exists."}

        if request.company_name and request.email.endswith("@gmail.com"):
            return {"success": False, "message": "Organization users cannot register with @gmail.com email addresses."}

        # Generate OTP & expiry time
        otp = str(random.randint(100000, 999999))
        otp_created_at = datetime.now(timezone.utc)
        otp_expiry_time = otp_created_at + timedelta(minutes=3)

        # Generate Unique username
        username = await generate_unique_username(request.first_name, request.last_name, db)
        user_id = str(uuid.uuid4())
        now_time = datetime.now(timezone.utc)

        signup_query = text("""
            INSERT INTO users (
                id, username, email, first_name, last_name, address, password, user_type,payment_status,
                mobile, secondary_email, pin_code, gender, orgnization, registered_by,
                otp, login_try_datetime, otp_created_at, login_otp_try_dt, otp_verify_status,
                is_superuser, is_staff, is_active, date_joined, updated_at, created_at
            ) VALUES (
                :id, :username, :email, :first_name, :last_name, :address, :password, :user_type,:payment_status,
                :mobile, :secondary_email, :pin_code, :gender, :orgnization, :registered_by,
                :otp, :login_try_datetime, :otp_created_at, :login_otp_try_dt, :otp_verify_status,
                FALSE, FALSE, TRUE, :date_joined, :updated_at, :created_at
            )
        """)

        db.execute(signup_query, {
            "id": user_id,
            "username": username,
            "email": request.email,
            "first_name": request.first_name,
            "last_name": request.last_name,
            "address": request.address,
            "password": request.password,
            "user_type": "support",
            "payment_status":"0",
            "mobile": request.mobile,
            "secondary_email": request.secondary_email,
            "pin_code": request.pin_code,
            "gender": request.gender,
            "orgnization": request.company_name or "",
            "registered_by": "0",
            "otp": otp,
            "login_try_datetime": now_time,
            "otp_created_at": otp_created_at,
            "login_otp_try_dt": otp_expiry_time,
            "otp_verify_status": False,
            "date_joined": now_time,
            "updated_at": now_time,
            "created_at": now_time
        })

        db.commit()

        with open("templates/signup_otp.html", "r", encoding="utf-8") as file:
            email_template = file.read()

        email_message = email_template.replace("{first_name}", request.first_name.capitalize()).replace("{otp}", otp)
        send_email(request.email, "Your Signup OTP", email_message)

        return {"success": True, "message": "OTP sent to email. Please verify within 3 minutes."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.post("/verify_otp", response_model=dict)
async def verify_otp(request: OTPVerifyRequest, db: Session = Depends(get_db)):
    try:
        current_time = datetime.now(timezone.utc)

        otp_query = text("""
            SELECT id, otp, otp_created_at, login_otp_try_dt, password,
                   email, first_name, username
            FROM users 
            WHERE otp = :otp 
              AND login_otp_try_dt >= :current_time
              AND otp_verify_status = FALSE
        """)

        user = db.execute(otp_query, {
            "otp": request.otp,
            "current_time": current_time
        }).fetchone()

        if not user:
            return {"success": False, "message": "Invalid or expired OTP."}

        user_id, db_otp, otp_created_at, otp_expiry_time, saved_password, email, first_name, username = user

        hashed_password = pwd_context.hash(saved_password)

        update_query = text("""
            UPDATE users 
            SET otp_verify_status = TRUE,
                otp = otp,
                password = :password
            WHERE id = :user_id
        """)
        db.execute(update_query, {
            "user_id": user_id,
            "password": hashed_password
        })
        db.commit()

        with open("templates/signup.html", "r", encoding="utf-8") as file:
            email_template = file.read()

        email_message = email_template \
            .replace("{first_name}", first_name.capitalize()) \
            .replace("{username}", username)

        send_email(email, "Thank You for Joining Us", email_message)

        return {"success": True, "message": "OTP verified and user registered successfully."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


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