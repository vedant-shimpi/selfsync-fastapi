from pydantic import BaseModel, Field


class VerifyCandidateOtpPydanticSchema(BaseModel):
    candidate_id:str = Field(...)
    otp: str = Field(...)

    
class ResendCandidateOtpPydanticSchema(BaseModel):
    candidate_id:str = Field(...)
    assessment_id:str = Field(...)
    hr_id:str = Field(...)
