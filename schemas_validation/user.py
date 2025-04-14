from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

class UpdateUserProfile(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None
    secondary_email: Optional[EmailStr] = None
    gender: Optional[str] = None
    orgnization: Optional[str] = None
    pin_code: Optional[str] = None
    address: Optional[str] = None
    user_type: Optional[str] = None
    registered_by: Optional[str] = None
    is_superuser: Optional[bool] = None
    is_staff: Optional[bool] = None
    is_active: Optional[bool] = None
    company_name: Optional[str] = None
    company_email: Optional[EmailStr] = None
    company_size: Optional[str] = None

class ManagerStatusUpdate(BaseModel):
    id: str
    is_active: bool