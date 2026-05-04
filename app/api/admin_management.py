from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.admin import AdminUser
from app.middleware.auth import get_current_user
from app.middleware.rbac import require_role
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/admin-management", tags=["Admin Management"])

class CreateAdminRequest(BaseModel):
    email: EmailStr
    role: str  # admin, moderator, viewer

@router.post("/create-admin")
@require_role(["super_admin"])
async def create_admin(
    request: CreateAdminRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create regular admin (Super Admin only)"""
    
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already admin
    existing_admin = db.query(AdminUser).filter(AdminUser.user_id == user.id).first()
    if existing_admin:
        raise HTTPException(status_code=400, detail="User is already an admin")
    
    # Create admin
    admin = AdminUser(
        user_id=user.id,
        role=request.role,
        created_by=current_user.id,
        is_active=True
    )
    db.add(admin)
    
    # Update user role
    user.role = request.role
    db.commit()
    
    return {"message": f"User {user.email} promoted to {request.role}"}

@router.get("/admins")
@require_role(["super_admin"])
async def get_all_admins(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all admin users"""
    
    admins = db.query(AdminUser).filter(AdminUser.is_active == True).all()
    
    results = []
    for admin in admins:
        user = db.query(User).filter(User.id == admin.user_id).first()
        results.append({
            "email": user.email if user else "Unknown",
            "role": admin.role,
            "created_at": admin.created_at
        })
    
    return {"admins": results}