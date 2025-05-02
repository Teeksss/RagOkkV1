"""
Authentication API endpoints.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Body, Form, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from ...database.document_store import get_db
from ...database.models import User
from ...auth.auth_service import (
    get_password_hash, 
    verify_password, 
    create_access_token,
    get_current_user
)
from ...utils.db_logger import DBLogger
from ...config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"description": "Unauthorized"}},
)

# Models
class UserRegister(BaseModel):
    """User registration model."""
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
    created_at: datetime


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str
    user: UserResponse


class PasswordResetRequest(BaseModel):
    """Password reset request model."""
    email: EmailStr


class PasswordReset(BaseModel):
    """Password reset model."""
    token: str
    new_password: str = Field(..., min_length=8)


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Login to get access token.
    """
    # Find user
    user = db.query(User).filter(User.username == form_data.username).first()
    
    # Check if user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Log failed login attempt
        db_logger = DBLogger(db)
        db_logger.log_warning(
            operation="login_attempt",
            message=f"Failed login attempt for username: {form_data.username}",
            ip_address=request.client.host if request else None
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
            "is_moderator": user.is_moderator
        },
        expires_delta=access_token_expires
    )
    
    # Update last login time
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Log successful login
    db_logger = DBLogger(db)
    db_logger.log_info(
        operation="login",
        message=f"User logged in: {user.username}",
        user_id=user.id,
        ip_address=request.client.host if request else None
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "is_moderator": user.is_moderator,
            "created_at": user.created_at
        }
    }


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Register a new user.
    """
    # Check if username already exists
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    import uuid
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        id=str(uuid.uuid4()),
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        created_at=datetime.utcnow()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log user registration
    db_logger = DBLogger(db)
    db_logger.log_info(
        operation="register",
        message=f"User registered: {new_user.username}",
        user_id=new_user.id,
        ip_address=request.client.host if request else None
    )
    
    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "full_name": new_user.full_name,
        "is_active": new_user.is_active,
        "is_admin": new_user.is_admin,
        "is_moderator": new_user.is_moderator,
        "created_at": new_user.created_at
    }


@router.post("/reset-password")
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset.
    """
    # Find user by email
    user = db.query(User).filter(User.email == reset_data.email).first()
    
    # Always return success to prevent email enumeration attacks
    if not user:
        return {"message": "If your email is registered, you will receive a password reset link"}
    
    # In a real application, you would:
    # 1. Generate a reset token
    # 2. Store it in the database with expiration
    # 3. Send an email with the reset link
    
    # For this example, we'll simulate success
    return {"message": "If your email is registered, you will receive a password reset link"}


@router.post("/reset-password-confirm")
async def confirm_password_reset(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """
    Confirm password reset.
    """
    # In a real application, you would:
    # 1. Verify the reset token
    # 2. Check if it's expired
    # 3. Find the associated user
    # 4. Update the password
    
    # For this example, we'll simulate failure
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired token"
    )