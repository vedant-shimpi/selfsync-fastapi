from fastapi import APIRouter
from fastapi import Depends, HTTPException
from pymongo.errors import DuplicateKeyError
import uuid
from schemas import CreateAssessment
from common.auth import get_current_user
from database import assessments_collection,packages_collection,get_db


router = APIRouter()


@router.post("/add_assessment")
async def add_assessment(assessment: CreateAssessment, current_user: dict = Depends(get_current_user)):
    try:
        assessment_data = assessment.dict()
        assessment_name = assessment.assessment_name.strip()

        # print(f"Checking for name: '{assessment_name}'")
        existing_assessment = await assessments_collection.find_one({
            "assessment_name": {
                "$regex": f"^{assessment_name}$",
                "$options": "i"
            }
        })

        if existing_assessment:
            raise HTTPException(status_code=400, detail="Assessment with this name already exists")

        # string_id = str(assessment_data["id"])
        # assessment_data["id"] = string_id
        # assessment_data["_id"] = string_id
        assessment_data["assessment_id"] = str(uuid.uuid4())

        result = await assessments_collection.insert_one(assessment_data)

        # print(f"Insert result: {result.inserted_id}")

        return {"message": "Assessment added successfully"}

    except Exception as e:
        print("Unhandled error:", str(e))
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
          
@router.get("/get_all_assessments")
async def get_all_assessments(current_user: dict = Depends(get_current_user),db=Depends(get_db)):
    data = []

    assessments = await assessments_collection.find().to_list(length=None)

    for item in assessments:
        data.append({
            "id": str(item.get("_id", "")),  # Ensures ObjectId is converted to string
            "assessment_name": item.get("assessment_name", ""),
            "short_description": item.get("short_description", ""),
            "long_description": item.get("long_description", ""),
            "duration": item.get("duration", "")
        })

    return {"assessments": data}

@router.get("/get_all_packages")
async def get_all_packages(current_user: dict = Depends(get_current_user),db=Depends(get_db)):
    data = []

    assessments = await packages_collection.find().to_list(length=None)

    for item in assessments:
        data.append({
            "id": str(item.get("_id", "")),  # Ensures ObjectId is converted to string
            "assessments": item.get("assessments", ""),
            "package_price": item.get("package_price", ""),
            "per_assessment_price": item.get("per_assessment_price", ""),
            "assessment_currency": item.get("assessment_currency", ""),
            "description": item.get("description", "")
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
