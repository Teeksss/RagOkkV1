"""
API endpoints for user management.
"""
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel, Field, EmailStr

from ...database.document_store import get_db
from ...database.models import User, Document, Conversation, Message, Feedback, APIKey
from ...auth.middleware import admin_required, user_required
from ...auth.auth_service import get_password_hash, verify_password
from ...utils.db_logger import DBLogger
from ...utils.auth import validate_password, validate_email, validate_username

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

# Models
class UserUpdate(BaseModel):
    """User update model."""
    username: Optional[str] = Field(None, min_length=3, max_length=64)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=128)
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    is_moderator: Optional[bool] = None


class PasswordChange(BaseModel):
    """Password change model."""
    current_password: str
    new_password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    """User response model."""
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_admin: bool
    is_moderator: bool
    created_at: datetime
    last_login: Optional[datetime] = None


@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    List users (admin only).
    """
    # Get users
    users = db.query(User).order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    
    # Format users
    result = []
    for user in users:
        result.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "is_moderator": user.is_moderator,
            "created_at": user.created_at,
            "last_login": user.last_login
        })
    
    return result


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Get current user.
    """
    # Get user
    user = db.query(User).filter(User.id == token.get("user_id")).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "is_moderator": user.is_moderator,
        "created_at": user.created_at,
        "last_login": user.last_login
    }


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str = Path(..., description="User ID"),
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Get user by ID (admin only).
    """
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "is_moderator": user.is_moderator,
        "created_at": user.created_at,
        "last_login": user.last_login
    }


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Update current user.
    """
    # Get user
    user = db.query(User).filter(User.id == token.get("user_id")).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate username if provided
    if user_data.username is not None:
        # Check if username already exists
        existing_user = db.query(User).filter(
            User.username == user_data.username,
            User.id != user.id
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Validate username format
        username_validation = validate_username(user_data.username)
        if not username_validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=username_validation["message"]
            )
        
        user.username = user_data.username
    
    # Validate email if provided
    if user_data.email is not None:
        # Check if email already exists
        existing_user = db.query(User).filter(
            User.email == user_data.email,
            User.id != user.id
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        
        # Validate email format
        email_validation = validate_email(user_data.email)
        if not email_validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=email_validation["message"]
            )
        
        user.email = user_data.email
    
    # Update other fields
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    
    # Cannot change admin status
    if user_data.is_admin is not None and user_data.is_admin != user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change admin status"
        )
    
    # Cannot change moderator status
    if user_data.is_moderator is not None and user_data.is_moderator != user.is_moderator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change moderator status"
        )
    
    # Cannot change active status
    if user_data.is_active is not None and user_data.is_active != user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change active status"
        )
    
    # Commit changes
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "is_moderator": user.is_moderator,
        "created_at": user.created_at,
        "last_login": user.last_login
    }


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Update user (admin only).
    """
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate username if provided
    if user_data.username is not None:
        # Check if username already exists
        existing_user = db.query(User).filter(
            User.username == user_data.username,
            User.id != user.id
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Validate username format
        username_validation = validate_username(user_data.username)
        if not username_validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=username_validation["message"]
            )
        
        user.username = user_data.username
    
    # Validate email if provided
    if user_data.email is not None:
        # Check if email already exists
        existing_user = db.query(User).filter(
            User.email == user_data.email,
            User.id != user.id
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        
        # Validate email format
        email_validation = validate_email(user_data.email)
        if not email_validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=email_validation["message"]
            )
        
        user.email = user_data.email
    
    # Update other fields
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    if user_data.is_admin is not None:
        user.is_admin = user_data.is_admin
    
    if user_data.is_moderator is not None:
        user.is_moderator = user_data.is_moderator
    
    # Commit changes
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "is_moderator": user.is_moderator,
        "created_at": user.created_at,
        "last_login": user.last_login
    }


@router.put("/me/password")
async def change_current_user_password(
    password_data: PasswordChange,
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Change current user password.
    """
    # Get user
    user = db.query(User).filter(User.id == token.get("user_id")).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password
    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    # Validate new password
    password_validation = validate_password(password_data.new_password)
    if not password_validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=password_validation["message"]
        )
    
    # Update password
    user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: str = Path(..., description="User ID"),
    permanently: bool = Query(False, description="Permanently delete user data"),
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Delete user (admin only).
    """
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db_logger = DBLogger(db)
    
    # If permanently delete, remove all user data
    if permanently:
        # Delete user's documents
        documents = db.query(Document).filter(Document.user_id == user_id).all()
        for doc in documents:
            db.delete(doc)
        
        # Delete user's conversations
        conversations = db.query(Conversation).filter(Conversation.user_id == user_id).all()
        for conv in conversations:
            db.delete(conv)
        
        # Delete user's messages
        messages = db.query(Message).filter(Message.user_id == user_id).all()
        for msg in messages:
            db.delete(msg)
        
        # Delete user's feedback
        feedback = db.query(Feedback).filter(Feedback.user_id == user_id).all()
        for fb in feedback:
            db.delete(fb)
        
        # Delete user's API keys
        api_keys = db.query(APIKey).filter(APIKey.created_by == user_id).all()
        for key in api_keys:
            db.delete(key)
        
        # Delete user
        db.delete(user)
        
        # Commit changes
        db.commit()
        
        # Log deletion
        db_logger.log_info(
            operation="user_delete",
            message=f"User {user.username} permanently deleted",
            user_id=token.get("user_id"),
            data={"deleted_user_id": user_id, "deleted_username": user.username}
        )
        
        return {"message": "User permanently deleted"}
    else:
        # Soft delete
        user.is_active = False
        db.commit()
        
        # Log deactivation
        db_logger.log_info(
            operation="user_deactivate",
            message=f"User {user.username} deactivated",
            user_id=token.get("user_id"),
            data={"deactivated_user_id": user_id}
        )
        
        return {"message": "User deactivated"}


@router.get("/statistics/me")
async def get_current_user_statistics(
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Get current user statistics.
    """
    user_id = token.get("user_id")
    
    # Count user's documents
    document_count = db.query(func.count(Document.id)).filter(
        Document.user_id == user_id,
        Document.deleted == False
    ).scalar() or 0
    
    # Count user's conversations
    conversation_count = db.query(func.count(Conversation.id)).filter(
        Conversation.user_id == user_id
    ).scalar() or 0
    
    # Count user's messages
    message_count = db.query(func.count(Message.id)).filter(
        Message.conversation_id.in_(
            db.query(Conversation.id).filter(Conversation.user_id == user_id)
        )
    ).scalar() or 0
    
    # Get document types
    document_types = db.query(
        Document.content_type,
        func.count(Document.id).label("count")
    ).filter(
        Document.user_id == user_id,
        Document.deleted == False
    ).group_by(
        Document.content_type
    ).all()
    
    document_types_result = []
    for doc_type, count in document_types:
        document_types_result.append({
            "type": doc_type or "unknown",
            "count": count
        })
    
    return {
        "document_count": document_count,
        "conversation_count": conversation_count,
        "message_count": message_count,
        "document_types": document_types_result
    }