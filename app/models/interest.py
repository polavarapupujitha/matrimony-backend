from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class Interest(Base):
    __tablename__ = "interests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    to_profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    status = Column(String(20), default="pending")  # pending, accepted, declined
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    from_profile = relationship("Profile", foreign_keys=[from_profile_id])
    to_profile = relationship("Profile", foreign_keys=[to_profile_id])