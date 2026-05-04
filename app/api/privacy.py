from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.block import BlockedUser
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/privacy", tags=["Privacy & Blocking"])

@router.post("/block/{profile_id}")
async def block_user(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Block another user"""
    
    # Get current user's profile
    current_profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not current_profile:
        raise HTTPException(status_code=404, detail="Your profile not found")
    
    # Check if target profile exists
    try:
        target_uuid = uuid.UUID(profile_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid profile ID")
    
    target_profile = db.query(Profile).filter(Profile.id == target_uuid).first()
    if not target_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Cannot block self
    if current_profile.id == target_uuid:
        raise HTTPException(status_code=400, detail="Cannot block yourself")
    
    # Check if already blocked
    existing_block = db.query(BlockedUser).filter(
        BlockedUser.blocker_id == current_profile.id,
        BlockedUser.blocked_id == target_uuid
    ).first()
    
    if existing_block:
        raise HTTPException(status_code=400, detail="User already blocked")
    
    # Create block
    block = BlockedUser(
        blocker_id=current_profile.id,
        blocked_id=target_uuid
    )
    db.add(block)
    db.commit()
    
    return {"message": f"User {target_profile.name} blocked successfully"}

@router.delete("/unblock/{profile_id}")
async def unblock_user(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unblock a user"""
    
    # Get current user's profile
    current_profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not current_profile:
        raise HTTPException(status_code=404, detail="Your profile not found")
    
    try:
        target_uuid = uuid.UUID(profile_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid profile ID")
    
    # Find and delete block
    block = db.query(BlockedUser).filter(
        BlockedUser.blocker_id == current_profile.id,
        BlockedUser.blocked_id == target_uuid
    ).first()
    
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    
    db.delete(block)
    db.commit()
    
    return {"message": "User unblocked successfully"}

@router.get("/blocked")
async def get_blocked_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of blocked users"""
    
    # Get current user's profile
    current_profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not current_profile:
        raise HTTPException(status_code=404, detail="Your profile not found")
    
    # Get all blocked users
    blocks = db.query(BlockedUser).filter(BlockedUser.blocker_id == current_profile.id).all()
    
    results = []
    for block in blocks:
        blocked_profile = db.query(Profile).filter(Profile.id == block.blocked_id).first()
        if blocked_profile:
            results.append({
                "profile_id": str(blocked_profile.id),
                "name": blocked_profile.name,
                "blocked_at": block.created_at
            })
    
    return {"total": len(results), "blocked_users": results}