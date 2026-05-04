from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./matrimony.db"
    
    # JWT
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # AWS
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_BUCKET_NAME: str = "matrimony-photos"
    AWS_REGION: str = "ap-south-1"
    
    # Twilio
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    
    # Email SMTP
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""  # Added this
    EMAIL_ENABLED: bool = False  # Added this
    
    # App Settings
    APP_NAME: str = "Matrimony App"
    DEBUG: bool = True
    OTP_EXPIRY_MINUTES: int = 5
    MAX_PHOTO_SIZE_MB: int = 5
    
    # Feature Toggles
    SMS_ENABLED: bool = False  # Added this
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # This allows extra fields in .env

settings = Settings()