from fastapi import APIRouter, Depends, HTTPException, status
from database import users_collection, position_collection
from common.auth import get_current_user


router = APIRouter()


@router.get("/get-position-title-list", response_model=dict)
async def get_position_list(curr_hr: dict = Depends(get_current_user)):
    try:
        hr_users_document = await users_collection.find_one({"email": curr_hr["email"]})
        if not hr_users_document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid token or user not found.")
        
        positions_cursor_list = [doc["position_title"] async for doc in position_collection.find({"user_id": hr_users_document["user_pk"]})]

        if not positions_cursor_list:
            return {"success":False, "data":[], "message":"Data not found."}
        
        return {"success":True, "data":positions_cursor_list, "message":"Data fetch successfully."}
    except Exception as ex:
        return {"success":False, "data":[], "message":str(ex)}
    