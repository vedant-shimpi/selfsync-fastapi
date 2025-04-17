from pydantic import BaseModel, EmailStr, Field
from typing import List

class AssessmentRequest(BaseModel):
    # assessment_id: str
    subject_name: str
    candidate_id: str
    otp: str
