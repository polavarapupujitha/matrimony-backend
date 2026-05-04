from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List
import uuid
from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.interest import Interest
from app.models.admin import AdminUser, ModerationQueue, Report, AdminActionLog
from app.middleware.auth import get_current_user
from app.middleware.rbac import require_role, require_permission
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/admin", tags=["Admin Panel"])

# ========== Schemas ==========
class UpdateUserStatusRequest(BaseModel):
    is_active: bool
    reason: Optional[str] = None

class ModeratePhotoRequest(BaseModel):
    status: str  # approved, rejected
    notes: Optional[str] = None

class ResolveReportRequest(BaseModel):
    status: str  # resolved, rejected
    notes: str

# ========== User Management APIs ==========
@router.get("/users")
@require_role(["super_admin", "admin", "viewer"])
async def get_all_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all users with filters"""
    
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if search:
        query = query.filter(
            (User.email.contains(search)) | 
            (User.mobile.contains(search))
        )
    
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    results = []
    for user in users:
        profile = db.query(Profile).filter(Profile.user_id == user.id).first()
        results.append({
            "id": str(user.id),
            "email": user.email,
            "mobile": user.mobile,
            "role": user.role,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "name": profile.name if profile else None,
            "gender": profile.gender if profile else None,
            "city": profile.city if profile else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
        })
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "users": results
    }

@router.get("/users/{user_id}")
@require_role(["super_admin", "admin"])
async def get_user_details(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed user information"""
    
    try:
        user_uuid = uuid.UUID(user_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    
    # Get statistics
    sent_interests = db.query(Interest).filter(Interest.from_profile_id == profile.id).count() if profile else 0
    received_interests = db.query(Interest).filter(Interest.to_profile_id == profile.id).count() if profile else 0
    
    return {
        "id": str(user.id),
        "email": user.email,
        "mobile": user.mobile,
        "role": user.role,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at,
        "last_login": user.last_login,
        "profile": {
            "id": str(profile.id) if profile else None,
            "name": profile.name if profile else None,
            "gender": profile.gender if profile else None,
            "dob": profile.dob.isoformat() if profile and profile.dob else None,
            "religion": profile.religion if profile else None,
            "mother_tongue": profile.mother_tongue if profile else None,
            "marital_status": profile.marital_status if profile else None,
            "height": profile.height if profile else None,
            "city": profile.city if profile else None,
            "about_me": profile.about_me if profile else None,
            "highest_education": profile.highest_education if profile else None,
            "employment_status": profile.employment_status if profile else None,
            "annual_income": profile.annual_income if profile else None,
            "profile_completeness": profile.profile_completeness if profile else 0
        } if profile else None,
        "statistics": {
            "sent_interests": sent_interests,
            "received_interests": received_interests
        }
    }

@router.put("/users/{user_id}/status")
@require_permission("manage_users")
async def update_user_status(
    user_id: str,
    request: UpdateUserStatusRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activate or deactivate user account"""
    
    try:
        user_uuid = uuid.UUID(user_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Cannot modify own status
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own status")
    
    # Cannot modify super admin if not super admin
    if user.role == "super_admin" and current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Cannot modify super admin")
    
    old_status = user.is_active
    user.is_active = request.is_active
    db.commit()
    
    # Log action
    admin = db.query(AdminUser).filter(AdminUser.user_id == current_user.id).first()
    if admin:
        log = AdminActionLog(
            id=uuid.uuid4(),
            admin_id=admin.id,
            action="user_status_change",
            target_type="user",
            target_id=user.id,
            details={
                "old_status": old_status,
                "new_status": request.is_active,
                "reason": request.reason,
                "target_email": user.email
            }
        )
        db.add(log)
        db.commit()
    
    return {
        "message": f"User {'activated' if request.is_active else 'suspended'} successfully",
        "user_id": str(user.id),
        "email": user.email,
        "is_active": user.is_active
    }

# ========== Moderation APIs ==========
@router.get("/moderation/queue")
@require_role(["super_admin", "admin", "moderator"])
async def get_moderation_queue(
    status: Optional[str] = Query("pending"),
    target_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get items awaiting moderation"""
    
    query = db.query(ModerationQueue)
    
    if status:
        query = query.filter(ModerationQueue.status == status)
    if target_type:
        query = query.filter(ModerationQueue.target_type == target_type)
    
    total = query.count()
    items = query.order_by(ModerationQueue.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    results = []
    for item in items:
        target_name = None
        target_user = None
        
        if item.target_type == "profile":
            profile = db.query(Profile).filter(Profile.id == item.target_id).first()
            if profile:
                target_name = profile.name
                user = db.query(User).filter(User.id == profile.user_id).first()
                target_user = user.email if user else None
        
        reporter = db.query(User).filter(User.id == item.reported_by).first() if item.reported_by else None
        reporter_profile = db.query(Profile).filter(Profile.user_id == reporter.id).first() if reporter else None
        
        results.append({
            "id": str(item.id),
            "target_type": item.target_type,
            "target_id": str(item.target_id),
            "target_name": target_name,
            "target_user": target_user,
            "reason": item.reason,
            "reported_by": reporter_profile.name if reporter_profile else None,
            "status": item.status,
            "created_at": item.created_at,
            "review_notes": item.review_notes
        })
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "queue": results
    }

@router.post("/moderation/{item_id}/review")
@require_role(["super_admin", "admin", "moderator"])
async def review_moderation_item(
    item_id: str,
    request: ModeratePhotoRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Review and resolve moderation item"""
    
    try:
        item_uuid = uuid.UUID(item_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid item ID")
    
    queue_item = db.query(ModerationQueue).filter(
        ModerationQueue.id == item_uuid,
        ModerationQueue.status == "pending"
    ).first()
    
    if not queue_item:
        raise HTTPException(status_code=404, detail="Moderation item not found")
    
    queue_item.status = request.status
    queue_item.review_notes = request.notes
    queue_item.resolved_at = datetime.utcnow()
    
    # Get admin user
    admin = db.query(AdminUser).filter(AdminUser.user_id == current_user.id).first()
    if admin:
        queue_item.reviewed_by = admin.id
    
    db.commit()
    
    return {
        "message": f"Item {request.status}",
        "item_id": item_id,
        "status": request.status
    }

# ========== Report Management APIs ==========
@router.get("/reports")
@require_role(["super_admin", "admin", "viewer"])
async def get_reports(
    status: Optional[str] = Query("pending"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user reports"""
    
    query = db.query(Report).filter(Report.status == status)
    
    total = query.count()
    reports = query.order_by(Report.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    results = []
    for report in reports:
        reporter = db.query(User).filter(User.id == report.reporter_id).first()
        reported = db.query(User).filter(User.id == report.reported_id).first()
        reporter_profile = db.query(Profile).filter(Profile.user_id == report.reporter_id).first()
        reported_profile = db.query(Profile).filter(Profile.user_id == report.reported_id).first()
        
        results.append({
            "id": str(report.id),
            "reporter": {
                "id": str(report.reporter_id),
                "name": reporter_profile.name if reporter_profile else "Unknown",
                "email": reporter.email if reporter else "Unknown"
            },
            "reported": {
                "id": str(report.reported_id),
                "name": reported_profile.name if reported_profile else "Unknown",
                "email": reported.email if reported else "Unknown"
            },
            "reason": report.reason,
            "description": report.description,
            "screenshot_urls": report.screenshot_urls,
            "status": report.status,
            "created_at": report.created_at,
            "resolution_notes": report.resolution_notes
        })
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "reports": results
    }

@router.post("/reports/{report_id}/resolve")
@require_role(["super_admin", "admin"])
async def resolve_report(
    report_id: str,
    request: ResolveReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resolve a user report"""
    
    try:
        report_uuid = uuid.UUID(report_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid report ID")
    
    report = db.query(Report).filter(Report.id == report_uuid).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report.status = request.status
    report.resolution_notes = request.notes
    report.resolved_at = datetime.utcnow()
    
    # Get admin user
    admin = db.query(AdminUser).filter(AdminUser.user_id == current_user.id).first()
    if admin:
        report.resolved_by = admin.id
    
    db.commit()
    
    return {
        "message": f"Report {request.status}",
        "report_id": report_id,
        "status": request.status
    }

# ========== Dashboard & Analytics APIs ==========
@router.get("/dashboard")
@require_role(["super_admin", "admin", "viewer"])
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics"""
    
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    verified_users = db.query(User).filter(User.is_verified == True).count()
    total_profiles = db.query(Profile).count()
    complete_profiles = db.query(Profile).filter(Profile.profile_completeness >= 80).count()
    
    pending_moderations = db.query(ModerationQueue).filter(ModerationQueue.status == "pending").count()
    pending_reports = db.query(Report).filter(Report.status == "pending").count()
    
    total_interests = db.query(Interest).count()
    accepted_interests = db.query(Interest).filter(Interest.status == "accepted").count()
    
    # Recent users (last 7 days)
    from datetime import timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users_last_week = db.query(User).filter(User.created_at >= week_ago).count()
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "verified": verified_users,
            "new_last_7_days": new_users_last_week
        },
        "profiles": {
            "total": total_profiles,
            "complete": complete_profiles,
            "completion_rate": round((complete_profiles / total_profiles * 100) if total_profiles > 0 else 0, 2)
        },
        "moderation": {
            "pending": pending_moderations,
            "reports": pending_reports
        },
        "interests": {
            "total": total_interests,
            "accepted": accepted_interests,
            "acceptance_rate": round((accepted_interests / total_interests * 100) if total_interests > 0 else 0, 2)
        }
    }

@router.get("/activity-logs")
@require_role(["super_admin", "admin"])
async def get_activity_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    action: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get admin activity logs"""
    
    query = db.query(AdminActionLog).order_by(AdminActionLog.created_at.desc())
    
    if action:
        query = query.filter(AdminActionLog.action == action)
    
    total = query.count()
    logs = query.offset((page - 1) * limit).limit(limit).all()
    
    results = []
    for log in logs:
        admin = db.query(AdminUser).filter(AdminUser.id == log.admin_id).first()
        admin_user = db.query(User).filter(User.id == admin.user_id).first() if admin else None
        
        results.append({
            "id": str(log.id),
            "admin": admin_user.email if admin_user else "Unknown",
            "admin_role": admin.role if admin else "Unknown",
            "action": log.action,
            "target_type": log.target_type,
            "target_id": str(log.target_id) if log.target_id else None,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at
        })
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "logs": results
    }