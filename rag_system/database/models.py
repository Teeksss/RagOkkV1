"""
Database models.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, LargeBinary, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID

Base = declarative_base()

class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    full_name = Column(String(128), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_moderator = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    settings = Column(JSONB, nullable=True)
    
    # Relationships
    documents = relationship("Document", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user", foreign_keys="APIKey.created_by")

class APIKey(Base):
    """API key model."""
    __tablename__ = "api_keys"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(64), nullable=False)
    key_hash = Column(String(128), nullable=False)
    prefix = Column(String(16), nullable=False)
    scopes = Column(JSONB, nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys", foreign_keys=[created_by])

class Document(Base):
    """Document model."""
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    content_type = Column(String(128), nullable=True)
    file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated_at = Column(DateTime, default=datetime.utcnow)
    processing_status = Column(String(64), default="pending")
    metadata = Column(JSONB, nullable=True)
    deleted = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    tags = relationship("DocumentTag", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    """Document chunk model."""
    __tablename__ = "document_chunks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding_vector = Column(LargeBinary, nullable=True)
    embedding_stored = Column(Boolean, default=False)
    vector_id = Column(String(36), nullable=True)
    metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")

class Tag(Base):
    """Tag model."""
    __tablename__ = "tags"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False, unique=True)
    
    # Relationships
    documents = relationship("DocumentTag", back_populates="tag")

class DocumentTag(Base):
    """Document-Tag association model."""
    __tablename__ = "document_tags"
    
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(String(36), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    
    # Relationships
    document = relationship("Document", back_populates="tags")
    tag = relationship("Tag", back_populates="documents")

class Conversation(Base):
    """Conversation model."""
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSONB, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    """Message model."""
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    role = Column(String(64), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSONB, nullable=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    user = relationship("User")
    feedbacks = relationship("Feedback", back_populates="message", cascade="all, delete-orphan")

class Feedback(Base):
    """Feedback model."""
    __tablename__ = "feedbacks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=True)
    thumbs_up = Column(Boolean, nullable=True)
    thumbs_down = Column(Boolean, nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message = relationship("Message", back_populates="feedbacks")
    user = relationship("User")

class Log(Base):
    """Log model."""
    __tablename__ = "logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String(16), nullable=False)  # INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    operation = Column(String(64), nullable=True)
    user_id = Column(String(36), nullable=True)
    request_path = Column(String(255), nullable=True)
    request_method = Column(String(16), nullable=True)
    status_code = Column(Integer, nullable=True)
    response_time = Column(Float, nullable=True)
    ip_address = Column(String(64), nullable=True)
    data = Column(JSONB, nullable=True)