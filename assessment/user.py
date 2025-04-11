from fastapi import APIRouter
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from config import oauth2_scheme, authenticate_user
from database import get_db
from fastapi import Depends, HTTPException
from assessment.email import send_email
from passlib.context import CryptContext
from config import oauth2_scheme, authenticate_user
from schemas import UpdateUserProfileRequest
from pymongo.errors import DuplicateKeyError
from database import get_db
from schemas import ManagerCreate   

router = APIRouter()

@router.get("/get_userprofile", response_model=dict)
async def get_userprofile(token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):

    email = authenticate_user(token)
    try:

        user_data = text("SELECT id, first_name, last_name, email, mobile, username, address, user_type, secondary_email, registered_by,pin_code, "
        "is_staff, payment_status, orgnization, is_active, date_joined, is_superuser, otp_verify_status, gender, last_login FROM users WHERE email = :email")

        user = db.execute(user_data, {"email": email}).fetchone()

        if not user:
            return({"success": False, "message": "User not found."})
        
        gender_mapping = {0: "female", 1: "male", 2: "other", None: "null"}
        gender_value = gender_mapping.get(user.gender, "other")
        
        payment_mapping ={0: "Not Paid",1:"Paid",2:"Exhausted"}
        payments = payment_mapping.get(user.payment_status, "Not Paid")

        registered_by_mapping = { 0: "user",1: "admin"}
        registered_by_value = registered_by_mapping.get(int(user.registered_by), "")
    
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
            "registered_by": registered_by_value,
            "pin_code": user.pin_code if user.pin_code else "",
            "is_staff": user.is_staff if user.is_staff else "",
            "payment_status": payments if payments else "",
            "company_name": user.orgnization if user.orgnization else "",
            "is_active": user.is_active if user.is_active else "",    
            "date_joined": user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
            "is_superuser": user.is_superuser if user.is_superuser else "",
            "otp_verify_status": user.otp_verify_status,
            "gender": gender_value if gender_value is not None else "",
            "last_login": user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None
        }

        return {"success": True, "data": user_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    

@router.post("/update_userprofile", response_model=dict)
async def update_userprofile(
    request: UpdateUserProfileRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        email = authenticate_user(token)

        user_query = text("SELECT id, otp_verify_status FROM users WHERE email = :email")
        user = db.execute(user_query, {"email": email}).fetchone()

        if not user:
            return {"success": False, "message": "User not found."}

        user_id, lotp_verify_status = user

        update_data = request.model_dump(exclude_unset=True)

        if "gender" in update_data:
            gender_mapping = {"female": 0, "male": 1}
            update_data["gender"] = gender_mapping.get(update_data["gender"].lower(), 2)
        if "registered_by" in update_data:
            registered_by_mapping = {"user": 0, "admin": 1}
            update_data["registered_by"] = registered_by_mapping.get(update_data["registered_by"].lower(), 2)
        if "company_name" in update_data:
            update_data["orgnization"] = update_data.pop("company_name")

        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields provided for update.")

        update_data["user_id"] = user_id

        set_value = ", ".join(f"{key} = :{key}" for key in update_data.keys() if key != "user_id")
        update_query = text(f"UPDATE users SET {set_value} WHERE id = :user_id")

        db.execute(update_query, update_data)
        db.commit()

        return {"success": True, "message": "User profile updated successfully."}

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/add_manager")
def add_manager(manager: ManagerCreate, db=Depends(get_db)):
    managers_collection = db["manager"]

    managers_collection.create_index("email", unique=True)

    try:
        managers_collection.insert_one({"email": manager.email})
        return {"message": "Manager added successfully"}
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Email already exists")