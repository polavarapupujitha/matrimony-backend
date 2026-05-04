from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import uuid
from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.interest import Interest
from app.middleware.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/interest", tags=["Interest"])

class SendInterestRequest(BaseModel):
    message: Optional[str] = None

@router.post("/send/{profile_id}")
async def send_interest(
    profile_id: str,
    request: SendInterestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get current user's profile
    current_profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not current_profile:
        raise HTTPException(status_code=404, detail="Your profile not found")
    
    # Convert profile_id string to UUID
    try:
        target_uuid = uuid.UUID(profile_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid profile ID format")
    
    # Check if target profile exists
    target_profile = db.query(Profile).filter(Profile.id == target_uuid).first()
    if not target_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Cannot send interest to self
    if current_profile.id == target_uuid:
        raise HTTPException(status_code=400, detail="Cannot send interest to yourself")
    
    # Check if interest already exists
    existing = db.query(Interest).filter(
        ((Interest.from_profile_id == current_profile.id) & (Interest.to_profile_id == target_uuid)) |
        ((Interest.from_profile_id == target_uuid) & (Interest.to_profile_id == current_profile.id))
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Interest already sent or received")
    
    # Create interest
    interest = Interest(
        id=uuid.uuid4(),
        from_profile_id=current_profile.id,
        to_profile_id=target_uuid,
        message=request.message,
        status="pending"
    )
    db.add(interest)
    db.commit()
    db.refresh(interest)
    
    return {
        "message": "Interest sent successfully",
        "interest_id": str(interest.id),
        "to_profile": target_profile.name
    }

@router.get("/received")
async def get_received_interests(
    current_user: User = Depends(get_current_user),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    current_profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not current_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    query = db.query(Interest).filter(Interest.to_profile_id == current_profile.id)
    
    if status:
        query = query.filter(Interest.status == status)
    
    interests = query.order_by(Interest.created_at.desc()).all()
    
    results = []
    for interest in interests:
        from_profile = interest.from_profile
        results.append({
            "id": str(interest.id),
            "from_profile": {
                "id": str(from_profile.id),
                "name": from_profile.name,
                "gender": from_profile.gender,
                "city": from_profile.city
            },
            "message": interest.message,
            "status": interest.status,
            "created_at": interest.created_at
        })
    
    return {"total": len(results), "results": results}

@router.get("/sent")
async def get_sent_interests(
    current_user: User = Depends(get_current_user),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    current_profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not current_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    query = db.query(Interest).filter(Interest.from_profile_id == current_profile.id)
    
    if status:
        query = query.filter(Interest.status == status)
    
    interests = query.order_by(Interest.created_at.desc()).all()
    
    results = []
    for interest in interests:
        to_profile = interest.to_profile
        results.append({
            "id": str(interest.id),
            "to_profile": {
                "id": str(to_profile.id),
                "name": to_profile.name,
                "gender": to_profile.gender,
                "city": to_profile.city
            },
            "message": interest.message,
            "status": interest.status,
            "created_at": interest.created_at
        })
    
    return {"total": len(results), "results": results}

@router.put("/{interest_id}/accept")
async def accept_interest(
    interest_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not current_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    try:
        interest_uuid = uuid.UUID(interest_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid interest ID")
    
    interest = db.query(Interest).filter(
        Interest.id == interest_uuid,
        Interest.to_profile_id == current_profile.id,
        Interest.status == "pending"
    ).first()
    
    if not interest:
        raise HTTPException(status_code=404, detail="Interest not found")
    
    interest.status = "accepted"
    interest.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Interest accepted", "mutual_match": False}

@router.put("/{interest_id}/decline")
async def decline_interest(
    interest_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not current_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    try:
        interest_uuid = uuid.UUID(interest_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid interest ID")
    
    interest = db.query(Interest).filter(
        Interest.id == interest_uuid,
        Interest.to_profile_id == current_profile.id,
        Interest.status == "pending"
    ).first()
    
    if not interest:
        raise HTTPException(status_code=404, detail="Interest not found")
    
    interest.status = "declined"
    interest.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Interest declined"}