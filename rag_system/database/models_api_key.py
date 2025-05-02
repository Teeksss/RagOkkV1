"""
API Key model for database.
This should be added to models.py
"""

class APIKey(Base):
    """API key model."""
    __tablename__ = "api_keys"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(64), nullable=False)
    key_hash = Column(String(128), nullable=False)  # In production, this should be properly hashed
    prefix = Column(String(16), nullable=False)
    scopes = Column(JSON, nullable=False)  # e.g. ["read", "write", "admin"]
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", backref="api_keys")