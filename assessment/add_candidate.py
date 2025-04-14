from fastapi import APIRouter, Depends, HTTPException, status
from database import get_db
from common.auth import get_current_user
import uuid
from datetime import datetime, timezone
from schemas_validation.assessment import AddCandidateSchemaRequest
from database import users_collection, assessments_collection, position_collection, candidate_collection


router = APIRouter()


@router.post("/add-candidate", response_model=dict)
async def add_candidate(request:AddCandidateSchemaRequest, curr_hr: dict = Depends(get_current_user), db=Depends(get_db)):
    try:
        hr_users_document = await users_collection.find_one({"email": curr_hr["email"]})
        if not hr_users_document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid token or user not found.")
        
        assessments_document = await assessments_collection.find_one({"_id":request.assessment_id})
        if not assessments_document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")
        
        position_document = await position_collection.find_one({"position_title":request.position_title, "user_id":hr_users_document["_id"]})
        now_time = datetime.now(timezone.utc)
        if not position_document:
            str_uuid_id = str(uuid.uuid4())
            position_details = {
                "_id": str_uuid_id,
                "position_title":request.position_title,
                "user_id": hr_users_document["_id"],
                "description":"",
                "created_at":now_time,
                "updated_at":now_time
            }
            await position_collection.insert_one(position_details)
            position_document = position_collection.find_one({"_id":str_uuid_id})
        for candidate_email in request.emails:
            str_uuid_id = str(uuid.uuid4())
            candidate_info = {
                "_id":str_uuid_id,
                "first_name":"",
                "last_name":"",
                "email":candidate_email,
                "assessment_id": assessments_document['_id'],
                "hr_id":hr_users_document["_id"],
                "manager_id":'',
                "black_listed":False,  # if candidate did somethin malicious activity 
                "candidate_score":0.00,
                "candidate_remark":"",
                "attented_exam":False,
                "exam_attented_at":None,  # update exam submission time
                "created_at":now_time,
                "updated_at":now_time
            }
            await candidate_collection.insert_one(candidate_info)
        return {"success": True, "data": request, "message":"Candidate added successfully."}

    except Exception as e:
        return {"success": False, "data":request, "message":str(e)}
    