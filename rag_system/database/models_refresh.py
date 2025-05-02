"""
Refresh token DB models extension.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, LargeBinary, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID

from .models import Base

class RefreshToken(Base):
    """Refresh token model."""
    __tablename__ = "refresh_tokens"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    issued_by_ip = Column(String(50), nullable=True)
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User")