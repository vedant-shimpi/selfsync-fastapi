from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from database import user_collection
from common.auth import get_current_user
from schemas import UpdateUserProfileRequest
from bson import ObjectId


router = APIRouter()

@router.get("/get_userprofile", response_model=dict)
async def get_userprofile(current_user: dict = Depends(get_current_user)):

    try:
        user = current_user  # This is already the MongoDB user document

        if not user:
            return {"success": False, "message": "User not found."}

        gender_mapping = {0: "female", 1: "male", 2: "other", None: "null"}
        gender_value = gender_mapping.get(user.get("gender"), "other")

        payment_mapping = {0: "Not Paid", 1: "Paid", 2: "Exhausted"}
        payments = payment_mapping.get(user.get("payment_status"), "Not Paid")

        registered_by_mapping = {0: "user", 1: "admin"}
        registered_by_value = registered_by_mapping.get(int(user.get("registered_by", 0)), "")

        user_data = {
            "id": str(user["_id"]),
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "email": user.get("email", ""),
            "mobile": user.get("mobile", ""),
            "username": user.get("username", ""),
            "address": user.get("address", ""),
            "user_type": user.get("user_type", ""),
            "secondary_email": user.get("secondary_email", ""),
            "registered_by": registered_by_value,
            "pin_code": user.get("pin_code", ""),
            "is_staff": user.get("is_staff", False),
            "payment_status": payments,
            "company_name": user.get("orgnization", ""),
            "is_active": user.get("is_active", True),
            "date_joined": user.get("date_joined").strftime('%Y-%m-%d %H:%M:%S') if user.get("date_joined") else None,
            "is_superuser": user.get("is_superuser", False),
            "otp_verify_status": user.get("otp_verify_status", False),
            "gender": gender_value,
            "last_login": user.get("last_login").strftime('%Y-%m-%d %H:%M:%S') if user.get("last_login") else None,
        }

        return {"success": True, "data": user_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.post("/update_userprofile", response_model=dict)
async def update_userprofile(
    request: UpdateUserProfileRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user["_id"]

        update_data = request.model_dump(exclude_unset=True)

        if "gender" in update_data:
            gender_mapping = {"female": 0, "male": 1}
            update_data["gender"] = gender_mapping.get(update_data["gender"].lower(), 2)

        if "registered_by" in update_data:
            registered_by_mapping = {"user": 0, "admin": 1}
            update_data["registered_by"] = registered_by_mapping.get(update_data["registered_by"].lower(), 2)

        if "company_name" in update_data:
            update_data["orgnization"] = update_data.pop("company_name")

        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields provided for update.")

        result = await user_collection.update_one(
            {"_id": ObjectId(user_id)},  # ObjectId(user_id) ensures MongoDB _id is correctly cast from string.
            {"$set": update_data}
        )

        if result.modified_count == 0:
            return {"success": False, "message": "No changes were made."}

        return {"success": True, "message": "User profile updated successfully."}

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))