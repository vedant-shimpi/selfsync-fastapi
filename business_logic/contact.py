from fastapi import APIRouter,status, HTTPException
from schemas import CreateContact
from business_logic.email import send_html_email
from database import contact_collection


router = APIRouter()


@router.post("/add_contact", status_code=status.HTTP_201_CREATED)
async def add_contact(contact: CreateContact):
    try:
        contact_collection.insert_one(contact.model_dump())

        if contact.contact_us_by == "contact":
            user_template = "contact_us_thankyou.html"
            support_template = "contact_us_backoffice.html"
        elif contact.contact_us_by == "demo":
            user_template = "schedule_demo_thankyou.html"
            support_template = "schedule_demo_backoffice.html"
        else:
            user_template = "default.html"
            support_template = "default.html" 

        send_html_email(
            subject=f"Your {contact.contact_us_by} info was submitted successfully",
            recipient=contact.email,
            template_name=user_template,
            context={"first_name": contact.first_name.capitalize()}
        )

        send_html_email(
            subject=f"New {contact.contact_us_by.capitalize()} Submission",
            recipient="support@selfsync.ai",
            template_name=support_template,
            context={
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "email": contact.email,
                "contact_us_by": contact.contact_us_by,
                "mobile": contact.mobile
            }
        )
        
        return {"message": "Your data has been successfully submitted."}
    
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while submitting your data>> {str(ex)}")
    