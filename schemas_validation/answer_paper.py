from pydantic import BaseModel, Field
from typing import List, Dict, Union
from uuid import UUID

class SaveAnswerPaperRequest(BaseModel):
    assessment_id: str
    hr_id: str
    candidate_id: str
    manager_id: Union[str, None] = None
    is_new_joiner: bool
    is_existing_emp: bool
    answers: List[Dict[str, str]] 