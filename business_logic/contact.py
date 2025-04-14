from fastapi import APIRouter
from fastapi import Depends, HTTPException
from pymongo.errors import DuplicateKeyError
from database import get_db
from schemas import CreateContact
from common.auth import get_current_user

router = APIRouter()

@router.post("/add_contact")
async def add_contact(contact: CreateContact, db=Depends(get_db)):
    contact_collection = db["contact"]

    contact_collection.create_index("contact_id", unique=True)

    try:
        contact_data = contact.dict()
        contact_data["contact_id"] = str(contact_data["contact_id"]) 
        contact_collection.insert_one(contact_data)
        return {"message": "Contact added successfully"}
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Contact with this ID already exists")