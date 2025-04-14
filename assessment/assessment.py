from fastapi import APIRouter
# from sqlalchemy.orm import Session
# from sqlalchemy.sql import text
from config import oauth2_scheme, authenticate_user
from database import get_db
from fastapi import Depends, HTTPException
# from assessment.email import send_email
from passlib.context import CryptContext
from config import oauth2_scheme, authenticate_user
from schemas import UpdateUserProfileRequest
from pymongo.errors import DuplicateKeyError
from database import get_db
from schemas import CreateAssessment 

router = APIRouter()


@router.post("/add_assessment")
def add_assessment(assessment: CreateAssessment, db=Depends(get_db)):
    assessment_collection = db["assessment"]

    # Create a unique index on 'id' to prevent duplicate entries
    assessment_collection.create_index("id", unique=True)

    try:
        # assessment_collection.insert_one(assessment.dict())
        assessment_data = assessment.dict()
        assessment_data["id"] = str(assessment_data["id"])  # convert UUID to string
        assessment_collection.insert_one(assessment_data)
        return {"message": "Assessment added successfully"}
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Assessment with this ID already exists")
    
@router.get("/get_all_assessments")
def get_all_assessments(db=Depends(get_db)):
    assessment_collection = db["assessment"]
    data = []

    for item in assessment_collection.find():
        data.append({
            "id": item["id"],
            "short_description": item["short_description"],
            "long_description": item["long_description"],
            "duration": item["duration"]
        })

    return {"assessments": data}