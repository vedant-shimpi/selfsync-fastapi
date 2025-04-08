from typing import List, Optional,Union
from pydantic import UUID4, BaseModel, EmailStr, AnyUrl, HttpUrl, Field, field_validator
from decimal import Decimal
from datetime import datetime
from fastapi import Form, UploadFile, File
from uuid import UUID

class SignupRequest(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    address: Optional[str] = None
    user_type: Optional[str] = None
    mobile: Optional[str] = None
    secondary_email: Optional[EmailStr] = None
    pin_code: Optional[str] = None
    gender: Optional[str] = None
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters long")


class OTPVerifyRequest(BaseModel):
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")

