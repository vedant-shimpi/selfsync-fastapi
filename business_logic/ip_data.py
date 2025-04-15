from database import get_db
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Request
from fastapi import Depends
from common.auth import get_current_user
import os
import httpx


API_KEY= os.getenv("IP_ADDRESS_KEY_GET_GEODATA")
router = APIRouter()

FIELDS = "ip,is_eu,city,country_name,country_code,currency,continent_name,continent_code,latitude,longitude,postal,calling_code,flag,emoji_flag,emoji_unicode"
ADMIN_EMAIL = "vedant.shimpi@digikore.com"  


def send_email(to: str, subject: str, html: str):
    print(f"Sending email to: {to}\nSubject: {subject}\nContent:\n{html}")

IP_REGEX = r"^\d{1,3}(\.\d{1,3}){3}$"

# Function to get the real client IP address (handles Nginx and proxies)
# Dont forgot add add config in NGINX
def get_real_client_ip(request: Request):
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()  # Get the real client IP from the X-Forwarded-For header
    return request.client.host  


@router.get("/fetch-ip-data")
async def get_ip_info(request: Request):

    client_ip = get_real_client_ip(request)
    
    url = f"https://api.ipdata.co/{client_ip}?api-key={API_KEY}&fields={FIELDS}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
            response.raise_for_status()
            data = response.json()
            return JSONResponse(
                status_code=200,
                content={
                    "status": {
                        "status": "success",
                        "detail": "IP data fetched successfully"
                    },
                    "data": data
                }
            )

    except httpx.HTTPStatusError as e:
        error_content = f"""
            <h2>IPData API Error</h2>
            <p><strong>Status:</strong> {e.response.status_code}</p>
            <p><strong>Response:</strong> {e.response.text}</p>
        """
        send_email(
            to=ADMIN_EMAIL,
            subject="🚨 IPData API Error Alert",
            html=error_content
        )

        return JSONResponse(
            status_code=e.response.status_code,
            content={
                "status": {
                    "status": "failed",
                    "detail": "There was an issue contacting the IP data service."
                },
                "data": None
            }
        )
    except httpx.RequestError as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": {
                    "status": "failed",
                    "detail": f"Network error: {str(e)}"
                },
                "data": None
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": {
                    "status": "failed",
                    "detail": f"Unexpected error: {str(e)}"
                },
                "data": None
            }
        )
