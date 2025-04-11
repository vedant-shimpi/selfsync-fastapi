from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from business_logic.login import router as login_router
from business_logic.email import router as email_router
from business_logic.user import router as user_router
from business_logic.manager import router as manager_router

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
