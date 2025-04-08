from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from assessment.login import router as login_router
from database import engine, Base


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
    allow_origins=["*"],  # Change this to restrict origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(login_router)