import asyncio
import logging
from fastapi import APIRouter, HTTPException
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os, re
from dotenv import load_dotenv

router = APIRouter()

load_dotenv()

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")

def send_email(to_email: str, subject: str, message: str):
    try:
        msg = MIMEMultipart()
        msg["From"] = DEFAULT_FROM_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "html")) 

        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()  
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)  
        server.sendmail(EMAIL_HOST_USER, to_email, msg.as_string())  
        server.quit()

        return True
    except Exception as e:
        return False


BASE_DIR = Path(__file__).resolve().parent.parent
templates_path = BASE_DIR / "templates"