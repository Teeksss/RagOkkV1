"""
JWT token generation and validation.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union

from jose import jwt, JWTError
from pydantic import BaseModel

from ..config import settings

logger = logging.getLogger(__name__)

class TokenData(BaseModel):
    """Token data model."""
    user_id: str
    username: str
    email: str
    is_admin: bool = False
    is_moderator: bool = False
    exp: Optional[datetime] = None


def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create access token.
    
    Args:
        data: Token data
        expires_delta: Expiration delta
        
    Returns:
        JWT token
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Create JWT token
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create refresh token.
    
    Args:
        data: Token data
        expires_delta: Expiration delta
        
    Returns:
        JWT token
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Default to 7 days
        expire = datetime.utcnow() + timedelta(days=7)
    
    to_encode.update({"exp": expire})
    
    # Create JWT token
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        Decoded token data
        
    Raises:
        JWTError: Invalid token
    """
    try:
        # Decode token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        return payload
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise


def verify_token(token: str) -> Optional[TokenData]:
    """
    Verify JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        Token data if valid, None otherwise
    """
    try:
        # Decode token
        payload = decode_token(token)
        
        # Extract user data
        user_id = payload.get("user_id")
        username = payload.get("username")
        email = payload.get("email")
        is_admin = payload.get("is_admin", False)
        is_moderator = payload.get("is_moderator", False)
        exp = payload.get("exp")
        
        if user_id is None or username is None or email is None:
            logger.warning("Invalid token payload: missing required fields")
            return None
        
        # Create token data
        token_data = TokenData(
            user_id=user_id,
            username=username,
            email=email,
            is_admin=is_admin,
            is_moderator=is_moderator,
            exp=datetime.fromtimestamp(exp) if exp else None
        )
        
        return token_data
    
    except JWTError as e:
        logger.error(f"JWT verification error: {str(e)}")
        return None