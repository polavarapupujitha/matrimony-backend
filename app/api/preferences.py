from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.middleware.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/preferences", tags=["Partner Preferences"])

class PartnerPreferenceUpdate(BaseModel):
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    height_min: Optional[int] = None
    height_max: Optional[int] = None
    religion_preference: Optional[str] = None
    caste_preference: Optional[str] = None
    mother_tongue_preference: Optional[str] = None
    marital_status_preference: Optional[List[str]] = None
    diet_preference: Optional[str] = None
    education_minimum: Optional[str] = None
    income_minimum: Optional[str] = None
    location_preference: Optional[str] = None

@router.get("/")
async def get_partner_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get partner preferences"""
    
    from app.models.profile import PartnerPreference
    
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    preference = db.query(PartnerPreference).filter(
        PartnerPreference.profile_id == profile.id
    ).first()
    
    if not preference:
        return {
            "age_min": 18,
            "age_max": 60,
            "height_min": 120,
            "height_max": 220,
            "marital_status_preference": ["never_married"]
        }
    
    return {
        "age_min": preference.age_min,
        "age_max": preference.age_max,
        "height_min": preference.height_min,
        "height_max": preference.height_max,
        "religion_preference": preference.religion_preference,
        "caste_preference": preference.caste_preference,
        "mother_tongue_preference": preference.mother_tongue_preference,
        "marital_status_preference": preference.marital_status_preference,
        "diet_preference": preference.diet_preference,
        "education_minimum": preference.education_minimum,
        "income_minimum": preference.income_minimum,
        "location_preference": preference.location_preference
    }

@router.put("/")
async def update_partner_preferences(
    preferences: PartnerPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update partner preferences"""
    
    from app.models.profile import PartnerPreference as PartnerPreferenceModel
    
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    preference = db.query(PartnerPreferenceModel).filter(
        PartnerPreferenceModel.profile_id == profile.id
    ).first()
    
    if not preference:
        preference = PartnerPreferenceModel(profile_id=profile.id)
        db.add(preference)
    
    for field, value in preferences.dict(exclude_unset=True).items():
        setattr(preference, field, value)
    
    db.commit()
    
    return {"message": "Partner preferences updated successfully"}