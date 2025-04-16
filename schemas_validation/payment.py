from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class CreateOrderRequest(BaseModel):
    amount : int
    currency : str
    notes : Optional[Dict] = None


class PaymentBase(BaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    amount: str
    payment_status: str 
    subscription_type: Optional[str]
    currency: str
    # Optional payment details
    payment_method: Optional[str]
    card_holder_name: Optional[str]
    transaction_time: Optional[datetime]
    location: Optional[str]
    ip_address: Optional[str]
    customer_email: Optional[str]
    customer_phone: Optional[str]
    order_items: Optional[List[Any]] = []
    payment_gateway_response: Optional[Dict[str, Any]] = {}
    transaction_mode: Optional[str]
    payment_channel: Optional[str]

    # Razorpay extra fields (optional)
    discount_applied: Optional[str] = None
    tax_amount: Optional[str] = None
    shipping_address: Optional[str] = None
    transaction_reference_id: Optional[str] = None
    entity: Optional[str] = None
    status: Optional[str] = None
    email: Optional[str] = None
    contact: Optional[str] = None
    international: Optional[bool] = False
    amount_refunded: Optional[str] = None
    refund_status: Optional[str] = None
    description: Optional[List[str]] = None
    card_id: Optional[str] = None
    bank: Optional[str] = None
    wallet: Optional[str] = None
    vpa: Optional[str] = None
    notes: Optional[Dict[str, Any]] = None
    fee: Optional[str] = None
    tax: Optional[str] = None
    error_code: Optional[str] = None
    error_description: Optional[str] = None
    error_source: Optional[str] = None
    error_step: Optional[str] = None
    error_reason: Optional[str] = None
    acquirer_data: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    upi_vpa: Optional[str] = None


class PaymentResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]]

class PaymentRequest(BaseModel):
    payment_id: str = Field(..., description="Razorpay payment ID")
    form_no: Optional[str] = Field(None, description="Optional form number")
    occasion_no: Optional[str] = Field(None, description="Optional occasion number")
    razorpay_order_id: Optional[str] = Field(None, description="Optional Razorpay order ID")

