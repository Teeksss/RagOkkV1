"""
Authentication and authorization middleware.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database.document_store import get_db
from ..database.models import User
from ..config import settings

logger = logging.getLogger(__name__)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"/api/{settings.API_VERSION}/auth/token"
)

# Models
class TokenData(BaseModel):
    """Token data model."""
    sub: str
    exp: datetime
    is_admin: bool = False
    is_moderator: bool = False


def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Token data
        expires_delta: Token expiration timedelta
        
    Returns:
        JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user from token.
    
    Args:
        token: JWT token
        db: Database session
        
    Returns:
        User model or None
    
    Raises:
        HTTPException: If token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Get subject (user ID)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Create token data
        token_data = TokenData(
            sub=user_id,
            exp=datetime.fromtimestamp(payload.get("exp")),
            is_admin=payload.get("is_admin", False),
            is_moderator=payload.get("is_moderator", False)
        )
        
        # Check if token has expired
        if datetime.utcnow() > token_data.exp:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(
        User.id == token_data.sub,
        User.is_active == True
    ).first()
    
    if user is None:
        raise credentials_exception
    
    return user


def admin_required(
    user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency for admin-only endpoints.
    
    Args:
        user: Current user
        
    Returns:
        User token data
    
    Raises:
        HTTPException: If user is not an admin
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    return {
        "user_id": user.id,
        "username": user.username,
        "is_admin": user.is_admin,
        "is_moderator": user.is_moderator
    }


def admin_or_moderator(
    user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency for admin or moderator endpoints.
    
    Args:
        user: Current user
        
    Returns:
        User token data
    
    Raises:
        HTTPException: If user is not an admin or moderator
    """
    if not user.is_admin and not user.is_moderator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    return {
        "user_id": user.id,
        "username": user.username,
        "is_admin": user.is_admin,
        "is_moderator": user.is_moderator
    }


def user_required(
    user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency for authenticated user endpoints.
    
    Args:
        user: Current user
        
    Returns:
        User token data
    """
    return {
        "user_id": user.id,
        "username": user.username,
        "is_admin": user.is_admin,
        "is_moderator": user.is_moderator
    }