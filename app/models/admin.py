from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class AdminUser(Base):
    __tablename__ = "admin_users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    role = Column(String(50))  # super_admin, admin, moderator, viewer
    assigned_region = Column(String(100), nullable=True)
    assigned_community = Column(String(100), nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    permissions = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    last_active = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class ModerationQueue(Base):
    __tablename__ = "moderation_queue"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_type = Column(String(20))  # profile, photo, interest
    target_id = Column(UUID(as_uuid=True))
    reason = Column(String(100))
    reported_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status = Column(String(20), default="pending")  # pending, approved, rejected, escalated
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    review_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    resolved_at = Column(DateTime, nullable=True)

class AdminActionLog(Base):
    __tablename__ = "admin_action_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_id = Column(UUID(as_uuid=True), ForeignKey("admin_users.id"))
    action = Column(String(100))
    target_type = Column(String(50))
    target_id = Column(UUID(as_uuid=True))
    details = Column(JSON)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reported_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reason = Column(String(100))
    description = Column(Text, nullable=True)
    screenshot_urls = Column(JSON, nullable=True)
    status = Column(String(20), default="pending")  # pending, resolved, rejected
    resolved_by = Column(UUID(as_uuid=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    resolved_at = Column(DateTime, nullable=True)