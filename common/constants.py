from dotenv import load_dotenv
import os
load_dotenv()


# JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "2b12PMeu6WtkGehQNX2OUaF1e1lbkePgdxhowD47XqlaUvnKIJ37fZu")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))  # 1440 minutes means 24 hours (1 day)

# Candidate status 
CANDIDATE_STATUS = {
    "otp_sent":"1",
    "otp_verified":"2",
    "manager_selected":"3",
    "page_visited":"4",
    "exam_started":"5",
    "exam_finished":"6",
    "incomplete_exam":"7"
}

# RESEND CANDIDATE OTP
OTP_RESEND_BLOCKED_MINUTES = 10
OTP_RESEND_MAX_COUNT = 5
MAX_OTP_WRONG_ATTEMPTS = 3
OTP_WRONG_ATTEMPTS_BLOCKED_MINUTES = 30
