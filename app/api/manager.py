from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import uuid
import secrets
from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.manager import ProfileManager, ManagerInvitation, ManagerActivityLog
from app.middleware.auth import get_current_user
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/manager", tags=["Parental Login"])

class InviteManagerRequest(BaseModel):
    email: EmailStr
    relationship_type: str
    permission_level: str = "limited"

class UpdatePermissionsRequest(BaseModel):
    can_edit_basic: Optional[bool] = None
    can_edit_family: Optional[bool] = None
    can_send_interest: Optional[bool] = None
    can_accept_interest: Optional[bool] = None
    daily_interest_limit: Optional[int] = None

@router.post("/invite")
async def invite_manager(
    request: InviteManagerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    existing_user = db.query(User).filter(User.email == request.email).first()
    
    if existing_user:
        existing_manager = db.query(ProfileManager).filter(
            ProfileManager.profile_id == profile.id,
            ProfileManager.manager_user_id == existing_user.id,
            ProfileManager.is_active == True
        ).first()
        if existing_manager:
            raise HTTPException(status_code=400, detail="User is already a manager")
    
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=7)
    
    invitation = ManagerInvitation(
        profile_id=profile.id,
        manager_email=request.email,
        relationship_type=request.relationship_type,
        permission_level=request.permission_level,
        token=token,
        expires_at=expires_at
    )
    db.add(invitation)
    db.commit()
    
    accept_url = f"http://localhost:8000/manager/accept/{token}"
    
    return {
        "message": "Invitation sent successfully",
        "token": token,
        "accept_url": accept_url,
        "expires_at": expires_at
    }

@router.post("/accept/{token}")
async def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    invitation = db.query(ManagerInvitation).filter(
        ManagerInvitation.token == token,
        ManagerInvitation.status == "pending",
        ManagerInvitation.expires_at > datetime.utcnow()
    ).first()
    
    if not invitation:
        raise HTTPException(status_code=400, detail="Invalid or expired invitation")
    
    if current_user.email != invitation.manager_email:
        raise HTTPException(status_code=400, detail="Invitation email does not match your account")
    
    profile = db.query(Profile).filter(Profile.id == invitation.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    manager = ProfileManager(
        profile_id=profile.id,
        manager_user_id=current_user.id,
        relationship_type=invitation.relationship_type,
        permission_level=invitation.permission_level,
        can_edit_basic=invitation.permission_level == "full",
        can_edit_family=True,
        can_send_interest=True,
        can_accept_interest=True,
        daily_interest_limit=10
    )
    db.add(manager)
    
    invitation.status = "accepted"
    db.commit()
    
    return {"message": f"You are now a manager for {profile.name}", "relationship_type": invitation.relationship_type}

@router.get("/profiles")
async def get_managed_profiles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    managers = db.query(ProfileManager).filter(
        ProfileManager.manager_user_id == current_user.id,
        ProfileManager.is_active == True
    ).all()
    
    results = []
    for manager in managers:
        profile = manager.profile
        results.append({
            "profile_id": str(profile.id),
            "name": profile.name,
            "relationship_type": manager.relationship_type,
            "permission_level": manager.permission_level,
            "can_edit_basic": manager.can_edit_basic,
            "can_send_interest": manager.can_send_interest,
            "daily_interest_limit": manager.daily_interest_limit
        })
    
    return {"total": len(results), "profiles": results}

@router.get("/pending-invitations")
async def get_pending_invitations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    invitations = db.query(ManagerInvitation).filter(
        ManagerInvitation.manager_email == current_user.email,
        ManagerInvitation.status == "pending",
        ManagerInvitation.expires_at > datetime.utcnow()
    ).all()
    
    results = []
    for inv in invitations:
        profile = db.query(Profile).filter(Profile.id == inv.profile_id).first()
        results.append({
            "token": inv.token,
            "profile_name": profile.name if profile else "Unknown",
            "relationship_type": inv.relationship_type,
            "permission_level": inv.permission_level,
            "expires_at": inv.expires_at
        })
    
    return {"total": len(results), "invitations": results}

@router.put("/{manager_id}/permissions")
async def update_manager_permissions(
    manager_id: str,
    request: UpdatePermissionsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        manager_uuid = uuid.UUID(manager_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid manager ID")
    
    manager = db.query(ProfileManager).filter(ProfileManager.id == manager_uuid).first()
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    
    profile = db.query(Profile).filter(Profile.id == manager.profile_id).first()
    if profile.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only profile owner can update permissions")
    
    for field, value in request.dict(exclude_unset=True).items():
        setattr(manager, field, value)
    
    db.commit()
    
    return {"message": "Permissions updated successfully"}

@router.delete("/{manager_id}")
async def remove_manager(
    manager_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        manager_uuid = uuid.UUID(manager_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid manager ID")
    
    manager = db.query(ProfileManager).filter(ProfileManager.id == manager_uuid).first()
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    
    profile = db.query(Profile).filter(Profile.id == manager.profile_id).first()
    if profile.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only profile owner can remove managers")
    
    manager.is_active = False
    db.commit()
    
    return {"message": "Manager removed successfully"}

@router.post("/switch/{profile_id}")
async def switch_profile(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        profile_uuid = uuid.UUID(profile_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid profile ID")
    
    manager = db.query(ProfileManager).filter(
        ProfileManager.profile_id == profile_uuid,
        ProfileManager.manager_user_id == current_user.id,
        ProfileManager.is_active == True
    ).first()
    
    if not manager:
        raise HTTPException(status_code=403, detail="You don't have access to this profile")
    
    from app.utils.jwt_handler import create_access_token
    
    token_data = {
        "sub": str(current_user.id),
        "profile_id": profile_id,
        "role": "manager",
        "relationship_type": manager.relationship_type
    }
    access_token = create_access_token(token_data)
    
    return {
        "access_token": access_token,
        "profile_id": profile_id,
        "relationship_type": manager.relationship_type,
        "permissions": {
            "can_edit_basic": manager.can_edit_basic,
            "can_send_interest": manager.can_send_interest
        }
    }