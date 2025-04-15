from fastapi import APIRouter
from pathlib import Path
import smtplib, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from jinja2 import Template
from typing import Dict


router = APIRouter()


load_dotenv()


EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")


def send_html_email(subject: str, recipient: str, template_name: str, context: Dict[str, str]):
    try:
        BASE_DIR = Path(__file__).resolve().parent.parent
        templates_path = BASE_DIR / "templates"
        template_file = templates_path / template_name

        # Load and render the HTML template with context
        html_template = Path(template_file).read_text(encoding="utf-8")
        template = Template(html_template)
        rendered_html = template.render(**context)

        # Create message container
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = DEFAULT_FROM_EMAIL
        msg['To'] = recipient

        # Attach HTML content
        msg.attach(MIMEText(rendered_html, 'html'))

        # Connect to SMTP server and send email
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            server.sendmail(DEFAULT_FROM_EMAIL, recipient, msg.as_string())

        return True
    except Exception as ex:
        return False

