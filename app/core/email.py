import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

def send_registration_approved_email(email, full_name):
    """Отправить письмо об одобрении регистрации"""
    # Здесь логика отправки письма
    pass

def send_registration_rejected_email(email, full_name):
    """Отправить письмо об отклонении регистрации"""
    pass