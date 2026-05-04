from fastapi import HTTPException, status
from functools import wraps
from typing import List

# Role hierarchy (higher role can access lower role permissions)
ROLE_HIERARCHY = {
    "super_admin": 100,
    "admin": 80,
    "sub_admin": 70,
    "moderator": 60,
    "viewer": 50,
    "support": 40,
    "user": 10
}

# Role permissions mapping
ROLE_PERMISSIONS = {
    "super_admin": [
        "manage_all_users", "manage_admins", "view_all", "delete_any", 
        "moderate_content", "view_reports", "manage_system"
    ],
    "admin": [
        "manage_users", "view_all", "moderate_content", "view_reports"
    ],
    "sub_admin": [
        "manage_region_users", "view_region", "moderate_region"
    ],
    "moderator": [
        "moderate_content", "view_reports", "escalate_reports"
    ],
    "viewer": [
        "view_all", "view_reports"
    ],
    "support": [
        "view_users", "assist_users"
    ],
    "user": [
        "view_own_profile", "edit_own_profile", "send_interest"
    ]
}

def require_role(allowed_roles: List[str]):
    """Decorator to check if user has required role"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_role = current_user.role
            if user_role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{user_role}' not allowed. Required: {allowed_roles}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_permission(required_permission: str):
    """Decorator to check if user has specific permission"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_role = current_user.role
            user_permissions = ROLE_PERMISSIONS.get(user_role, [])
            
            if required_permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{required_permission}' required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def get_user_role_level(role: str) -> int:
    """Get role level for comparison"""
    return ROLE_HIERARCHY.get(role, 0)

def can_user_access(target_user_role: str, current_user_role: str) -> bool:
    """Check if current user can access target user based on roles"""
    current_level = get_user_role_level(current_user_role)
    target_level = get_user_role_level(target_user_role)
    
    # Super admin can access anyone
    if current_user_role == "super_admin":
        return True
    
    # Admin cannot access super admin
    if target_user_role == "super_admin":
        return False
    
    # Users can only access their own data
    if current_user_role == "user":
        return False
    
    return current_level >= target_level