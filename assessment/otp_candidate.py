from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse
from database import candidate_collection, assessments_collection, users_collection
import random
from datetime import datetime, timezone, timedelta
from business_logic.email import send_html_email
from schemas_validation.candidate_otp import VerifyCandidateOtpPydanticSchema, ResendCandidateOtpPydanticSchema
from bson import ObjectId


router = APIRouter()


@router.post("/verify-candiate-otp")
async def verify_candiate_otp(request:VerifyCandidateOtpPydanticSchema):
    try:
        candidate_document = await candidate_collection.find_one({"id": request.candidate_id})
        if not candidate_document:
            return JSONResponse(content={"success":False, "message":"Invalid candidate id."}, status_code=status.HTTP_404_NOT_FOUND)
        
        now = datetime.now(timezone.utc)

        # Check if user is blocked
        otp_blocked_until_dt = candidate_document.get("otp_blocked_until")
        if otp_blocked_until_dt and otp_blocked_until_dt.tzinfo is None:
            # Convert naive to aware
            otp_blocked_until_dt = otp_blocked_until_dt.replace(tzinfo=timezone.utc)
        if candidate_document.get("otp_blocked_until") and otp_blocked_until_dt > now:
            return JSONResponse(content={"success":False, "message":f"Too many attempts. Try again after {candidate_document['otp_blocked_until']}"}, status_code=status.HTTP_403_FORBIDDEN)
        otp_created_at = candidate_document.get("otp_created_at")
        if otp_created_at and otp_created_at.tzinfo is None:
            # Convert naive to aware
            otp_created_at = otp_created_at.replace(tzinfo=timezone.utc)
        # Check if OTP is expired
        if not otp_created_at or (otp_created_at + timedelta(hours=2)) < now:
            return JSONResponse(content={"success":False, "message":"OTP has expired. Please request a new one."}, status_code=status.HTTP_403_FORBIDDEN)

        # Check if OTP is correct
        if candidate_document["otp"] == request.otp:
            # Reset attempt count and mark as verified
            await candidate_collection.update_one(
                {"id": request.candidate_id},
                {
                    "$set": {
                        "otp_verify_status": True,
                        "otp_attempts": 0,
                        "otp_blocked_until": None,
                    }
                }
            )
            return JSONResponse(content={"success":True, "message":"OTP verified successfully."}, status_code=status.HTTP_200_OK)

        # OTP is wrong, increment attempts
        attempts = candidate_document.get("otp_attempts", 0) + 1

        update_data = {
            "otp_attempts": attempts,
            "otp_try_datetime": now,
        }

        # If 3 wrong attempts, block for 30 minutes
        if attempts >= 3:
            update_data["otp_blocked_until"] = now + timedelta(minutes=30)
            update_data["otp_attempts"] = 0  # Optional: reset or keep at 3

        await candidate_collection.update_one(
            {"id": request.candidate_id},
            {"$set": update_data}
        )
        return JSONResponse(content={"success":False, "message":"Invalid OTP."}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as ex:
        return JSONResponse(content={"success":False, "message":str(ex)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

@router.post("/resend-candidate-otp")
async def resend_candidate_otp(request: ResendCandidateOtpPydanticSchema):
    candidate_document = await candidate_collection.find_one({"id":request.candidate_id})
    if not candidate_document:
        return JSONResponse(content={"success":False, "message":"Invalid candidate id."}, status_code=status.HTTP_404_NOT_FOUND)
    
    assessments_document = await assessments_collection.find_one({"_id":request.assessment_id})
    if not assessments_document:
        return JSONResponse(content={"success":False, "message":"Invalid assessment id."}, status_code=status.HTTP_404_NOT_FOUND)
    
    hr_users_document = await users_collection.find_one({"_id":request.hr_id})
    if not hr_users_document:
        return JSONResponse(content={"success":False, "message":"Invalid hr id."}, status_code=status.HTTP_404_NOT_FOUND)
    
    now = datetime.now(timezone.utc)

    # Check if resend is blocked
    blocked_until = candidate_document.get("otp_resend_blocked_until")
    if blocked_until and blocked_until > now:
        wait_seconds = int((blocked_until - now).total_seconds())
        return JSONResponse(content={"success":False, "message":f"OTP resend limit reached. Try again after {wait_seconds // 60} minutes."}, status_code=status.HTTP_403_FORBIDDEN)

    # Check resend count
    resend_count = candidate_document.get("otp_resend_count", 0)
    if resend_count >= 5:
        await candidate_collection.update_one(
            {"id": request.candidate_id},
            {
                "$set": {
                    "otp_resend_blocked_until": now + timedelta(minutes=10),
                    "otp_resend_count": 0  # Optional: reset or keep at 5
                }
            }
        )
        return JSONResponse(content={"success":False, "message":"Maximum resend attempts reached. Try again after 10 minutes."}, status_code=status.HTTP_403_FORBIDDEN)

    # Generate new OTP
    new_otp = str(random.randint(100000, 999999))

    # Update in DB
    await candidate_collection.update_one(
        {"id": request.candidate_id},
        {
            "$set": {
                "otp": new_otp,
                "otp_created_at": now,
            },
            "$inc": {
                "otp_resend_count": 1
            }
        }
    )
    send_html_email(subject="New OTP from SelfsyncAi", recipient=candidate_document['email'], template_name="assessment-invite.html", 
                    context={
                    "assessment_name": assessments_document["assessment_name"],
                    "duration": assessments_document["duration"],
                    "question_count": assessments_document.get("question_count", 60),
                    "due_date": (now + timedelta(days=1)).strftime("%d/%m/%Y %H:%M"),
                    "custom_instructions": "Read questions carefully and answer properly.",
                    "assessment_url": "https://assessment.selfsync.ai/test/?assessment={}&hr={}&candidate={}&is_new_joiner={}".format(assessments_document["_id"], hr_users_document["_id"], request.candidate_id, candidate_document["is_new_joiner"]),
                    "otp":new_otp
                })
    return JSONResponse(content={"success":True, "message":"OTP resent successfully"}, status_code=status.HTTP_200_OK)