from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.photo import Photo
from app.middleware.auth import get_current_user
from app.schemas.photo import PhotoURLRequest, PhotoResponse

router = APIRouter(prefix="/photo", tags=["Photo Upload"])

@router.post("/save-url")
async def save_photo_url(
    request: PhotoURLRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save photo URL from frontend (Supabase/Cloudinary URL)"""
    
    # Get user's profile
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Check if this is the first photo
    existing_photos_count = db.query(Photo).filter(Photo.profile_id == profile.id).count()
    is_primary = request.is_primary or existing_photos_count == 0
    
    # Save photo URL
    photo = Photo(
        id=uuid.uuid4(),
        profile_id=profile.id,
        url=request.url,
        is_primary=is_primary,
        is_verified=False
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    
    return {
        "message": "Photo URL saved successfully",
        "photo_id": str(photo.id),
        "url": photo.url,
        "is_primary": photo.is_primary
    }

@router.get("/my-photos", response_model=List[PhotoResponse])
async def get_my_photos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all photo URLs of current user"""
    
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    photos = db.query(Photo).filter(Photo.profile_id == profile.id).all()
    
    return [
        {
            "id": str(p.id),
            "url": p.url,
            "is_primary": p.is_primary,
            "is_verified": p.is_verified,
            "created_at": p.created_at.isoformat() if p.created_at else None
        }
        for p in photos
    ]

@router.put("/{photo_id}/make-primary")
async def make_primary(
    photo_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set a photo as primary"""
    
    try:
        photo_uuid = uuid.UUID(photo_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid photo ID")
    
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Check if photo exists
    photo = db.query(Photo).filter(Photo.id == photo_uuid, Photo.profile_id == profile.id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    # Remove primary from all photos
    db.query(Photo).filter(Photo.profile_id == profile.id).update({"is_primary": False})
    
    # Set this photo as primary
    photo.is_primary = True
    db.commit()
    
    return {"message": "Primary photo updated"}

@router.delete("/{photo_id}")
async def delete_photo(
    photo_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a photo URL"""
    
    try:
        photo_uuid = uuid.UUID(photo_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid photo ID")
    
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    photo = db.query(Photo).filter(Photo.id == photo_uuid, Photo.profile_id == profile.id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    db.delete(photo)
    db.commit()
    
    return {"message": "Photo deleted successfully"}