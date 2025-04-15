from fastapi import APIRouter
from fastapi import FastAPI, HTTPException, Depends
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone, timedelta
import uuid
from schemas import SignupRequest, OTPVerifyRequest, UserLogin
from database import get_db
import random
import string
from common.utils import create_access_token, hash_password, verify_password
from jose import JWTError, jwt
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from business_logic.email import send_html_email
from motor.motor_asyncio import AsyncIOMotorDatabase


router = APIRouter()


async def generate_unique_username(first_name: str, last_name: str, db: AsyncIOMotorDatabase):
    while True:
        random_suffix = "".join(random.choices(string.digits, k=4))  
        username = f"{first_name.lower()}_{random_suffix}"

        existing_user = await db["users"].find_one({"username": username})
        if not existing_user:
            return username


@router.post("/signup", response_model=dict)
async def signup(request: SignupRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        # Check if user with email already exists
        existing_user = await db["users"].find_one({"email": request.email})

        if existing_user:
            if not existing_user.get("otp_verify_status", False):
                # Resend OTP logic
                otp = str(random.randint(100000, 999999))
                otp_created_at = datetime.now(timezone.utc)
                otp_expiry_time = otp_created_at + timedelta(minutes=3)

                # Update user with new OTP and timestamps
                await db["users"].update_one(
                    {"_id": existing_user["_id"]},
                    {
                        "$set": {
                            "otp": otp,
                            "otp_created_at": otp_created_at,
                            "login_otp_try_dt": otp_expiry_time,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )

                # Resend OTP email
                send_html_email(
                    subject="Your Signup OTP",
                    recipient=request.email,
                    template_name="signup_otp.html",
                    context={
                        "first_name": existing_user["first_name"].capitalize(),
                        "otp": otp
                    }
                )

                return {
                    "success": True,
                    "message": "User already exists but not verified. OTP re-sent to email. Please verify within 3 minutes."
                }

            return {"success": False, "message": "User with this email already exists."}

        # Gmail restriction for organization users
        if request.company_name and request.email.endswith("@gmail.com"):
            return {"success": False, "message": "Organization users cannot register with @gmail.com email addresses."}

        # Generate OTP & times
        otp = str(random.randint(100000, 999999))
        otp_created_at = datetime.now(timezone.utc)
        otp_expiry_time = otp_created_at + timedelta(minutes=3)

        # Unique username
        username = await generate_unique_username(request.first_name, request.last_name, db)
        user_id = str(uuid.uuid4())
        now_time = datetime.now(timezone.utc)

        # Create user document
        user_data = {
            "_id": user_id,
            "username": username,
            "email": request.email,
            "first_name": request.first_name,
            "last_name": request.last_name,
            "address": request.address,
            "password": hash_password(request.password),  # store Hashed password
            "user_type": request.user_type,
            "payment_status": "0",
            "mobile": request.mobile,
            "secondary_email": request.secondary_email,
            "pin_code": request.pin_code,
            "gender": request.gender,
            "orgnization": request.company_name or "",
            "registered_by": "0",
            "otp": otp,
            "login_try_datetime": now_time,
            "last_login": now_time,
            "otp_created_at": otp_created_at,
            "login_otp_try_dt": otp_expiry_time,
            "otp_verify_status": False,
            "is_superuser": False,
            "is_staff": False,
            "is_active": True,
            "company_email": request.company_email or "",
            "company_size": request.company_size or "",
            "date_joined": now_time,
            "updated_at": now_time,
            "created_at": now_time
        }

        await db["users"].insert_one(user_data)

        # Read and send OTP email
        send_html_email(subject="Your Signup OTP", recipient= request.email, template_name= "signup_otp.html", context= {"first_name":request.first_name.capitalize(), "otp":otp})

        return {"success": True, "message": "OTP sent to email. Please verify within 3 minutes."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.post("/verify_otp", response_model=dict)
async def verify_otp(request: OTPVerifyRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        current_time = datetime.now(timezone.utc)

        # Fetch the user with matching OTP and conditions
        user = await db["users"].find_one({
            "otp": request.otp,
            "login_otp_try_dt": {"$gte": current_time},
            "otp_verify_status": False
        })

        if not user:
            return {"success": False, "message": "Invalid or expired OTP."}

        # Update user record to mark OTP verified and update password
        await db["users"].update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "otp_verify_status": True,
                }
            }
        )

        return {"success": True, "message": "OTP verified and user registered successfully."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/login")
async def login(user: UserLogin, db: AsyncIOMotorDatabase = Depends(get_db)):

    # Find user by email
    db_user = await db["users"].find_one({"email": user.email})

    if not db_user:
        return {"success": False, "message": "Invalid email or password"}
    
    if not db_user.get("is_active", False):
        return {"success": False, "message": "User is not active"}
    
    if db_user.get("is_deleted", False):
        return {"success": False, "message": "User is deactivated"}
    
    if not db_user.get("otp_verify_status", False):
        return {"success": False, "message": "User otp verification is pending"}

    # Verify password
    if not verify_password(user.password, db_user["password"]):
        return {"success": False, "message": "Invalid email or password"}

    # Update last login time
    await db["users"].update_one(
        {"_id": db_user["_id"]},
        {"$set": {"last_login": datetime.now(timezone.utc)}}
    )

    # Generate JWT Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": db_user["email"]}, expires_delta=access_token_expires)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": db_user["email"],
            "first_name": db_user["first_name"]
        },
        "message": "Login successful",
    }