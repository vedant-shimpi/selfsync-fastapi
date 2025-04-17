from fastapi import APIRouter
from fastapi import Depends, HTTPException
from pymongo.errors import DuplicateKeyError
from database import get_db
from schemas import CreateContact
from common.auth import get_current_user
from business_logic.email import send_html_email
import os

router = APIRouter()

@router.post("/add_contact")
async def add_contact(contact: CreateContact, db=Depends(get_db)):
    contact_collection = db["contact"]

    # Ensure unique contact_id
    contact_collection.create_index("contact_id", unique=True)

    try:
        contact_data = contact.dict()
        contact_data["contact_id"] = str(contact_data["contact_id"])
        contact_collection.insert_one(contact_data)

        # Decide the template based on contact_us_by
        if contact.contact_us_by == "contact":
            template = "contact_us_thankyou.html"
        elif contact.contact_us_by == "demo":
            template = "schedule_demo_thankyou.html"
        else:
            template = "default.html" 

        send_html_email(
            subject="Your contact info was submitted successfully",
            recipient=contact.email,
            template_name=template,
            context={"first_name": contact.first_name.capitalize()}
        )
        
        return {"message": "Your data has been successfully submitted."}

    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Contact with this ID already exists")


# @router.post("/add_contact")
# async def add_contact(contact: CreateContact, db=Depends(get_db)):
#     contact_collection = db["contact"]

#     # Ensure unique contact_id
#     contact_collection.create_index("contact_id", unique=True)

#     try:
#         contact_data = contact.dict()
#         contact_data["contact_id"] = str(contact_data["contact_id"])
#         contact_collection.insert_one(contact_data)

    
#         send_html_email(subject="Your contact info was submitted successfully", recipient= contact.email, template_name= "signup_otp.html", context= {"first_name":contact.first_name.capitalize()})
#         return {"message": "Your data has been successfully submitted."}

#     except DuplicateKeyError:
#         raise HTTPException(status_code=400, detail="Contact with this ID already exists")
    
