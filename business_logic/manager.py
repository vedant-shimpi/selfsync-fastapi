from fastapi import APIRouter, Depends, HTTPException
from fastapi import Depends, HTTPException
from business_logic.email import send_email
from pymongo.errors import DuplicateKeyError
from schemas_validation.manager import ManagerCreate, ManagerInfo
import random
import string  
from pymongo.collection import Collection
from datetime import datetime, timezone, timedelta
import uuid
from common.utils import hash_password
from common.auth import get_current_user
from database import managers_collection, users_collection, get_db


router = APIRouter()


def generate_unique_password(first_name: str):
    random_suffix = "".join(random.choices(string.digits, k=4))
    return f"{first_name.lower()}_{random_suffix}"


# Send email using template
def send_email_with_password(email: str, password: str, first_name: str):
    with open("templates/login_info.html", "r", encoding="utf-8") as file:
        email_template = file.read()

    email_message = (
        email_template
        .replace("{first_name}", first_name.capitalize())
        .replace("{email}", email)
        .replace("{password}", password)
    )
    send_email(email, "login information", email_message)


@router.post("/add_manager")
async def add_manager(
    manager: ManagerCreate, current_user: dict = Depends(get_current_user), db=Depends(get_db)
):
    if current_user.get("user_type") != "hr":
        return {"success": False, "message": "You are not authorized to add a manager."}

    users_collection = db["users"]
    managers_collection = db["manager"]

    name_parts = manager.full_name.strip().split()
    first_name = name_parts[0]
    last_name = name_parts[-1] if len(name_parts) > 1 else ""

    now = datetime.now(timezone.utc)

    # Validate HR
    hr_exists = await users_collection.find_one({"_id": str(manager.hr_id)})
    print("Found HR record:", hr_exists)
    if not hr_exists:
        return {"success": False, "message": "Provided hr_id does not exist or is not an HR."}

    # Check if manager already exists for same HR
    existing_user = await users_collection.find_one({
        "email": manager.email,
        "user_type": "manager"
    })

    if existing_user:
        existing_manager = await managers_collection.find_one({
            "_id": existing_user["_id"],
            "hr_id": manager.hr_id
        })

        if existing_manager:
            if not existing_user.get("is_deleted", False):
                return {"success": False, "message": "This manager is already added by you."}
            else:
                # Reactivate deleted manager
                await users_collection.update_one(
                    {"_id": existing_user["_id"]},
                    {
                        "$set": {
                            "first_name": first_name,
                            "last_name": last_name,
                            "is_deleted": False,
                            "updated_at": now
                        }
                    }
                )

                await managers_collection.update_one(
                    {"_id": existing_user["_id"]},
                    {
                        "$set": {
                            "full_name": manager.full_name,
                            "updated_at": now
                        }
                    }
                )

                return {"success": True, "message": "Manager reactivated successfully."}

    # Create new manager even if email already exists (different HR)
    password = generate_unique_password(first_name)
    while True:
        suffix = "".join(random.choices(string.digits, k=4))
        username = f"{first_name.lower()}_{suffix}"
        if not await users_collection.find_one({"username": username}):
            break

    user_id = str(uuid.uuid4())

    user_data = {
        "_id": user_id,
        "username": username,
        "email": manager.email,
        "first_name": first_name,
        "last_name": last_name,
        "address": "",
        "password": hash_password(password),
        "user_type": "manager",
        "payment_status": "0",
        "mobile": "",
        "secondary_email": "",
        "pin_code": "",
        "gender": "",
        "orgnization": "",
        "registered_by": "0",
        "otp": None,
        "otp_created_at": now,
        "login_try_datetime": now,
        "last_login": now,
        "login_otp_try_dt": now + timedelta(minutes=3),
        "otp_verify_status": True,
        "is_superuser": False,
        "is_staff": False,
        "is_active": True,
        "is_deleted": False,
        "company_email": "",
        "company_size": "",
        "date_joined": now,
        "updated_at": now,
        "created_at": now,
        "manager_id": user_id
    }

    manager_data = {
        "_id": user_id,
        "email": manager.email,
        "full_name": manager.full_name,
        "password": hash_password(password),
        "hr_id": manager.hr_id,
        "created_at": now,
        "updated_at": now
    }

    try:
        await users_collection.insert_one(user_data)
        await managers_collection.insert_one(manager_data)

        send_email_with_password(manager.email, password, first_name)

        return {"success": True, "message": "Manager created, login enabled, and email sent."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_manager_info", response_model=dict)
async def get_manager_info(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    try:
        manager = await managers_collection.find_one(
            {"email": current_user["email"]},
            {"_id": 0, "password": 0}
        )

        if not manager:
            raise HTTPException(status_code=404, detail="Manager not found")

        return {"success": True, "data": manager}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
