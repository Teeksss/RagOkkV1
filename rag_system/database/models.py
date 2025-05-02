"""
Database models for RAG system.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON,
    UniqueConstraint, LargeBinary, Enum, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(256), unique=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    full_name = Column(String(128))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_moderator = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    last_login = Column(DateTime(timezone=True))
    preferences = Column(JSON)
    
    # Relationships
    documents = relationship("Document", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")
    messages = relationship("Message", back_populates="user")
    feedback = relationship("Feedback", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")


class Document(Base):
    """Document model."""
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    filename = Column(String(256), nullable=False)
    content_type = Column(String(128), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    last_updated_at = Column(DateTime(timezone=True))
    processing_status = Column(String(32), default="pending")  # pending, processing, ready, error
    deleted = Column(Boolean, default=False)
    metadata = Column(JSON)
    current_version = Column(Integer, default=1)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")


class DocumentVersion(Base):
    """Document version model."""
    __tablename__ = "document_versions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)
    diff = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    created_by = Column(String(36), nullable=True)
    
    # Relationships
    document = relationship("Document", back_populates="versions")
    
    __table_args__ = (
        UniqueConstraint('document_id', 'version_number', name='uq_document_version'),
    )


class DocumentChunk(Base):
    """Document chunk model."""
    __tablename__ = "document_chunks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=True)
    embedding_stored = Column(Boolean, default=False)
    vector_id = Column(String(64), nullable=True)
    embedding_vector = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    __table_args__ = (
        UniqueConstraint('document_id', 'chunk_index', name='uq_document_chunk'),
    )


class Conversation(Base):
    """Conversation model."""
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    title = Column(String(256), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Message model."""
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    role = Column(String(32), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=func.now())
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    user = relationship("User", back_populates="messages")
    feedback = relationship("Feedback", back_populates="message", cascade="all, delete-orphan")


class Feedback(Base):
    """Feedback model."""
    __tablename__ = "feedback"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String(36), ForeignKey("messages.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5 scale
    thumbs_up = Column(Boolean, nullable=True)
    thumbs_down = Column(Boolean, nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    message = relationship("Message", back_populates="feedback")
    user = relationship("User", back_populates="feedback")


class ABTest(Base):
    """A/B test model."""
    __tablename__ = "ab_tests"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    control_config = Column(JSON, nullable=False)
    variant_config = Column(JSON, nullable=False)
    traffic_split = Column(Float, default=0.5)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    analyzed_at = Column(DateTime(timezone=True), nullable=True)
    results = Column(JSON, nullable=True)
    
    # Relationships
    test_results = relationship("ABTestResult", back_populates="ab_test", cascade="all, delete-orphan")


class ABTestResult(Base):
    """A/B test result model."""
    __tablename__ = "ab_test_results"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    test_id = Column(String(36), ForeignKey("ab_tests.id"), nullable=False)
    user_id = Column(String(36), nullable=False)
    group = Column(String(32), nullable=False)  # control, variant
    created_at = Column(DateTime(timezone=True), default=func.now())
    conversions = Column(JSON, nullable=True)
    
    # Relationships
    ab_test = relationship("ABTest", back_populates="test_results")
    
    __table_args__ = (
        UniqueConstraint('test_id', 'user_id', name='uq_test_user'),
    )


class Log(Base):
    """System log model."""
    __tablename__ = "logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime(timezone=True), default=func.now())
    level = Column(String(16), nullable=False)  # INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    operation = Column(String(64), nullable=True)
    user_id = Column(String(36), nullable=True)
    request_path = Column(String(256), nullable=True)
    request_method = Column(String(16), nullable=True)
    status_code = Column(Integer, nullable=True)
    response_time = Column(Float, nullable=True)
    ip_address = Column(String(64), nullable=True)
    data = Column(JSON, nullable=True)


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
    user = relationship("User", back_populates="api_keys")