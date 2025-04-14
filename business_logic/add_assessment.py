from fastapi import APIRouter
from fastapi import Depends, HTTPException
from pymongo.errors import DuplicateKeyError
from database import get_db
from schemas import CreateAssessment, AddPackage
from common.auth import get_current_user

router = APIRouter()

@router.post("/add_assessment")
def add_assessment(assessment: CreateAssessment,current_user: dict = Depends(get_current_user), db=Depends(get_db)):
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
async def get_all_assessments(current_user: dict = Depends(get_current_user),db=Depends(get_db)):
    assessment_collection = db["assessment"]
    data = []

    assessments = await assessment_collection.find().to_list(length=None)

    for item in assessments:
        data.append({
            "id": str(item.get("_id", "")),  # Ensures ObjectId is converted to string
            "short_description": item.get("short_description", ""),
            "long_description": item.get("long_description", ""),
            "duration": item.get("duration", "")
        })

    return {"assessments": data}

# @router.post("/add_package")
# async def add_package(assessment: AddPackage,current_user: dict = Depends(get_current_user), db=Depends(get_db)):
#     assessment_collection = db["packages"]

#     await assessment_collection.create_index("id", unique=True)

#     try:
#         assessment_data = assessment.dict()
#         assessment_data["id"] = str(assessment_data["id"])  # Convert UUID to string
#         await assessment_collection.insert_one(assessment_data)
#         return {"message": "Assessment package added successfully"}
#     except DuplicateKeyError:
#         raise HTTPException(status_code=400, detail="Assessment with this ID already exists")
