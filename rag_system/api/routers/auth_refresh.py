"""
Authentication refresh endpoints.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...database.document_store import get_db
from ...database.models import User, RefreshToken
from ...auth.auth_service import create_access_token, decode_token
from ...config import settings
from ...utils.db_logger import DBLogger

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"description": "Unauthorized"}},
)

# Models
class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token.
    """
    # Check refresh token in database
    token_record = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_data.refresh_token,
        RefreshToken.expires_at > datetime.utcnow()
    ).first()
    
    if not token_record:
        logger.warning(f"Invalid or expired refresh token attempted")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user
    user = db.query(User).filter(User.id == token_record.user_id).first()
    
    if not user or not user.is_active:
        logger.warning(f"Refresh token used for inactive or deleted user")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new access token
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
    
    # Determine if we should rotate the refresh token
    # Best practice is to rotate refresh tokens to prevent them from being used
    # for extended periods of time
    should_rotate_refresh_token = token_record.last_used_at and (
        (datetime.utcnow() - token_record.last_used_at) > timedelta(days=1) or
        (token_record.expires_at - datetime.utcnow()) < timedelta(days=3)
    )
    
    refresh_token_value = None
    
    if should_rotate_refresh_token:
        # Generate new refresh token
        import uuid
        import secrets
        
        # Create new refresh token
        refresh_token_value = secrets.token_urlsafe(64)
        new_refresh_token = RefreshToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token=refresh_token_value,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            issued_by_ip=token_record.issued_by_ip
        )
        
        # Add new token and remove old one
        db.add(new_refresh_token)
        db.delete(token_record)
    else:
        # Update last used time
        token_record.last_used_at = datetime.utcnow()
    
    # Log token refresh
    db_logger = DBLogger(db)
    db_logger.log_info(
        operation="token_refresh",
        message=f"Token refreshed for user: {user.username}",
        user_id=user.id,
        data={
            "token_rotated": should_rotate_refresh_token
        }
    )
    
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_value,
        "token_type": "bearer"
    }


@router.post("/logout/refresh")
async def invalidate_refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Invalidate refresh token (logout).
    """
    # Find token
    token_record = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_data.refresh_token
    ).first()
    
    if token_record:
        # Get user for logging
        user_id = token_record.user_id
        
        # Delete token
        db.delete(token_record)
        db.commit()
        
        # Log token invalidation
        db_logger = DBLogger(db)
        db_logger.log_info(
            operation="token_invalidate",
            message="Refresh token invalidated",
            user_id=user_id
        )
    
    # Always return success to prevent enumeration
    return {"message": "Token invalidated"}