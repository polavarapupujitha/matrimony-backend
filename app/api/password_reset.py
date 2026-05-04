from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app.models.user import User
from app.utils.password import hash_password
from app.utils.jwt_handler import create_access_token, decode_token
from app.utils.email import send_password_reset_email
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["Password Reset"])

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Request password reset link"""
    
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        return {"message": "If your email is registered, you will receive a reset link"}
    
    # Create reset token (valid for 1 hour)
    reset_token = create_access_token(
        {"sub": str(user.id), "reset": True},
        expires_delta=timedelta(hours=1)
    )
    
    # Send email
    background_tasks.add_task(send_password_reset_email, user.email, reset_token)
    
    return {"message": "Password reset link sent to your email"}

@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Reset password using token"""
    
    payload = decode_token(request.token)
    
    if not payload or not payload.get("reset"):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.password_hash = hash_password(request.new_password)
    db.commit()
    
    return {"message": "Password reset successfully. You can now login with your new password."}