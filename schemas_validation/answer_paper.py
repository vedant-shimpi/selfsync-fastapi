from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union
from uuid import UUID
from datetime import datetime

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

class TraitScores(BaseModel):
    scores: Dict[str, Optional[float]] = Field(default_factory=lambda: {
        "Trait Inference": None,
        "Trait": None,
        "Evidence": None,
        "Model Mapping": None,
        "Mbti": None,
        "Big Five": None,
        "Disc": None,
        "Enneagram": None,
        "Cliftonstrengths": None,
        "Growth Area": None,
        "Assertiveness": None,
        "Conscientiousness": None,
        "Emotional Stability": None,
        "Introversion": None,
        "Resilience": None,
        "Thinking": None,
        "Steadiness": None,
        "Potential Blind Spots": None
    })
    out_of: Optional[float] = None

class ReportData(BaseModel):
    report_pk: str
    candidate_id: str
    manager_id: Optional[str]
    assessment_id: str
    hr_id: str
    status: str = "Pending"
    is_report_submitted: Optional[bool] = None
    created_at: datetime
    updated_at: datetime
    person_name: str
    summary: Optional[str] = None
    traits_score: TraitScores = Field(default_factory=TraitScores)
    trait_categories: Dict[str, Optional[float]] = Field(default_factory=lambda: {
        "Trait Inference": None,
        "Trait": None,
        "Evidence": None,
        "Model Mapping": None,
        "Mbti": None,
        "Big Five": None,
        "Disc": None,
        "Enneagram": None,
        "Cliftonstrengths": None,
        "Growth Area": None,
        "Assertiveness": None,
        "Conscientiousness": None,
        "Emotional Stability": None,
        "Introversion": None,
        "Resilience": None,
        "Thinking": None,
        "Steadiness": None,
        "Potential Blind Spots": None
    })

class CandidateRequest(BaseModel):
    candidate_id: str