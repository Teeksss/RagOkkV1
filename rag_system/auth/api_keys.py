"""
API key authentication utilities.
"""
import os
import secrets
import logging
from typing import Optional, Tuple
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status, Security, Request
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from ..database.models import ApiKey, User
from ..database.document_store import get_db

logger = logging.getLogger(__name__)

# API key header
API_KEY_HEADER = APIKeyHeader(name="X-API-KEY", auto_error=False)


def generate_api_key() -> str:
    """
    Generate a secure API key.
    
    Returns:
        API key string
    """
    return secrets.token_urlsafe(32)


def create_api_key(db: Session, user_id: str, name: str, 
                   expires_days: Optional[int] = None) -> ApiKey:
    """
    Create a new API key for user.
    
    Args:
        db: Database session
        user_id: User ID
        name: API key name
        expires_days: Number of days until key expires (None for no expiration)
        
    Returns:
        Created API key
    """
    # Generate API key
    key = generate_api_key()
    
    # Calculate expiration
    expires_at = None
    if expires_days is not None and expires_days > 0:
        expires_at = datetime.utcnow() + timedelta(days=expires_days)
    
    # Create API key
    api_key = ApiKey(
        user_id=user_id,
        key=key,
        name=name,
        is_active=True,
        created_at=datetime.utcnow(),
        expires_at=expires_at
    )
    
    # Save to database
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    return api_key


def revoke_api_key(db: Session, key_id: str, user_id: str) -> bool:
    """
    Revoke an API key.
    
    Args:
        db: Database session
        key_id: API key ID
        user_id: User ID (for authorization)
        
    Returns:
        Success status
    """
    # Get API key
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    
    if not api_key:
        return False
    
    # Check ownership
    if api_key.user_id != user_id:
        logger.warning(f"User {user_id} attempted to revoke API key {key_id} owned by {api_key.user_id}")
        return False
    
    # Revoke key
    api_key.is_active = False
    db.commit()
    
    return True


def verify_api_key(db: Session, api_key: str) -> Tuple[bool, Optional[str]]:
    """
    Verify an API key.
    
    Args:
        db: Database session
        api_key: API key to verify
        
    Returns:
        Tuple of (is_valid, user_id)
    """
    # Find API key
    key = db.query(ApiKey).filter(ApiKey.key == api_key).first()
    
    if not key:
        return False, None
    
    # Check if active
    if not key.is_active:
        return False, None
    
    # Check if expired
    if key.expires_at and key.expires_at < datetime.utcnow():
        return False, None
    
    # Update last used timestamp
    key.last_used_at = datetime.utcnow()
    db.commit()
    
    return True, key.user_id


async def get_api_key_user(
    api_key: str = Security(API_KEY_HEADER),
    db: Session = Depends(get_db)
) -> str:
    """
    Get user from API key.
    
    Args:
        api_key: API key
        db: Database session
        
    Returns:
        User ID
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    is_valid, user_id = verify_api_key(db, api_key)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    return user_id


async def get_auth_user(request: Request, 
                        token_user: Optional[str] = Depends(get_current_user),
                        api_key_user: Optional[str] = Depends(get_api_key_user)) -> str:
    """
    Get authenticated user from JWT token or API key.
    
    Args:
        request: FastAPI request
        token_user: User ID from JWT token
        api_key_user: User ID from API key
        
    Returns:
        User ID
    """
    # Priority: JWT token > API key
    if token_user:
        return token_user
    
    if api_key_user:
        return api_key_user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer or APIKey"},
    )