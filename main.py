from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from business_logic.login import router as login_router
from business_logic.email import router as email_router
from business_logic.user import router as user_router
from business_logic.manager import router as manager_router
from business_logic.add_assessment import router as add_assessment_router
from business_logic.ip_data import router as ip_data_router
from business_logic.contact import router as contact_router
from assessment.add_candidate import router as add_candidate_router
from assessment.question_bank import router as question_bank_router
from assessment.position_role import router as position_role_router
from assessment.answer_paper import router as answer_paper_router
from business_logic.payment import router as payment_router



app = FastAPI()

# CORS Middleware (Adjust for production)
# app.add_middleware(
#    CORSMiddleware,
#    allow_origins=["http://localhost:3001"] ,
#    allow_credentials=True,
#    allow_methods=["*"],
#    allow_headers=["*"],
# )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# No more SQLAlchemy setup
# No Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(login_router, tags=["Login"])
app.include_router(email_router, tags=["Email"])
app.include_router(user_router, tags=["User"])
app.include_router(manager_router, tags=["Manager"])
app.include_router(add_assessment_router, tags=["add_assessment"])
app.include_router(ip_data_router, tags=["ip_data"])
app.include_router(contact_router, tags=["contact"])
app.include_router(add_candidate_router, tags=["add_candidate"])
app.include_router(question_bank_router, tags=["question_bank"])
app.include_router(position_role_router, tags=["position_role"])
app.include_router(answer_paper_router, tags=["answer_paper"])
app.include_router(payment_router, tags=["payment"])


