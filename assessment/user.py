from fastapi import APIRouter
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from config import oauth2_scheme, authenticate_user
from database import get_db
from fastapi import Depends, HTTPException
from assessment.email import send_email
from passlib.context import CryptContext
from config import oauth2_scheme, authenticate_user

router = APIRouter()

@router.get("/get_userprofile", response_model=dict)
async def get_userprofile(token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):

    email = authenticate_user(token)
    try:

        user_data = text("SELECT id, first_name, last_name, email, mobile, username, address, user_type, secondary_email, pin_code, "
        "is_staff, is_active, date_joined, is_superuser, login_otp_verify_status,gender, last_login FROM users WHERE email = :email")

        user = db.execute(user_data, {"email": email}).fetchone()

        if not user:
            return({"success": False, "message": "User not found."})
        
        gender_mapping = {0: "female", 1: "male", 2: "other", None: "null"}
        gender_value = gender_mapping.get(user.gender, "other")


        user_data = {
            "id": str(user.id),  
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "mobile": user.mobile if user.mobile else "",
            "username": user.username if user.username else "",
            "address": user.address if user.address else "",
            "user_type": user.user_type if user.user_type else "",
            "secondary_email": user.secondary_email if user.secondary_email else "",
            "pin_code": user.pin_code if user.pin_code else "",
            "is_staff": user.is_staff if user.is_staff else "",
            "is_active": user.is_active if user.is_active else "",    
            "date_joined": user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
            "is_superuser": user.is_superuser if user.is_superuser else "",
            "login_otp_verify_status": user.login_otp_verify_status,
            "gender": gender_value if gender_value is not None else "",
            "last_login": user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None
        }

        return {"success": True, "data": user_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")