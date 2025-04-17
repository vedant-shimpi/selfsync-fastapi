from pydantic import BaseModel, Field
from typing import List, Dict, Union
from uuid import UUID

class SaveAnswerPaperRequest(BaseModel):
    assessment_id: str
    hr_id: str
    otp: str
    candidate_id: str
    manager_id: Union[str, None] = None
    is_new_joiner: bool
    is_existing_emp: bool
    first_name: str
    last_name: str
    answers: List[Dict[str, str]] 