from fastapi import APIRouter, Depends, HTTPException, status, Query
from database import get_db, report_table_collection, answer_papers_collection, assessments_collection, users_collection, candidate_collection, managers_collection
from common.auth import get_current_user
from schemas_validation.answer_paper import SaveAnswerPaperRequest, ReportData, TraitScores, CandidateRequest
from datetime import datetime, timezone
from uuid import uuid4
from typing import List

router = APIRouter()


@router.post("/save_answer_paper", response_model=dict)
async def save_bulk_answer_papers(
    requests: List[SaveAnswerPaperRequest],
    db=Depends(get_db)
):
    try:
        now_time = datetime.now(timezone.utc)

        for request in requests:
            # Check if assessment exists
            assessment = await assessments_collection.find_one({"assessment_pk": request.assessment_id})
            if not assessment:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Assessment not found for ID: {request.assessment_id}")

            # Check if HR exists
            hr = await users_collection.find_one({"user_pk": request.hr_id})
            if not hr:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"HR not found for ID: {request.hr_id}")

            # Check if candidate exists
            candidate = await candidate_collection.find_one({"candidate_pk": request.candidate_id})
            if not candidate:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found!")

            # Check candidate OTP
            if candidate.get("otp") != request.otp:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP provided.")

            # Check if assessment already completed
            if candidate.get("is_assessment_completed") is True:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Exam already completed.")

            answer_paper_data = {
                "answer_paper_pk": str(uuid4()),
                "assessment_id": request.assessment_id,
                "hr_id": request.hr_id,
                "candidate_id": candidate["candidate_pk"],
                "manager_id": request.manager_id if not request.is_new_joiner else None,
                "is_new_joiner": request.is_new_joiner,
                "is_existing_emp": request.is_existing_emp,
                "first_name": request.first_name,
                "last_name": request.last_name,
                "answers": request.answers,
                "created_at": now_time,
                "updated_at": now_time
            }

            result = await answer_papers_collection.insert_one(answer_paper_data)
            answer_paper_id = result.inserted_id

            # Update candidate info
            update_fields = {
                "is_assessment_completed": True,
                "first_name": request.first_name,
                "last_name": request.last_name,
                "updated_at": now_time,
                "exam_completed_at": now_time,
                "answer_paper_id": str(answer_paper_id)
            }

            if not request.is_new_joiner and request.manager_id:
                update_fields["first_name"] = request.first_name
                update_fields["last_name"] = request.last_name
                manager = await managers_collection.find_one({"manager_pk": request.manager_id})
                if manager:
                    update_fields["manager_id"] = request.manager_id
                    update_fields["manager_email"] = manager.get("email")

                    full_name = manager.get("full_name", "").strip()
                    name_parts = full_name.split()

                    if len(name_parts) >= 2:
                        update_fields["manager_first_name"] = name_parts[0]
                        update_fields["manager_last_name"] = " ".join(name_parts[1:])
                    elif len(name_parts) == 1:
                        update_fields["manager_first_name"] = name_parts[0]
                        update_fields["manager_last_name"] = ""
                    else:
                        update_fields["manager_first_name"] = ""
                        update_fields["manager_last_name"] = ""

            await candidate_collection.update_one(
                {"candidate_pk": candidate["candidate_pk"]},
                {"$set": update_fields}
            )

            report_data = ReportData(
                report_pk=str(uuid4()),
                candidate_id=candidate["candidate_pk"],
                manager_id=update_fields.get("manager_id"),
                assessment_id=request.assessment_id,
                hr_id=request.hr_id,
                created_at=now_time,
                updated_at=now_time,
                person_name=f"{request.first_name} {request.last_name}"
            )

            await report_table_collection.insert_one(report_data.model_dump())

        return {
            "success": True,
            "message": f"Answer papers saved successfully for {len(requests)} candidates."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/get_reports", response_model=ReportData)
async def get_report(request: CandidateRequest, db=Depends(get_db)):
    report = await report_table_collection.find_one({"candidate_id": request.candidate_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found for the given candidate_id.")
    
    report["_id"] = str(report["_id"])
    return report