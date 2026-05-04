from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models.profile import Profile
from app.models.user import User
from app.middleware.auth import get_current_user
from pydantic import BaseModel, Field
from datetime import date

router = APIRouter(prefix="/profile", tags=["Profile"])

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[date] = None
    religion: Optional[str] = None
    mother_tongue: Optional[str] = None
    marital_status: Optional[str] = None
    height: Optional[int] = None
    city: Optional[str] = None
    about_me: Optional[str] = None
    highest_education: Optional[str] = None
    employment_status: Optional[str] = None
    annual_income: Optional[str] = None
    diet: Optional[str] = None

@router.get("/me")
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile"""
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return {
        "id": str(profile.id),
        "user_id": str(profile.user_id),
        "name": profile.name,
        "gender": profile.gender,
        "dob": profile.dob,
        "age": calculate_age(profile.dob) if profile.dob else None,
        "religion": profile.religion,
        "mother_tongue": profile.mother_tongue,
        "marital_status": profile.marital_status,
        "height": profile.height,
        "city": profile.city,
        "about_me": profile.about_me,
        "highest_education": profile.highest_education,
        "employment_status": profile.employment_status,
        "annual_income": profile.annual_income,
        "diet": profile.diet,
        "profile_completeness": profile.profile_completeness
    }

@router.put("/me")
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Update fields
    for field, value in profile_data.dict(exclude_unset=True).items():
        setattr(profile, field, value)
    
    # Update completeness
    completeness = calculate_completeness(profile)
    profile.profile_completeness = completeness
    profile.last_active = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Profile updated", "completeness": completeness}

def calculate_age(dob):
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def calculate_completeness(profile):
    fields = [
        profile.name, profile.gender, profile.dob, profile.religion,
        profile.mother_tongue, profile.marital_status, profile.height,
        profile.city, profile.highest_education, profile.employment_status
    ]
    completed = sum(1 for f in fields if f)
    return int((completed / len(fields)) * 100)