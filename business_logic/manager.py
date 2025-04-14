from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from fastapi import Depends, HTTPException
from business_logic.email import send_email
from pymongo.errors import DuplicateKeyError
from schemas import ManagerCreate, ManagerInfo
import random
import string  
from pymongo.collection import Collection
from datetime import datetime, timezone, timedelta
import uuid
from common.utils import hash_password
from common.auth import get_current_user

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
async def add_manager(manager: ManagerCreate, db=Depends(get_db)):
    users_collection = db["users"]
    managers_collection = db["manager"]

    users_collection.create_index("email", unique=True)
    users_collection.create_index("username", unique=True)
    managers_collection.create_index("email", unique=True)

    name_parts = manager.full_name.strip().split()
    first_name = name_parts[0]
    last_name = name_parts[-1] if len(name_parts) > 1 else ""

    hr_exists = await users_collection.find_one({"_id": manager.hr_id})
    if not hr_exists:
        return {"success": False, "message": "Provided hr_id does not exist in users table."}

    # Generate password and username
    password = generate_unique_password(first_name)
    while True:
        suffix = "".join(random.choices(string.digits, k=4))
        username = f"{first_name.lower()}_{suffix}"
        if not await users_collection.find_one({"username": username}):
            break

    now = datetime.now(timezone.utc)
    user_id = str(uuid.uuid4())

    try:
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
            "date_joined": now,
            "updated_at": now,
            "created_at": now
        }
        await users_collection.insert_one(user_data)

        await managers_collection.insert_one({
            "email": manager.email,
            "full_name": manager.full_name,
            "password": hash_password(password),
            "hr_id": manager.hr_id,
            "created_at": now,
            "updated_at": now
        })

        # Send credentials to manager
        send_email_with_password(manager.email, password, first_name)

        return {"success": True, "message": "Manager created, login enabled, and email sent."}

    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Email already exists in users or manager.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_manager_info", response_model=dict)
async def get_manager_info(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    try:
        managers_collection = db["manager"]
        manager = await managers_collection.find_one(
            {"email": current_user["email"]},
            {"_id": 0, "password": 0}
        )

        if not manager:
            raise HTTPException(status_code=404, detail="Manager not found")

        return {"success": True, "data": manager}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
