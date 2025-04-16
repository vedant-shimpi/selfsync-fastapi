from fastapi import APIRouter, Depends, HTTPException, status
from database import get_db, answer_papers_collection, assessments_collection, users_collection, candidate_collection
from common.auth import get_current_user
from schemas_validation.answer_paper import SaveAnswerPaperRequest
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
            assessment = await assessments_collection.find_one({"_id": request.assessment_id})
            if not assessment:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Assessment not found for ID: {request.assessment_id}")

            # Check if HR exists
            hr = await users_collection.find_one({"_id": request.hr_id})
            if not hr:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"HR not found for ID: {request.hr_id}")

            # Check if candidate exists
            candidate = await candidate_collection.find_one({"id": request.candidate_id})
            if not candidate:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Candidate not found for ID: {request.candidate_id}")

            # Save answer paper
            answer_paper_data = {
                "_id": str(uuid4()),
                "assessment_id": request.assessment_id,
                "hr_id": request.hr_id,
                "candidate_id": request.candidate_id,
                "manager_id": request.manager_id if request.is_new_joiner else None,
                "is_new_joiner": request.is_new_joiner,
                "is_existing_emp": request.is_existing_emp,
                "answers": request.answers,
                "created_at": now_time,
                "updated_at": now_time
            }
            result = await answer_papers_collection.insert_one(answer_paper_data)
            answer_paper_id = result.inserted_id 

            #update fields
            update_fields = {
            "is_assessment_completed": True,
            "updated_at": now_time,
            "exam_completed_at": now_time,
            "answer_paper_id": str(answer_paper_id)
            }
            if request.is_new_joiner and request.manager_id:
                update_fields["manager_id"] = request.manager_id

            candidate_doc = await candidate_collection.find_one({"id": request.candidate_id})
            if not candidate_doc:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Candidate not found for ID: {request.candidate_id}")

            result = await candidate_collection.update_one(
                {"id": request.candidate_id},
                {"$set": update_fields}
            )

        return {
            "success": True,
            "message": f"Answer papers saved successfully for {len(requests)} candidates."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

