from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import uuid
from app.database import get_db
from app.models.user import User
from app.models.notification import Notification
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("/")
async def get_notifications(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    total = query.count()
    notifications = query.order_by(Notification.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    unread_count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    
    results = []
    for notif in notifications:
        results.append({
            "id": str(notif.id),
            "type": notif.type,
            "title": notif.title,
            "message": notif.message,
            "data": notif.data,
            "is_read": notif.is_read,
            "created_at": notif.created_at
        })
    
    return {
        "total": total,
        "unread_count": unread_count,
        "page": page,
        "limit": limit,
        "notifications": results
    }

@router.put("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        notif_uuid = uuid.UUID(notification_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid notification ID")
    
    notification = db.query(Notification).filter(
        Notification.id == notif_uuid,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    db.commit()
    
    return {"message": "Marked as read"}

@router.put("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    
    return {"message": "All notifications marked as read"}

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        notif_uuid = uuid.UUID(notification_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid notification ID")
    
    notification = db.query(Notification).filter(
        Notification.id == notif_uuid,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notification)
    db.commit()
    
    return {"message": "Notification deleted"}