from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from database import question_banks_collection, questions_collection, get_db
from common.auth import get_current_user
from schemas_validation.question_bank import SubjectRequest
from common.auth import get_current_user

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
async def get_questions_by_subject(
    request: SubjectRequest,
    db=Depends(get_db)):
    bank = await question_banks_collection.find_one({"name": request.subject_name})
    if not bank:
        return {"success": False, "message": "Question bank not found"}

    question_ids = bank.get("question_ids", [])
    questions_cursor = questions_collection.find({
        "_id": {"$in": question_ids}
    })
    questions = await questions_cursor.to_list(length=None)

    clean_questions = remove_question_data(questions)

    return {
        "success": True,
        "subject": request.subject_name,
        "total_questions": len(clean_questions),
        "questions": clean_questions
    }

