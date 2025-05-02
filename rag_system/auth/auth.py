"""
Authentication API endpoints.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, EmailStr
from passlib.context import CryptContext

from ..database.document_store import get_db
from ..database.models import User
from ..config import settings
from .middleware import create_access_token, get_current_user
from ..utils.db_logger import DBLogger

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"description": "Unauthorized"}},
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Models
class UserCreate(BaseModel):
    """User creation model."""
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    """User response model."""
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_admin: bool
    is_moderator: bool


class Token(BaseModel):
    """Token model."""
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse


class ResetPasswordRequest(BaseModel):
    """Reset password request model."""
    email: EmailStr


class ChangePasswordRequest(BaseModel):
    """Change password request model."""
    current_password: str
    new_password: str = Field(..., min_length=8)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password.
    
    Args:
        plain_password: Plain password
        hashed_password: Hashed password
        
    Returns:
        Whether password is correct
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash password.
    
    Args:
        password: Plain password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate user.
    
    Args:
        db: Database session
        username: Username
        password: Password
        
    Returns:
        User model or None
    """
    # Check if username is actually an email
    if "@" in username:
        user = db.query(User).filter(User.email == username).first()
    else:
        user = db.query(User).filter(User.username == username).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Get access token.
    """
    # Authenticate user
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.id,
            "is_admin": user.is_admin,
            "is_moderator": user.is_moderator
        },
        expires_delta=access_token_expires
    )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Log login
    db_logger = DBLogger(db)
    db_logger.log_info(
        operation="login",
        message=f"User {user.username} logged in",
        user_id=user.id
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "is_moderator": user.is_moderator
        }
    }


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Register new user.
    """
    # Check if username exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active=True,
        is_admin=False,
        is_moderator=False,
        created_at=datetime.utcnow()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log registration
    db_logger = DBLogger(db)
    db_logger.log_info(
        operation="register",
        message=f"User {new_user.username} registered",
        user_id=new_user.id
    )
    
    # Send welcome email in background
    if background_tasks:
        background_tasks.add_task(
            send_welcome_email,
            new_user.email,
            new_user.username
        )
    
    return new_user


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Request password reset.
    """
    # Check if email exists
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        # Return success anyway to prevent user enumeration
        return {
            "status": "success",
            "message": "If your email is registered, you will receive a password reset link"
        }
    
    # Generate reset token
    reset_token = create_access_token(
        data={"sub": user.id, "purpose": "reset_password"},
        expires_delta=timedelta(hours=1)
    )
    
    # Send reset email in background
    if background_tasks:
        background_tasks.add_task(
            send_password_reset_email,
            user.email,
            user.username,
            reset_token
        )
    
    # Log password reset request
    db_logger = DBLogger(db)
    db_logger.log_info(
        operation="reset_password_request",
        message=f"Password reset requested for user {user.username}",
        user_id=user.id
    )
    
    return {
        "status": "success",
        "message": "If your email is registered, you will receive a password reset link"
    }


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change password.
    """
    # Verify current password
    if not verify_password(request.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    user.hashed_password = get_password_hash(request.new_password)
    db.commit()
    
    # Log password change
    db_logger = DBLogger(db)
    db_logger.log_info(
        operation="change_password",
        message=f"Password changed for user {user.username}",
        user_id=user.id
    )
    
    return {
        "status": "success",
        "message": "Password changed successfully"
    }


async def send_welcome_email(email: str, username: str):
    """
    Send welcome email.
    
    Args:
        email: User email
        username: Username
    """
    # This is a placeholder. Implement actual email sending logic.
    logger.info(f"Sending welcome email to {email}")


async def send_password_reset_email(email: str, username: str, reset_token: str):
    """
    Send password reset email.
    
    Args:
        email: User email
        username: Username
        reset_token: Reset token
    """
    # This is a placeholder. Implement actual email sending logic.
    logger.info(f"Sending password reset email to {email}")