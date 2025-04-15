from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from database import users_collection, managers_collection, get_db
from common.auth import get_current_user
from schemas_validation.user import UpdateUserProfile, ManagerStatusUpdate
from bson import ObjectId

router = APIRouter()

@router.get("/get_user_details", response_model=dict)
async def get_userprofile(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    try:
        user_id = current_user["_id"]

        user = await users_collection.find_one({"_id": user_id}, {"password": 0})
        if not user:
            return {"success": False, "message": "User not found"}

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
async def update_userprofile(
    payload: UpdateUserProfile,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    try:
        user_id = current_user["_id"]
        users_collection = db["users"]

        update_data = {k: v for k, v in payload.dict().items() if v is not None}

        if "company_name" in update_data:
            update_data["orgnization"] = update_data.pop("company_name")

        if not update_data:
            return {"success": False, "message": "No fields provided to update"}

        result = await users_collection.update_one(
            {"_id": user_id},
            {"$set": update_data}
        )

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



@router.post("/deactivate_manager", response_model=dict)
async def deactivate_manager(
    payload: ManagerStatusUpdate,current_user: dict = Depends(get_current_user),
    db=Depends(get_db)):
    try:
        if current_user.get("user_type") != "hr":
            return {"success": False, "message": "You are not authorized to perform this action."}

        manager_user_id = payload.id
        is_deleted_value = payload.is_deleted

        manager_user = await users_collection.find_one({
            "_id": manager_user_id,
            "user_type": "manager"
        })
        if not manager_user:
            return {"success": False, "message": "Manager not found or invalid user type."}

        #  Check that this manager was added by current HR
        manager_doc = await managers_collection.find_one({"_id": manager_user_id})
        if not manager_doc or manager_doc.get("hr_id") != current_user["_id"]:
            return {"success": False, "message": "You are not authorized to modify this manager."}

        #  Update is_deleted
        result = await users_collection.update_one(
            {"_id": manager_user_id},
            {"$set": {"is_deleted": is_deleted_value}}
        )

        if result.modified_count == 0:
            return {"success": False, "message": "No change made. Manager is already in that status."}

        return {
            "success": True,
            "message": f"Manager {'deactivated' if is_deleted_value else 'activated'} successfully."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
