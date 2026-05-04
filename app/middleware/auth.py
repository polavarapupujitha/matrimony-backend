from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import uuid
from app.database import get_db
from app.models.user import User
from app.utils.jwt_handler import decode_token

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # Convert string to UUID
    try:
        user_uuid = uuid.UUID(user_id)
    except:
        raise HTTPException(status_code=401, detail="Invalid user ID format")
    
    user = db.query(User).filter(User.id == user_uuid, User.is_active == True).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user