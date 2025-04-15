from fastapi import APIRouter, Depends, HTTPException, status
from database import get_db
from common.auth import get_current_user
from common.constants import CANDIDATE_STATUS
import uuid, random
from datetime import datetime, timezone, timedelta
from schemas_validation.assessment import AddCandidateSchemaRequest, CandidateInfoPydanticSchema
from database import users_collection, assessments_collection, position_collection, candidate_collection
from business_logic.email import send_html_email

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
            otp = str(random.randint(100000, 999999))
            candidate_info = CandidateInfoPydanticSchema(
                _id=str_uuid_id,
                # "first_name":"",
                # "last_name":"",
                email=candidate_email,
                assessment_id= assessments_document['_id'],
                hr_id=hr_users_document["_id"],
                is_new_joiner= request.is_new_joiner,
                is_existing_emp= request.is_existing_emp,
                otp= otp,
                # "otp_try_datetime": None,
                # "otp_created_at": now_time,
                otp_verify_status= False,
                status=CANDIDATE_STATUS["otp_sent"],
                # "manager_id":'',
                # "manager_email":'',
                # "manager_first_name":'',
                # "manager_last_name":'',
                # black_listed=False,  # if candidate did somethin malicious activity 
                is_assessment_started=False,
                is_assessment_completed=False,
                # "exam_completed_at":None,  # update exam submission time
                candidate_score=0.00,
                # "candidate_remark":"",
                # "created_at":now_time,
                # "updated_at":now_time
            )
            await candidate_collection.insert_one(candidate_info.model_dump())  # model_dump()	Converts the Pydantic model into a regular Python dictionary. exclude_none=True	Removes any fields from the dictionary where the value is None. Mongo will not store those keys at all.
            send_html_email(
                subject="Assessment Invitation | SelfsyncAi",
                recipient=candidate_email,
                template_path="templates/assessment_invite.html",
                context={
                    "assessment_name": assessments_document["assessment_name"],
                    "duration": assessments_document["duration"],
                    "question_count": 60,
                    "due_date": now_time + timedelta(days=1),
                    "custom_instructions": "Read questions carefully and answer properly.",
                    "assessment_url": "https://assessment.selfsync.ai/test/?assessment={}&hr={}&candidate={}".format(assessments_document["_id"], hr_users_document["_id"], str_uuid_id)
                }
            )

        return {"success": True, "data": request, "message":"Candidate added successfully."}

    except Exception as e:
        return {"success": False, "data":request, "message":str(e)}
    