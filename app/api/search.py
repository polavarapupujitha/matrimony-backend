from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.block import BlockedUser
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/profiles")
async def search_profiles(
    age_min: Optional[int] = Query(18, ge=18, le=60),
    age_max: Optional[int] = Query(60, ge=18, le=60),
    gender: Optional[str] = None,
    city: Optional[str] = None,
    religion: Optional[str] = None,
    mother_tongue: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search for other profiles (blocked users are excluded)"""
    
    # Get current user's profile
    current_profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not current_profile:
        raise HTTPException(status_code=404, detail="Your profile not found")
    
    # Get list of blocked users (users blocked by current user)
    blocked_subquery = db.query(BlockedUser.blocked_id).filter(
        BlockedUser.blocker_id == current_profile.id
    ).subquery()
    
    # Build query - exclude self and blocked users
    query = db.query(Profile).filter(
        Profile.id != current_profile.id,
        Profile.is_visible == True,
        Profile.id.notin_(blocked_subquery)
    )
    
    # Age filter (based on DOB)
    if age_min or age_max:
        today = date.today()
        if age_min:
            max_dob = date(today.year - age_min, today.month, today.day)
            query = query.filter(Profile.dob <= max_dob)
        if age_max:
            min_dob = date(today.year - age_max, today.month, today.day)
            query = query.filter(Profile.dob >= min_dob)
    
    # Gender filter
    if gender:
        query = query.filter(Profile.gender == gender)
    
    # City filter
    if city:
        query = query.filter(Profile.city == city)
    
    # Religion filter
    if religion:
        query = query.filter(Profile.religion == religion)
    
    # Mother tongue filter
    if mother_tongue:
        query = query.filter(Profile.mother_tongue == mother_tongue)
    
    # Get total count
    total = query.count()
    
    # Pagination
    profiles = query.offset((page - 1) * limit).limit(limit).all()
    
    # Prepare results
    results = []
    for profile in profiles:
        # Calculate age
        age = None
        if profile.dob:
            today = date.today()
            age = today.year - profile.dob.year - ((today.month, today.day) < (profile.dob.month, profile.dob.day))
        
        results.append({
            "id": str(profile.id),
            "name": profile.name,
            "age": age,
            "gender": profile.gender,
            "city": profile.city,
            "religion": profile.religion,
            "mother_tongue": profile.mother_tongue,
            "height": profile.height,
            "marital_status": profile.marital_status,
            "highest_education": profile.highest_education,
            "employment_status": profile.employment_status,
            "about_me": profile.about_me[:100] if profile.about_me else None,
            "profile_completeness": profile.profile_completeness,
            "last_active": profile.last_active
        })
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "results": results
    }

@router.get("/recent")
async def get_recent_profiles(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recently active profiles (excludes blocked users)"""
    
    # Get current user's profile
    current_profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not current_profile:
        raise HTTPException(status_code=404, detail="Your profile not found")
    
    # Get blocked users
    blocked_ids = db.query(BlockedUser.blocked_id).filter(
        BlockedUser.blocker_id == current_profile.id
    ).subquery()
    
    # Query recent profiles
    profiles = db.query(Profile).filter(
        Profile.id != current_profile.id,
        Profile.is_visible == True,
        Profile.id.notin_(blocked_ids)
    ).order_by(Profile.last_active.desc()).limit(limit).all()
    
    results = []
    for profile in profiles:
        results.append({
            "id": str(profile.id),
            "name": profile.name,
            "gender": profile.gender,
            "city": profile.city,
            "photo_url": profile.photos[0].url if profile.photos and len(profile.photos) > 0 else None,
            "last_active": profile.last_active
        })
    
    return {"total": len(results), "results": results}