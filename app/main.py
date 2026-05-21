from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import Base, engine
from app.api import auth, profile, search, interest, manager, admin, photo, password_reset, privacy, mobile_auth, setup, admin_management, notification, preferences

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Matrimony App API",
    description="Matrimony Application Backend with Authentication, Profile, Search, Interest, Parental Login, Admin Panel, Photo Upload, Password Reset, Privacy & Blocking, Mobile OTP, RBAC, Notifications & Partner Preferences",
    version="2.0.0"
)

# Serve static files (for uploaded photos)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== ALL ROUTERS ==========
app.include_router(auth.router)              # Email Authentication (Register, Login)
app.include_router(mobile_auth.router)       # Mobile Authentication (OTP)
app.include_router(profile.router)           # Profile APIs (Get, Update)
app.include_router(search.router)            # Search APIs (Find profiles)
app.include_router(interest.router)          # Interest APIs (Send, Accept, Decline)
app.include_router(manager.router)           # Parental Login APIs (Invite, Accept, Switch)
app.include_router(admin.router)             # Admin Panel APIs (User management, Moderation)
app.include_router(photo.router)             # Photo Upload APIs (Upload, Delete, Make Primary)
app.include_router(password_reset.router)    # Password Reset APIs (Forgot, Reset)
app.include_router(privacy.router)           # Privacy & Blocking APIs (Block, Unblock)
app.include_router(setup.router)             # Setup APIs (Create Super Admin)
app.include_router(admin_management.router)  # Admin Management APIs (Create Admin)
app.include_router(notification.router)      # Notifications APIs (Get, Read, Delete)
app.include_router(preferences.router)       # Partner Preferences APIs (Get, Update)

# ========== ROOT ENDPOINTS ==========
@app.get("/")
def root():
    return {
        "message": "Matrimony API is running!",
        "version": "2.0.0",
        "status": "healthy",
        "endpoints": {
            "auth": {
                "email": "/auth/register, /auth/login",
                "mobile": "/mobile-auth/send-otp, /mobile-auth/verify-otp",
                "password_reset": "/auth/forgot-password, /auth/reset-password"
            },
            "profile": "/profile/me",
            "search": "/search/profiles",
            "interest": "/interest/send, /interest/received, /interest/sent",
            "parental_login": "/manager/invite, /manager/accept, /manager/profiles",
            "admin": "/admin/users, /admin/dashboard, /admin/reports",
            "photo": "/photo/upload, /photo/my-photos",
            "privacy": "/privacy/block, /privacy/unblock, /privacy/blocked",
            "setup": "/setup/create-super-admin",
            "admin_management": "/admin-management/create-admin, /admin-management/admins",
            "notifications": "/notifications, /notifications/{id}/read",
            "preferences": "/preferences"
        }
    }

@app.get("/health")
def health():
    return {"status": "healthy", "service": "Matrimony App", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)