from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class ProfileManager(Base):
    __tablename__ = "profile_managers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    manager_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    relationship_type = Column(String(50))  # father, mother, brother, sister, guardian
    permission_level = Column(String(20), default="limited")
    can_edit_basic = Column(Boolean, default=False)
    can_edit_family = Column(Boolean, default=True)
    can_send_interest = Column(Boolean, default=True)
    can_accept_interest = Column(Boolean, default=True)
    can_chat = Column(Boolean, default=False)
    daily_interest_limit = Column(Integer, default=10)
    interests_sent_today = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships - simplified
    profile = relationship("Profile", foreign_keys=[profile_id])
    manager = relationship("User", foreign_keys=[manager_user_id])

class ManagerInvitation(Base):
    __tablename__ = "manager_invitations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    manager_email = Column(String(255))
    manager_mobile = Column(String(15), nullable=True)
    relationship_type = Column(String(50))
    permission_level = Column(String(20), default="limited")
    token = Column(String(255), unique=True)
    expires_at = Column(DateTime)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, server_default=func.now())

class ManagerActivityLog(Base):
    __tablename__ = "manager_activity_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("profile_managers.id"), nullable=True)
    action = Column(String(50))
    target_id = Column(UUID(as_uuid=True), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, server_default=func.now())