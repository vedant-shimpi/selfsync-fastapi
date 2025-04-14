from pydantic import BaseModel, EmailStr, Field
from typing import List


class ManagerCreate(BaseModel):
    email: EmailStr
    full_name: str
    hr_id: str

class ManagerInfo(BaseModel):
    email: EmailStr

