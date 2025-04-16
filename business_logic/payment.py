from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from uuid import uuid4
import requests
from schemas_validation.payment import CreateOrderRequest  
from database import get_db  
from config import RAZORPAY_URL, RAZORPAY_API_KEY, RAZORPAY_SECRET_KEY
from common.auth import get_current_user

router = APIRouter()


@router.post("/create-order")
def create_order(request: CreateOrderRequest, current_user: dict = Depends(get_current_user),):

    if current_user:
        razorpay_create_order_url = RAZORPAY_URL + "orders"
        
        notes = request.notes or {}
        notes["username"] = current_user["username"]

        payload = {
            "amount": request.amount,     
            "currency": request.currency,
            "receipt": "receipt_" + str(uuid4())[:30],
            "notes": notes
        }

        razorpay_auth_keys = (RAZORPAY_API_KEY, RAZORPAY_SECRET_KEY)

        try:
            response = requests.post(
                url=razorpay_create_order_url,
                json=payload,
                auth=razorpay_auth_keys
            )

            if response.status_code in (200, 201):
                return JSONResponse(content={"success": True, "data": response.json()}, status_code=status.HTTP_201_CREATED)

            error_message = response.json().get("error", "Unable to create order.")
            return JSONResponse(content={"success": False, "error": error_message}, status_code=status.HTTP_401_UNAUTHORIZED)

        except Exception as ex:
            return JSONResponse(content={"success": False, "error": str(ex)}, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    return JSONResponse(content={"success": False, "error": "Invalid user"}, status_code=status.HTTP_401_UNAUTHORIZED)

