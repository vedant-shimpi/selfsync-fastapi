from pydantic import BaseModel, EmailStr, Field
from typing import List

class SubjectRequest(BaseModel):
    subject_name: str
