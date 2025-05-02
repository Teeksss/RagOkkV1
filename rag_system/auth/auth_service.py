"""
Authentication service.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..config import settings
from ..database.document_store import get_db
from ..database.models import User, APIKey

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        Whether password is correct
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Get password hash.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create access token.
    
    Args:
        data: Token data
        expires_delta: Token expiration
        
    Returns:
        JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from token.
    
    Args:
        token: JWT token
        db: Database session
        
    Returns:
        User model
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Find user
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.
    
    Args:
        current_user: Current user
        
    Returns:
        User model
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return current_user


async def verify_api_key(
    api_key: str, 
    required_scopes: Optional[list] = None, 
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Verify API key.
    
    Args:
        api_key: API key
        required_scopes: Required scopes
        db: Database session
        
    Returns:
        API key information
        
    Raises:
        HTTPException: If API key is invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract prefix for lookup
    prefix = api_key[:16] if len(api_key) >= 16 else api_key
    
    # Hash API key (in a real system, you would use a proper hashing method)
    key_hash = f"hashed_{api_key}"
    
    # Find API key
    api_key_db = db.query(APIKey).filter(
        APIKey.prefix == prefix,
        APIKey.key_hash == key_hash
    ).first()
    
    if not api_key_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if expired
    if api_key_db.expires_at and api_key_db.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check required scopes
    if required_scopes:
        has_scopes = all(scope in api_key_db.scopes for scope in required_scopes)
        if not has_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"API key doesn't have required scopes: {', '.join(required_scopes)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # Update last used time
    api_key_db.last_used_at = datetime.utcnow()
    db.commit()
    
    # Find associated user
    user = db.query(User).filter(User.id == api_key_db.created_by).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key user not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key user is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "key_id": api_key_db.id,
        "user_id": user.id,
        "username": user.username,
        "scopes": api_key_db.scopes,
        "is_admin": user.is_admin,
        "is_moderator": user.is_moderator
    }