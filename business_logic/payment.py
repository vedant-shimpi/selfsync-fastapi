from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from uuid import uuid4
import requests
from schemas_validation.payment import CreateOrderRequest, PaymentResponse, PaymentBase, PaymentRequest, FailedPaymentRequest
from database import get_db, users_collection, packages_collection, failed_payments_collection
from config import RAZORPAY_URL, RAZORPAY_API_KEY, RAZORPAY_SECRET_KEY
from common.auth import get_current_user
from pymongo import ReturnDocument
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

router = APIRouter()

@router.post("/get-payment-details")
async def get_payment_details(
    request: PaymentRequest, current_user: dict = Depends(get_current_user)):
    try:
        if not RAZORPAY_API_KEY or not RAZORPAY_SECRET_KEY:
            return JSONResponse(
                content={"success": False, "error": "Razorpay API credentials are missing."}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR )

        payment_id = request.payment_id
        razorpay_api_url = RAZORPAY_URL + f"payments/{payment_id}"
        auth = (RAZORPAY_API_KEY, RAZORPAY_SECRET_KEY)

        # Make the request to Razorpay's API
        response = requests.get(razorpay_api_url, auth=auth)
        response.raise_for_status()  # Raises an error for 4xx/5xx status codes

        # Return the payment data as JSON
        return response.json()
    except requests.exceptions.HTTPError as e:
        return JSONResponse(
            content={"success": False, "error": "Failed to fetch payment details."}, status_code=response.status_code )
    except Exception as ex:
        return JSONResponse(
            content={"success": False, "error": str(ex)}, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY )
    

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


@router.post("/payment")
async def create_payment(payment: PaymentBase, current_user: dict = Depends(get_current_user)):
    if payment.payment_status != "Captured":
        raise HTTPException(status_code=400, detail="Payment not successful, please make the payment")
    if current_user["user_type"] not in ["hr", "individual"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: HR role required.")

    razorpay_auth_keys = (RAZORPAY_API_KEY, RAZORPAY_SECRET_KEY)
    print("payment.razorpay_payment_id", payment.razorpay_payment_id)
    razorpay_get_payment_url = RAZORPAY_URL + f"payments/{payment.razorpay_payment_id}"
    
    response = requests.get(url=razorpay_get_payment_url, auth=razorpay_auth_keys)
    if response.status_code not in (200, 201):
        return JSONResponse(content={"success": False, "error": "Razorpay verification failed."}, status_code=400)

    # Match package by amount
    package = await packages_collection.find_one({"package_price": payment.amount})
    if not package:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Package not found")

    # Update user document
    updated_user = await users_collection.find_one_and_update(
        {"_id": current_user["_id"]},
        {
            "$set": {
                "payment_status": "Captured",
                "assessments": package["assessments"],
                "package_price": package["package_price"]
            }
        },
        return_document=ReturnDocument.AFTER
    )

    if not updated_user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")

    return {
        "success": True,
        "message": "Payment captured and user updated.",
        "data": {
            "payment_status": "Captured",
            "assessments": package["assessments"],
            "package_price": package["package_price"]
        }
    }

@router.post("/failed-payment")
async def failed_payment(
    request_data: FailedPaymentRequest, current_user: dict = Depends(get_current_user)):

    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated!" )

    failed_payment_data = {
        "user_id": str(current_user["_id"]),
        "amount": request_data.amount,
        "contact": request_data.contact,
        "email": request_data.email,
        "razorpay_order_id": request_data.razorpay_order_id,
        "date_time": request_data.date_time or datetime.now(timezone.utc).isoformat(),
        "level": request_data.level,
        "problem": request_data.problem,
        "created_at": datetime.now(timezone.utc)
    }

    await failed_payments_collection.insert_one(failed_payment_data)

    return JSONResponse(
        content={"success": True, "message": "Saved successfully!"}, status_code=status.HTTP_201_CREATED)