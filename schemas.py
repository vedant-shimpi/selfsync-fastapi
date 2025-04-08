from typing import List, Optional,Union
from pydantic import UUID4, BaseModel, EmailStr, AnyUrl, HttpUrl, Field, field_validator
from decimal import Decimal
from datetime import datetime
from fastapi import Form, UploadFile, File
from uuid import UUID

class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    address: str
    referred_by: str

class OTPVerifyRequest(BaseModel):
    otp: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str