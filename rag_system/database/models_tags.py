"""
Tag models for database.
These should be added to models.py
"""
import uuid
from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Tag model
class Tag(Base):
    """Tag model."""
    __tablename__ = "tags"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False, unique=True)
    
    # Relationships
    documents = relationship("DocumentTag", back_populates="tag")


# Document-Tag association model
class DocumentTag(Base):
    """Document-Tag association model."""
    __tablename__ = "document_tags"
    
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(String(36), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    
    # Relationships
    document = relationship("Document", backref="tag_associations")
    tag = relationship("Tag", back_populates="documents")
    
    __table_args__ = (
        UniqueConstraint('document_id', 'tag_id', name='uq_document_tag'),
    )