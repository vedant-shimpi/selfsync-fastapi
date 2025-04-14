from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from database import question_banks_collection, questions_collection, get_db
from common.auth import get_current_user
from schemas_validation.question_bank import SubjectRequest
from bson import ObjectId

router = APIRouter()

def convert_objectid(doc):
    """Recursively converts ObjectId fields to string in a dict or list"""
    if isinstance(doc, list):
        return [convert_objectid(item) for item in doc]
    elif isinstance(doc, dict):
        return {
            key: convert_objectid(value)
            for key, value in doc.items()
        }
    elif isinstance(doc, ObjectId):
        return str(doc)
    else:
        return doc

@router.post("/get_questions")
async def get_questions_by_subject(request: SubjectRequest, db=Depends(get_db)):


    bank = await question_banks_collection.find_one({"name": request.subject_name})
    if not bank:
        raise HTTPException(status_code=404, detail="Question bank not found")

    question_ids = bank.get("question_ids", [])
    questions_cursor = questions_collection.find({
        "_id": {"$in": question_ids}
    })
    questions = await questions_cursor.to_list(length=None)

    # Convert ObjectId strings
    clean_questions = [convert_objectid(q) for q in questions]

    return {
        "success": True,
        "subject": request.subject_name,
        "total_questions": len(clean_questions),
        "questions": clean_questions
    }
