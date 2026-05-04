from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import uuid
import os
import shutil
from datetime import datetime
from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.photo import Photo
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/photo", tags=["Photo Upload"])

# Create upload directory if not exists
UPLOAD_DIR = "uploads/photos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

@router.post("/upload")
async def upload_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload profile photo"""
    
    # Get user's profile
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Validate file type
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    filename = f"{profile.id}_{timestamp}_{unique_id}{file_extension}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Check if this is the first photo
    existing_photos_count = db.query(Photo).filter(Photo.profile_id == profile.id).count()
    is_primary = existing_photos_count == 0
    
    # Save to database
    photo = Photo(
        id=uuid.uuid4(),
        profile_id=profile.id,
        url=f"/uploads/photos/{filename}",
        is_primary=is_primary,
        is_verified=False
    )
    db.add(photo)
    db.commit()
    
    return {
        "message": "Photo uploaded successfully",
        "photo_id": str(photo.id),
        "url": photo.url,
        "is_primary": is_primary
    }

@router.get("/my-photos")
async def get_my_photos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all photos of current user"""
    
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    photos = db.query(Photo).filter(Photo.profile_id == profile.id).all()
    
    return {
        "photos": [
            {
                "id": str(p.id),
                "url": p.url,
                "is_primary": p.is_primary,
                "is_verified": p.is_verified
            }
            for p in photos
        ]
    }

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
    """Delete a photo"""
    
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
    
    # Delete file from disk
    file_path = os.path.join(UPLOAD_DIR, os.path.basename(photo.url))
    if os.path.exists(file_path):
        os.remove(file_path)
    
    db.delete(photo)
    db.commit()
    
    return {"message": "Photo deleted successfully"}