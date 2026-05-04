from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    name = Column(String(100))
    gender = Column(String(10))
    dob = Column(Date, nullable=True)
    religion = Column(String(50), nullable=True)
    mother_tongue = Column(String(50), nullable=True)
    marital_status = Column(String(20), nullable=True)
    height = Column(Integer, nullable=True)
    city = Column(String(100), nullable=True)
    about_me = Column(Text, nullable=True)
    profile_completeness = Column(Integer, default=0)
    is_visible = Column(Boolean, default=True)
    last_active = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Extended fields
    highest_education = Column(String(100), nullable=True)
    employment_status = Column(String(50), nullable=True)
    annual_income = Column(String(50), nullable=True)
    diet = Column(String(50), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="profile")
    photos = relationship("Photo", back_populates="profile", cascade="all, delete-orphan")