from typing import List, Optional,Union
from pydantic import UUID4, BaseModel, EmailStr, AnyUrl, HttpUrl, Field, field_validator
from decimal import Decimal
from datetime import datetime
from fastapi import Form, UploadFile, File
from uuid import UUID , uuid4
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
    company_email: Optional[EmailStr] = None
    company_size: Optional[str] = None


class OTPVerifyRequest(BaseModel):
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class CreateAssessment(BaseModel):
    id: Optional[UUID] = Field(default_factory=uuid4)
    assessment_name: str
    short_description: str
    long_description: str
    duration: int
    # hr_id:str

class AddPackage(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    assessments: str
    package_price: str
    per_assessment_price: str
    assessment_currency:str
    description: List[str]

class CreateContact(BaseModel):
    contact_id: UUID = Field(default_factory=uuid4)
    first_name: str
    last_name: str
    email: EmailStr
    mobile: str
    message: str
    contact_us_by:str


