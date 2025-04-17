from fastapi import APIRouter,status, HTTPException
from schemas import CreateContact
from business_logic.email import send_html_email
from database import contact_collection


router = APIRouter()


@router.post("/add_contact", status_code=status.HTTP_201_CREATED)
async def add_contact(contact: CreateContact):
    try:
        contact_collection.insert_one(contact.model_dump())

        # Decide the template based on contact_us_by
        if contact.contact_us_by == "contact":
            template = "contact_us_thankyou.html"
        elif contact.contact_us_by == "demo":
            template = "schedule_demo_thankyou.html"
        else:
            template = "default.html" 

        send_html_email(
            subject="Your contact info was submitted successfully",
            recipient=contact.email,
            template_name=template,
            context={"first_name": contact.first_name.capitalize()}
        )
        
        return {"message": "Your data has been successfully submitted."}
    
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while submitting your data>> {str(ex)}")
    