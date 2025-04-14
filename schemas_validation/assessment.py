from pydantic import BaseModel, EmailStr, Field
from typing import List


class AddCandidateSchemaRequest(BaseModel):
    assessment_id : str = Field(..., min_length=32, max_length=40)
    position_title : str = Field(..., min_length=3, max_length=40)
    emails: List[EmailStr] = Field(...)  # accept only list of emails


    