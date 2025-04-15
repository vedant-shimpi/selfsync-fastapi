from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import List, Optional
from datetime import datetime, timezone

class AddCandidateSchemaRequest(BaseModel):
    assessment_id : str = Field(..., min_length=32, max_length=40)
    position_title : Optional[str] = ""
    emails: List[EmailStr] = Field(...)  # accept only list of emails
    is_new_joiner: bool = True
    is_existing_emp: bool = False
    

    @model_validator(mode="after")  #  it is used to validate the model after all individual fields have been validated.
    def validate_flags_are_opposite(self) -> 'AddCandidateSchemaRequest':
        if self.is_new_joiner == self.is_existing_emp:
            raise ValueError("`is_new_joiner` and `is_existing_emp` must be opposites.")
        return self
    
    # @field_validator('is_new_joiner')  #  for individual field validation 
    # @classmethod
    # def validate_is_new_joiner(cls, v: str) -> str:
    #     if not v.isalnum():
    #         raise ValueError("assessment_id must be alphanumeric.")
    #     return v



class CandidateInfoPydanticSchema(BaseModel):
    _id: str  # assuming str_uuid_id is a string UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: EmailStr
    assessment_id: str
    hr_id: str
    is_new_joiner: bool
    is_existing_emp: bool
    otp: str
    otp_try_datetime: Optional[datetime] = None
    otp_created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    otp_verify_status: bool
    status: str
    manager_id: Optional[str] = None
    manager_email: Optional[EmailStr] = None
    manager_first_name: Optional[str] = None
    manager_last_name: Optional[str] = None
    black_listed: bool = False  # if candidate did somethin malicious activity 
    is_assessment_started: bool
    is_assessment_completed: bool
    exam_completed_at: Optional[datetime] = None  # update exam submission time
    candidate_score: float = 0.00
    candidate_remark: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        extra = "forbid"  # No extra fields allowed in input data