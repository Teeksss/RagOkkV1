"""
API endpoints for user-specific data.
"""
import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...auth.middleware import admin_required, admin_or_moderator
from ...auth.jwt import get_current_user
from ...database.models import Document, DocumentChunk, Conversation, Message, User
from ...database.document_store import get_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}},
)


class UserDocumentResponse(BaseModel):
    """User document response model."""
    id: str
    title: str
    filename: str
    content_type: str
    created_at: str
    processing_status: str
    chunk_count: int


class UserQueryResponse(BaseModel):
    """User query response model."""
    id: str
    query: str
    timestamp: str
    conversation_id: Optional[str] = None


@router.get("/docs", response_model=List[UserDocumentResponse])
async def get_user_documents(
    skip: int = 0,
    limit: int = 20,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get documents belonging to the current user.
    """
    # Query user documents
    documents = db.query(Document).filter(
        Document.user_id == user_id,
        Document.deleted == False
    ).order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    
    # Prepare response with chunk counts
    result = []
    for doc in documents:
        # Count chunks
        chunk_count = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == doc.id
        ).count()
        
        # Format document
        result.append({
            "id": doc.id,
            "title": doc.metadata.get("title", doc.filename) if doc.metadata else doc.filename,
            "filename": doc.filename,
            "content_type": doc.content_type,
            "created_at": doc.created_at.isoformat(),
            "processing_status": doc.processing_status,
            "chunk_count": chunk_count
        })
    
    return result


@router.get("/queries", response_model=List[UserQueryResponse])
async def get_user_queries(
    skip: int = 0,
    limit: int = 20,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get queries made by the current user.
    """
    # Get user messages that are queries (role = user)
    messages = db.query(Message).filter(
        Message.user_id == user_id,
        Message.role == "user"
    ).order_by(Message.timestamp.desc()).offset(skip).limit(limit).all()
    
    result = []
    for msg in messages:
        result.append({
            "id": msg.id,
            "query": msg.content,
            "timestamp": msg.timestamp.isoformat(),
            "conversation_id": msg.conversation_id
        })
    
    return result


@router.get("/conversations", response_model=List[Dict[str, Any]])
async def get_user_conversations(
    skip: int = 0,
    limit: int = 20,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get conversations belonging to the current user.
    """
    conversations = db.query(Conversation).filter(
        Conversation.user_id == user_id
    ).order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for conv in conversations:
        # Get message count
        message_count = db.query(Message).filter(
            Message.conversation_id == conv.id
        ).count()
        
        # Get first message (query)
        first_message = db.query(Message).filter(
            Message.conversation_id == conv.id,
            Message.role == "user"
        ).order_by(Message.timestamp.asc()).first()
        
        result.append({
            "id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat(),
            "message_count": message_count,
            "first_query": first_message.content if first_message else ""
        })
    
    return result


# Admin routes

@router.get("/all", response_model=List[Dict[str, Any]])
async def get_all_users(
    skip: int = 0,
    limit: int = 50,
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Get all users (admin only).
    """
    users = db.query(User).order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for user in users:
        # Count documents
        doc_count = db.query(Document).filter(
            Document.user_id == user.id,
            Document.deleted == False
        ).count()
        
        # Count conversations
        conv_count = db.query(Conversation).filter(
            Conversation.user_id == user.id
        ).count()
        
        result.append({
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "name": user.name,
            "role": user.role,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "document_count": doc_count,
            "conversation_count": conv_count
        })
    
    return result


@router.get("/{user_id}/documents", response_model=List[UserDocumentResponse])
async def get_user_documents_by_id(
    user_id: str = Path(..., description="User ID"),
    skip: int = 0,
    limit: int = 20,
    token: Dict[str, Any] = Depends(admin_or_moderator),
    db: Session = Depends(get_db)
):
    """
    Get documents belonging to specific user (admin or moderator only).
    """
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Query user documents
    documents = db.query(Document).filter(
        Document.user_id == user_id,
        Document.deleted == False
    ).order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    
    # Prepare response with chunk counts
    result = []
    for doc in documents:
        # Count chunks
        chunk_count = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == doc.id
        ).count()
        
        # Format document
        result.append({
            "id": doc.id,
            "title": doc.metadata.get("title", doc.filename) if doc.metadata else doc.filename,
            "filename": doc.filename,
            "content_type": doc.content_type,
            "created_at": doc.created_at.isoformat(),
            "processing_status": doc.processing_status,
            "chunk_count": chunk_count
        })
    
    return result