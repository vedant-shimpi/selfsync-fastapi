from fastapi import APIRouter
from database import get_db
from fastapi import Depends, HTTPException
from business_logic.email import send_email
from pymongo.errors import DuplicateKeyError
from schemas import ManagerCreate, ManagerInfo
import random
import string  
from pymongo.collection import Collection

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
def add_manager(manager: ManagerCreate, db=Depends(get_db)):
    managers_collection = db["manager"]
    managers_collection.create_index("email", unique=True)

    name_parts = manager.full_name.strip().split()
    first_name = name_parts[0]
    last_name = name_parts[-1] if len(name_parts) > 1 else ""

    # Generate password
    password = generate_unique_password(first_name)

    try:
        managers_collection.insert_one({
            "email": manager.email,
            "full_name": manager.full_name,
            "password": password
        })

        send_email_with_password(manager.email, password, first_name)

        return {"message": "Manager added and email sent successfully."}
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Email already exists")


@router.get("/get_manager_info")
def get_manager_info(query: ManagerInfo, db=Depends(get_db)):
    managers_collection: Collection = db["manager"]
    
    manager = managers_collection.find_one({"email": query.email}, {"_id": 0, "password": 0})  

    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")

    return {"success": True, "data": manager}
