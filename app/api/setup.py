from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.admin import AdminUser
from app.utils.password import hash_password
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/setup", tags=["Setup"])

class CreateSuperAdminRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    secret_key: str

@router.post("/create-super-admin")
async def create_super_admin(
    request: CreateSuperAdminRequest,
    db: Session = Depends(get_db)
):
    """Create first super admin (Only once)"""
    
    # Check if super admin already exists
    existing_super_admin = db.query(AdminUser).filter(AdminUser.role == "super_admin").first()
    if existing_super_admin:
        raise HTTPException(status_code=400, detail="Super admin already exists")
    
    # Secret key check (for security)
    if request.secret_key != "MATRIMONY_SUPER_SECRET_2024":
        raise HTTPException(status_code=403, detail="Invalid secret key")
    
    # Check if user exists
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        # Create user
        user = User(
            email=request.email,
            password_hash=hash_password(request.password),
            role="super_admin",
            is_verified=True,
            is_active=True
        )
        db.add(user)
        db.flush()
        
        # Create profile
        from app.models.profile import Profile
        profile = Profile(
            user_id=user.id,
            name=request.name,
            profile_completeness=0
        )
        db.add(profile)
    
    # Create admin user entry
    admin_user = AdminUser(
        user_id=user.id,
        role="super_admin",
        is_active=True
    )
    db.add(admin_user)
    db.commit()
    
    return {
        "message": "Super admin created successfully",
        "email": user.email,
        "role": user.role
    }