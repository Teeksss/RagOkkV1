"""
API endpoints for user management.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel, Field, EmailStr

from ...database.document_store import get_db
from ...database.models import User, Document, Conversation, Message
from ...auth.middleware import admin_required, user_required, admin_or_moderator
from ...auth.auth import get_password_hash, verify_password
from ...utils.db_logger import DBLogger

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

# Models
class UserUpdate(BaseModel):
    """User update model."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    preferences: Optional[Dict[str, Any]] = None


class UserPasswordUpdate(BaseModel):
    """User password update model."""
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


class UserStats(BaseModel):
    """User statistics model."""
    document_count: int
    conversation_count: int
    message_count: int
    last_activity: Optional[datetime] = None


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Get current user information.
    """
    # Get user
    user = db.query(User).filter(User.id == token.get("user_id")).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


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
    
    # Update fields
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    
    if user_data.email is not None:
        # Check if email is already used
        existing_user = db.query(User).filter(
            User.email == user_data.email,
            User.id != user.id
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        user.email = user_data.email
    
    if user_data.preferences is not None:
        # Merge with existing preferences
        current_prefs = user.preferences or {}
        current_prefs.update(user_data.preferences)
        user.preferences = current_prefs
    
    db.commit()
    db.refresh(user)
    
    return user


@router.put("/me/password")
async def update_current_user_password(
    password_update: UserPasswordUpdate,
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Update current user password.
    """
    # Get user
    user = db.query(User).filter(User.id == token.get("user_id")).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password
    if not verify_password(password_update.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    # Update password
    user.hashed_password = get_password_hash(password_update.new_password)
    db.commit()
    
    # Log password change
    db_logger = DBLogger(db)
    db_logger.log_info(
        operation="password_change",
        message="Password changed",
        user_id=user.id
    )
    
    return {"status": "success", "message": "Password updated successfully"}


@router.get("/me/stats", response_model=UserStats)
async def get_current_user_stats(
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Get current user statistics.
    """
    user_id = token.get("user_id")
    
    # Get document count
    document_count = db.query(func.count(Document.id)).filter(
        Document.user_id == user_id,
        Document.deleted == False
    ).scalar() or 0
    
    # Get conversation count
    conversation_count = db.query(func.count(Conversation.id)).filter(
        Conversation.user_id == user_id
    ).scalar() or 0
    
    # Get message count
    message_count = db.query(func.count(Message.id)).filter(
        Message.user_id == user_id
    ).scalar() or 0
    
    # Get last activity
    last_message = db.query(Message).filter(
        Message.user_id == user_id
    ).order_by(desc(Message.timestamp)).first()
    
    last_activity = last_message.timestamp if last_message else None
    
    return {
        "document_count": document_count,
        "conversation_count": conversation_count,
        "message_count": message_count,
        "last_activity": last_activity
    }


@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by username or email"),
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    List users (admin only).
    """
    # Build query
    query = db.query(User)
    
    # Apply filters
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if search:
        query = query.filter(
            User.username.ilike(f"%{search}%") | 
            User.email.ilike(f"%{search}%") |
            User.full_name.ilike(f"%{search}%")
        )
    
    # Get total count
    total_count = query.count()
    
    # Apply pagination
    users = query.order_by(User.username).offset(skip).limit(limit).all()
    
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str = Path(..., description="User ID"),
    token: Dict[str, Any] = Depends(admin_or_moderator),
    db: Session = Depends(get_db)
):
    """
    Get user by ID (admin or moderator only).
    """
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/{user_id}/status")
async def update_user_status(
    user_id: str = Path(..., description="User ID"),
    is_active: bool = Body(..., embed=True),
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Update user active status (admin only).
    """
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update status
    user.is_active = is_active
    db.commit()
    
    # Log status change
    db_logger = DBLogger(db)
    db_logger.log_info(
        operation="user_status_change",
        message=f"User status changed to {'active' if is_active else 'inactive'}",
        user_id=token.get("user_id"),
        data={"target_user_id": user_id, "is_active": is_active}
    )
    
    return {"status": "success", "is_active": is_active}


@router.put("/{user_id}/role")
async def update_user_role(
    user_id: str = Path(..., description="User ID"),
    is_admin: Optional[bool] = Body(None),
    is_moderator: Optional[bool] = Body(None),
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Update user roles (admin only).
    """
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if trying to change self
    if user_id == token.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )
    
    # Update roles
    if is_admin is not None:
        user.is_admin = is_admin
    
    if is_moderator is not None:
        user.is_moderator = is_moderator
    
    db.commit()
    
    # Log role change
    db_logger = DBLogger(db)
    db_logger.log_info(
        operation="user_role_change",
        message="User role changed",
        user_id=token.get("user_id"),
        data={
            "target_user_id": user_id, 
            "is_admin": user.is_admin, 
            "is_moderator": user.is_moderator
        }
    )
    
    return {
        "status": "success", 
        "is_admin": user.is_admin, 
        "is_moderator": user.is_moderator
    }


@router.delete("/{user_id}")
async def delete_user(
    user_id: str = Path(..., description="User ID"),
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
    
    # Check if trying to delete self
    if user_id == token.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    # Delete user
    db.delete(user)
    db.commit()
    
    # Log user deletion
    db_logger = DBLogger(db)
    db_logger.log_info(
        operation="user_delete",
        message=f"User {user.username} deleted",
        user_id=token.get("user_id"),
        data={"deleted_user_id": user_id}
    )
    
    return {"status": "success", "message": "User deleted successfully"}


@router.get("/{user_id}/stats", response_model=UserStats)
async def get_user_stats(
    user_id: str = Path(..., description="User ID"),
    token: Dict[str, Any] = Depends(admin_or_moderator),
    db: Session = Depends(get_db)
):
    """
    Get user statistics (admin or moderator only).
    """
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get document count
    document_count = db.query(func.count(Document.id)).filter(
        Document.user_id == user_id,
        Document.deleted == False
    ).scalar() or 0
    
    # Get conversation count
    conversation_count = db.query(func.count(Conversation.id)).filter(
        Conversation.user_id == user_id
    ).scalar() or 0
    
    # Get message count
    message_count = db.query(func.count(Message.id)).filter(
        Message.user_id == user_id
    ).scalar() or 0
    
    # Get last activity
    last_message = db.query(Message).filter(
        Message.user_id == user_id
    ).order_by(desc(Message.timestamp)).first()
    
    last_activity = last_message.timestamp if last_message else None
    
    return {
        "document_count": document_count,
        "conversation_count": conversation_count,
        "message_count": message_count,
        "last_activity": last_activity
    }