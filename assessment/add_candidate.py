from fastapi import APIRouter, Depends, HTTPException, status
from database import get_db
from common.auth import get_current_user
from common.constants import CANDIDATE_STATUS
import uuid, random
from datetime import datetime, timezone, timedelta
from schemas_validation.assessment import AddCandidateSchemaRequest, CandidateInfoPydanticSchema
from database import users_collection, assessments_collection, position_collection, candidate_collection
from business_logic.email import send_html_email
from bson.son import SON


router = APIRouter()


@router.post("/add-candidate", response_model=dict)
async def add_candidate(request:AddCandidateSchemaRequest, curr_hr: dict = Depends(get_current_user), db=Depends(get_db)):
    try:
        hr_users_document = await users_collection.find_one({"email": curr_hr["email"]})
        if not hr_users_document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid token or user not found.")
        
        assessments_document = await assessments_collection.find_one({"assessment_pk":request.assessment_id})
        if not assessments_document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")
        
        # email_count = len(request.emails)
        # credit_point = hr_users_document.get("credit_point", 0)

        # if email_count > credit_point:
        #     return {"success": False, "message": "Don't have sufficient credits."}
        
        position_document = await position_collection.find_one({"position_title":request.position_title, "user_id":hr_users_document["user_pk"]})
        now_time = datetime.now(timezone.utc)

        if not position_document:
            str_uuid_id = str(uuid.uuid4())
            position_details = {
                "position_pk": str_uuid_id,
                "position_title":request.position_title,
                "user_id": hr_users_document["user_pk"],
                "description":"",
                "created_at":now_time,
                "updated_at":now_time
            }
            await position_collection.insert_one(position_details)
            position_document = position_collection.find_one({"position_pk":str_uuid_id})

        for candidate_email in request.emails:
            str_uuid_id = str(uuid.uuid4())
            otp = str(random.randint(100000, 999999))

            candidate_info = CandidateInfoPydanticSchema(
                candidate_pk=str_uuid_id,
                # "first_name":"",
                # "last_name":"",
                email=candidate_email,
                assessment_id= assessments_document['assessment_pk'],
                hr_id=hr_users_document["user_pk"],
                is_new_joiner= request.is_new_joiner,
                is_existing_emp= request.is_existing_emp,
                otp= otp,
                # "otp_try_datetime": None,
                otp_created_at= now_time,
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
                template_name="assessment-invite.html",
                context={
                    "assessment_name": assessments_document["assessment_name"],
                    "duration": assessments_document["duration"],
                    "question_count": assessments_document.get("question_count", 60),
                    "due_date": (now_time + timedelta(days=1)).strftime("%d/%m/%Y %H:%M"),
                    "custom_instructions": "Read questions carefully and answer properly.",
                    "assessment_url": "https://assessment.selfsync.ai/test/?assessment={}&hr={}&candidate={}&is_new_joiner={}".format(assessments_document["assessment_pk"], hr_users_document["user_pk"], str_uuid_id, request.is_new_joiner),
                    "otp":otp
                }
            )

        # Deduct credits from HR account
        # updated_credit = credit_point - email_count
        # await users_collection.update_one(
        #     {"user_pk": hr_users_document["user_pk"]},
        #     {"$set": {"credit_point": updated_credit}}
        # )

        return {"success": True, "data": request, "message": "Candidate(s) added successfully."}

    except Exception as e:
        return {"success": False, "data":request, "message":str(e)}
    

@router.get("/alocated-assessment-history")
async def alocated_assessment_history(curr_hr: dict = Depends(get_current_user),):
    pipeline = [
        {
            "$match": {
                "hr_id": curr_hr["user_pk"],
            }
        },
        {
            "$project": {
                "date_only": {
                    "$dateToString": { "format": "%Y-%m-%d %H:%M", "date": "$created_at" }
                },
                "candidate_pk":1, "email": 1, "is_assessment_started":1, "is_assessment_completed":1,
                "exam_completed_at":1, "candidate_score":1, "candidate_remark":1, "assessment_id":1,
                "is_new_joiner":1, "is_existing_emp":1, "manager_id":1, "manager_email":1,
                "manager_first_name":1, "manager_last_name":1,
            }
        },
        {
            "$lookup": {
                "from": "assessment",
                "let": { "aid": "$assessment_id" },
                "pipeline": [
                    {
                        "$match": {
                            "$expr": { "$eq": ["$assessment_pk", "$$aid"] }
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "assessment_name": 1
                        }
                    }
                ],
                "as": "assessment_info"
            }
        },
        {
            "$addFields": {
                "assessment_name": {
                    "$arrayElemAt": ["$assessment_info.assessment_name", 0]
                }
            }
        },
        {
            "$group": {
                "_id": {  # _id is used for group by; we can pass multiple parameters over here
                    "date": "$date_only",
                    "new_joiner_flag": "$is_new_joiner",
                    "assessment_id": "$assessment_id"
                },
                "count": { "$sum": 1 },
                # "assessment_ids":{ "$addToSet": "$assessment_id" },  # $addToSet = If multiple candidates may have different assessment IDs on the same date; $first = If all assessment_ids are same and you only want one
                "candidates": {
                    "$push": {
                        "candidate_pk":"$candidate_pk", "email":"$email", "is_assessment_started":"$is_assessment_started",
                        "is_assessment_completed":"$is_assessment_completed",
                        "exam_completed_at":"$exam_completed_at", "candidate_score":"$candidate_score",
                        "candidate_remark":"$candidate_remark", "is_new_joiner":"$is_new_joiner",
                        "is_existing_emp":"$is_existing_emp", "manager_id":"$manager_id",
                        "manager_email":"$manager_email", "manager_first_name":"$manager_first_name",
                        "manager_last_name":"$manager_last_name", "assessment_name": "$assessment_name"
                    }
                }
            }
        },
        {
            "$sort": SON([("_id.date", -1)])   # latest date on top
        }
    ]
    cursor = candidate_collection.aggregate(pipeline)
    result = await cursor.to_list(length=None)
    return {"alocated_assessment_history":result}
