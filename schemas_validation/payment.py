from pydantic import BaseModel
from typing import Optional, Dict

class CreateOrderRequest(BaseModel):
    amount : int
    currency : str
    notes : Optional[Dict] = None