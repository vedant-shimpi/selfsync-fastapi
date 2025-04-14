from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from database import user_collection
from common.auth import get_current_user
from schemas import UpdateUserProfile
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

        # If the user is of type 'manager', fetch the manager details
        if user["user_type"] == "manager":
            manager = await managers_collection.find_one({"_id": user["manager_id"]})
            if manager:
                manager["_id"] = str(manager["_id"])

                return {
                    "success": True,
                    "data": {
                        "user_info": user,
                        "manager_info": manager
                    }
                }
            else:
                return {
                    "success": True,
                    "data": {
                        "user_info": user,
                        "manager_info": None
                    }
                }

        if user["user_type"] == "hr":
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


@router.post("/update_user_details", response_model=dict)
async def update_userprofile(payload: UpdateUserProfile, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    try:
        user_id = current_user["_id"]
        users_collection = db["users"]

        update_data = {k: v for k, v in payload.dict().items() if v is not None}

        if "company_name" in update_data:
            update_data["orgnization"] = update_data.pop("company_name")

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided to update")

        result = await users_collection.update_one({"_id": user_id}, {"$set": update_data})

        if result.modified_count == 0:
            return {"success": False, "message": "User not found or no changes made"}

        updated_user = await users_collection.find_one({"_id": user_id}, {"password": 0})
        if not updated_user:
            return {"success": False, "message": "User not found"}

        updated_user["_id"] = str(updated_user["_id"])

        return {
            "success": True,
            "message": "User details updated successfully",
            "data": updated_user
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


