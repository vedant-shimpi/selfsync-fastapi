from typing import List, Optional,Union
from pydantic import UUID4, BaseModel, EmailStr, AnyUrl, HttpUrl, Field, field_validator
from decimal import Decimal
from datetime import datetime
from fastapi import Form, UploadFile, File
from uuid import UUID
from typing import Literal

class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    user_type: Literal["hr", "individual"]  # "Literal" force to enter either "hr" or "individual"
    company_name: Optional[str] = None
    address: Optional[str] = None
    mobile: Optional[str] = None
    secondary_email: Optional[EmailStr] = None
    pin_code: Optional[str] = None
    gender: Optional[str] = None


class OTPVerifyRequest(BaseModel):
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UpdateUserProfileRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    user_type: Optional[str] = None
    address: Optional[str] = None
    mobile: Optional[str] = None
    orgnization: Optional[str] = None
    company_name: Optional[str] = None
    secondary_email: Optional[str] = None
    pin_code: Optional[str] = None
    gender: Optional[str] = None

    @field_validator("secondary_email", mode="before")
    @classmethod
    def validate_secondary_email(cls, v):
        if v in (None, ""):
            return None 
        try:
            from email_validator import validate_email
            return validate_email(v).email  
        except Exception:
            raise ValueError("Invalid email format for secondary_email")
        
class ManagerCreate(BaseModel):
    email: EmailStr
    full_name: str
    hr_id: str

class ManagerInfo(BaseModel):
    email: EmailStr

class CreateAssessment(BaseModel):
    id: UUID  
    short_description: str
    long_description: str
    duration: int