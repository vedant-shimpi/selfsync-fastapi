from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from database import question_banks_collection, questions_collection, get_db, assessments_collection, candidate_collection
from schemas_validation.question_bank import AssessmentRequest
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()

def remove_question_data(questions):
    clean_list = []
    for question in questions:
        cleaned = {
            "_id": str(question["_id"]),
            "question_text": question["question_text"],
            "category": question.get("category"),
            "type": question.get("type"),
            "difficulty": question.get("difficulty"),
            "skill_id": str(question["skill_id"]) if "skill_id" in question else None,
            "options": [
                {
                    "id": option["id"],
                    "text": option["text"]
                } for option in question.get("options", [])
            ]
        }
        clean_list.append(cleaned)
    return clean_list


@router.post("/get_questions")
async def get_questions_by_assessment(request: AssessmentRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        # assessment = await assessments_collection.find_one({"_id": (request.assessment_id)})
        # if not assessment:
        #     return JSONResponse(status_code=404, content={"success": False, "message": "Assessment not found"})

        # assessment_name = assessment.get("assessment_name")
        # if not assessment_name:
        #     return JSONResponse(status_code=400, content={"success": False, "message": "Assessment name not available"})

        # question_bank = await question_banks_collection.find_one({"name": assessment_name})
        # if not question_bank:
        #     return JSONResponse(status_code=404, content={"success": False, "message": "Question bank not found for the assessment"})

        # question_ids = question_bank.get("question_ids", [])
        # if not question_ids:
        #     return JSONResponse(status_code=200, content={"success": True, "message": "No questions linked to the bank", "questions": []})
        
        bank = await question_banks_collection.find_one({"name": request.subject_name})
        if not bank:
            return {"success": False, "message": "Question bank not found"}
        
        candidate = await candidate_collection.find_one ({"candidate_pk": (request.candidate_id)})
        if not candidate:
            return JSONResponse(status_code=404, content={"success": False, "message": "Candidate not found!"})
        
        # Check OTP match
        if candidate.get("otp") != request.otp:
            return JSONResponse(status_code=400, content={"success": False, "message": "Invalid OTP!"})
        
        candidate = await candidate_collection.find_one({"is_assessment_completed": False, "candidate_pk": (request.candidate_id)})
        if not candidate:
            return JSONResponse(status_code=404, content={"success": False, "message": "Candidate already finished exam!"})

        # Fetch questions
        # questions_cursor = questions_collection.find({
        #     "_id": {"$in": question_ids}})
        # questions = await questions_cursor.to_list(length=None)
        question_ids = bank.get("question_ids", [])
        questions_cursor = questions_collection.find({
            "question_id": {"$in": question_ids}
        })
        questions = await questions_cursor.to_list(length=None)

        cleaned_questions = remove_question_data(questions)

        return {
            "success": True,
            # "assessment_name": assessment_name,
             "subject": request.subject_name,
            "total_questions": len(cleaned_questions),
            "questions": cleaned_questions
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "message": f"Server error: {str(e)}"})