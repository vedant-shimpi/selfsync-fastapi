from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from database import user_collection
from common.auth import get_current_user
from schemas import UpdateUserProfileRequest
from bson import ObjectId
from database import get_db

router = APIRouter()

@router.get("/get_user_details", response_model=dict)
async def get_userprofile(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    try:
        user_id = current_user["_id"]
        users_collection = db["users"]
        managers_collection = db["manager"]

        user = await users_collection.find_one({"_id": user_id}, {"password": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user["_id"] = str(user["_id"])

        if user["user_type"] == "hr":
            # Fetch all managers added by HR
            manager_list_cursor = managers_collection.find({"hr_id": user_id}, {"password": 0})
            manager_list = []
            async for manager in manager_list_cursor:
                manager["_id"] = str(manager["_id"])
                manager_list.append(manager)

            return {
                "success": True,
                "data": {
                    "user_info": user,
                    "managers": manager_list
                }
            }

        return {
            "success": True,
            "data": user
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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