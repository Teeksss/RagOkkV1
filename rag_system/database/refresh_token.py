"""
Refresh token model and utilities.
"""
import logging
import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_

from .models import RefreshToken, User
from ..config import settings

logger = logging.getLogger(__name__)

def create_refresh_token(
    db: Session,
    user_id: str,
    ip_address: Optional[str] = None
) -> str:
    """
    Create refresh token for user.
    
    Args:
        db: Database session
        user_id: User ID
        ip_address: Client IP address
        
    Returns:
        Refresh token
    """
    import secrets
    
    # Generate token
    token = secrets.token_urlsafe(64)
    
    # Calculate expiration
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Create token
    refresh_token = RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user_id,
        token=token,
        expires_at=expires_at,
        created_at=datetime.utcnow(),
        issued_by_ip=ip_address
    )
    
    # Add to database
    db.add(refresh_token)
    db.commit()
    
    return token

def invalidate_user_tokens(
    db: Session,
    user_id: str
) -> int:
    """
    Invalidate all refresh tokens for user.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        Number of tokens invalidated
    """
    # Get all tokens for user
    tokens = db.query(RefreshToken).filter(RefreshToken.user_id == user_id).all()
    
    count = len(tokens)
    
    # Delete all tokens
    for token in tokens:
        db.delete(token)
    
    db.commit()
    
    return count

def cleanup_expired_tokens(db: Session) -> int:
    """
    Clean up expired refresh tokens.
    
    Args:
        db: Database session
        
    Returns:
        Number of tokens deleted
    """
    # Delete expired tokens
    result = db.query(RefreshToken).filter(
        RefreshToken.expires_at < datetime.utcnow()
    ).delete()
    
    db.commit()
    
    return result