from app.middleware.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.utils.password import hash_password, verify_password
from app.utils.jwt_handler import create_access_token, create_refresh_token
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: str
    role: str

@router.post("/register", response_model=LoginResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    print("=" * 50)
    print(f"📝 REGISTER ATTEMPT: {request.email}")
    
    # Check if user exists
    print("🔍 Checking if user already exists...")
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        print("❌ User already exists!")
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    print("👤 Creating new user...")
    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        role="user",
        is_verified=True
    )
    db.add(user)
    db.flush()
    print(f"✅ User created with ID: {user.id}")
    
    # Create profile
    print("📋 Creating profile for user...")
    try:
        profile = Profile(
            user_id=user.id,
            name=request.name,
            profile_completeness=0
        )
        db.add(profile)
        db.commit()
        db.refresh(user)
        print(f"✅ Profile created with ID: {profile.id}")
    except Exception as e:
        print(f"❌ Profile creation failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Profile creation failed: {str(e)}")
    
    # Create tokens
    print("🔑 Creating JWT tokens...")
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    print(f"✅ Registration successful for {request.email}")
    print("=" * 50)
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=str(user.id),
        role=user.role
    )

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    print("=" * 50)
    print(f"🔐 LOGIN ATTEMPT: {request.username}")
    
    user = db.query(User).filter(User.email == request.username).first()
    
    if not user:
        print("❌ User not found!")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(request.password, user.password_hash):
        print("❌ Invalid password!")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user.last_login = datetime.utcnow()
    db.commit()
    
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    print(f"✅ Login successful for {request.username}")
    print("=" * 50)
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=str(user.id),
        role=user.role
    )
@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout from current device"""
    from app.models.user import Session
    
    db.query(Session).filter(
        Session.user_id == current_user.id,
        Session.is_active == True
    ).update({"is_active": False})
    db.commit()
    
    return {"message": "Logged out successfully"}

@router.post("/logout/all")
async def logout_all_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout from all devices"""
    from app.models.user import Session
    
    db.query(Session).filter(
        Session.user_id == current_user.id
    ).update({"is_active": False})
    db.commit()
    
    return {"message": "Logged out from all devices successfully"}