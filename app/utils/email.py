import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

# Email configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "False") == "True"

async def send_email(to_email: str, subject: str, body: str, is_html: bool = False) -> bool:
    """Send email using SMTP"""
    
    if not EMAIL_ENABLED:
        print(f"📧 [DEV MODE] Email to: {to_email}")
        print(f"   Subject: {subject}")
        print(f"   Body: {body}")
        return True
    
    if not SMTP_USER or not SMTP_PASSWORD:
        print("⚠️ Email credentials missing. Using dev mode.")
        print(f"📧 [DEV MODE] Email to: {to_email}")
        return True
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg["From"] = EMAIL_FROM
        msg["To"] = to_email
        msg["Subject"] = subject
        
        # Attach body
        if is_html:
            msg.attach(MIMEText(body, "html"))
        else:
            msg.attach(MIMEText(body, "plain"))
        
        # Send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Email sent to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False

async def send_password_reset_email(to_email: str, reset_token: str) -> bool:
    """Send password reset email with link"""
    
    reset_link = f"http://localhost:8000/auth/reset-password?token={reset_token}"
    
    subject = "Reset Your Matrimony App Password"
    
    body = f"""
    Hello,
    
    You requested to reset your password. Click the link below to set a new password:
    
    {reset_link}
    
    This link will expire in 1 hour.
    
    If you didn't request this, please ignore this email.
    
    Thanks,
    Matrimony App Team
    """
    
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2>Reset Your Password</h2>
        <p>You requested to reset your password. Click the button below:</p>
        <a href="{reset_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a>
        <p>Or copy this link: <a href="{reset_link}">{reset_link}</a></p>
        <p>This link expires in 1 hour.</p>
        <hr>
        <p style="color: gray;">Matrimony App Team</p>
    </body>
    </html>
    """
    
    return await send_email(to_email, subject, html_body, is_html=True)

async def send_verification_email(to_email: str, verification_token: str) -> bool:
    """Send email verification link"""
    
    verify_link = f"http://localhost:8000/auth/verify-email?token={verification_token}"
    
    subject = "Verify Your Matrimony App Email"
    
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2>Welcome to Matrimony App!</h2>
        <p>Please verify your email address by clicking the button below:</p>
        <a href="{verify_link}" style="background-color: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a>
        <p>Or copy this link: <a href="{verify_link}">{verify_link}</a></p>
        <hr>
        <p style="color: gray;">Matrimony App Team</p>
    </body>
    </html>
    """
    
    return await send_email(to_email, subject, html_body, is_html=True)