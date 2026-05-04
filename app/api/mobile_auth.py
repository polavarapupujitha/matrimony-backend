from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import random
import os
from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.utils.jwt_handler import create_access_token, create_refresh_token
from pydantic import BaseModel, Field
import re

router = APIRouter(prefix="/mobile-auth", tags=["Mobile Authentication"])

class MobileRequest(BaseModel):
    mobile: str = Field(..., pattern=r'^[6-9]\d{9}$')

class VerifyOTPRequest(BaseModel):
    mobile: str = Field(..., pattern=r'^[6-9]\d{9}$')
    otp: str = Field(..., min_length=6, max_length=6)
    name: str = Field(..., min_length=2, max_length=100)

# In-memory OTP storage (for development)
otp_storage = {}

def generate_otp() -> str:
    return str(random.randint(100000, 999999))

def send_otp_sms(mobile: str, otp: str):
    print(f"📱 [DEV MODE] OTP for {mobile}: {otp}")
    return True

@router.post("/send-otp")
async def send_otp(
    request: MobileRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(User.mobile == request.mobile).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Mobile number already registered")
    
    otp = generate_otp()
    otp_storage[request.mobile] = {
        "otp": otp,
        "expires_at": datetime.now().timestamp() + 300
    }
    
    background_tasks.add_task(send_otp_sms, request.mobile, otp)
    
    return {
        "message": "OTP sent successfully",
        "mobile": request.mobile,
        "expires_in": 300
    }

@router.post("/verify-otp")
async def verify_otp_register(
    request: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    stored_data = otp_storage.get(request.mobile)
    if not stored_data:
        raise HTTPException(status_code=400, detail="OTP not found or expired")
    
    if datetime.now().timestamp() > stored_data["expires_at"]:
        del otp_storage[request.mobile]
        raise HTTPException(status_code=400, detail="OTP expired")
    
    if stored_data["otp"] != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    existing_user = db.query(User).filter(User.mobile == request.mobile).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Mobile number already registered")
    
    user = User(
        id=uuid.uuid4(),
        mobile=request.mobile,
        role="user",
        is_verified=True,
        is_active=True
    )
    db.add(user)
    db.flush()
    
    profile = Profile(
        id=uuid.uuid4(),
        user_id=user.id,
        name=request.name,
        profile_completeness=0
    )
    db.add(profile)
    db.commit()
    
    del otp_storage[request.mobile]
    
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user_id": str(user.id),
        "role": user.role,
        "message": "Registration successful"
    }

@router.post("/login-otp")
async def login_with_otp(
    request: MobileRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.mobile == request.mobile).first()
    if not user:
        raise HTTPException(status_code=404, detail="Mobile number not registered")
    
    otp = generate_otp()
    otp_storage[f"login_{request.mobile}"] = {
        "otp": otp,
        "expires_at": datetime.now().timestamp() + 300,
        "user_id": str(user.id)
    }
    
    background_tasks.add_task(send_otp_sms, request.mobile, otp)
    
    return {
        "message": "Login OTP sent successfully",
        "mobile": request.mobile,
        "expires_in": 300
    }

@router.post("/verify-login-otp")
async def verify_login_otp(
    request: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    stored_data = otp_storage.get(f"login_{request.mobile}")
    if not stored_data:
        raise HTTPException(status_code=400, detail="OTP not found or expired")
    
    if datetime.now().timestamp() > stored_data["expires_at"]:
        del otp_storage[f"login_{request.mobile}"]
        raise HTTPException(status_code=400, detail="OTP expired")
    
    if stored_data["otp"] != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    user = db.query(User).filter(User.mobile == request.mobile).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.last_login = datetime.utcnow()
    db.commit()
    
    del otp_storage[f"login_{request.mobile}"]
    
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user_id": str(user.id),
        "role": user.role,
        "message": "Login successful"
    }