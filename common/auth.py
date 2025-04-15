from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from common.utils import decode_access_token
from database import users_collection

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
# OAuth2PasswordBearer tells FastAPI how to expect the token (i.e., from the Authorization: Bearer <token> header).
# tokenUrl="login" refers to the route where the token will be generated.
# tokenUrl="login" only used in OpenAPI docs (Swagger UI) to help users know where to get the token.

async def get_current_user(token: str = Depends(oauth2_scheme)):
    email = decode_access_token(token)
    if email is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
