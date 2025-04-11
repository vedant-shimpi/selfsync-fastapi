from fastapi import APIRouter
from database import get_db
from fastapi import Depends, HTTPException
from pymongo.errors import DuplicateKeyError
from database import get_db
from schemas import ManagerCreate   


router = APIRouter()


@router.post("/add_manager")
def add_manager(manager: ManagerCreate, db=Depends(get_db)):
    managers_collection = db["manager"]
    managers_collection.create_index("email", unique=True)
    try:
        managers_collection.insert_one({"email": manager.email})
        return {"message": "Manager added successfully"}
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Email already exists")