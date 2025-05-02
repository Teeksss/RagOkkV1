"""
Authentication middleware.
"""
import logging
from typing import Dict, Any, Optional, Callable, Union
from functools import wraps

from fastapi import Depends, HTTPException, Header, status
from jose import JWTError
from sqlalchemy.orm import Session

from .auth_service import decode_token, verify_api_key
from ..database.document_store import get_db

logger = logging.getLogger(__name__)

async def get_token_from_header(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Get token data from authorization header.
    
    Args:
        authorization: Authorization header
        x_api_key: API key header
        
    Returns:
        Token data
        
    Raises:
        HTTPException: If no valid authentication provided
    """
    # Check for API key first
    if x_api_key:
        # Return stub data for now, will be verified by verify_api_key
        return {"type": "api_key", "key": x_api_key}
    
    # Check for JWT token
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        # Return stub data for now, will be verified by decode_token
        return {"type": "bearer", "token": token}
    
    # No valid authentication
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

async def auth_middleware(
    token_data: Dict[str, Any] = Depends(get_token_from_header),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Authentication middleware.
    
    Args:
        token_data: Token data
        db: Database session
        
    Returns:
        User information
        
    Raises:
        HTTPException: If authentication fails
    """
    if token_data["type"] == "bearer":
        try:
            # Decode JWT token
            payload = decode_token(token_data["token"])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    elif token_data["type"] == "api_key":
        try:
            # Verify API key
            api_key_info = await verify_api_key(token_data["key"], db=db)
            return api_key_info
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # Unknown token type
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

def user_required(token: Dict[str, Any] = Depends(auth_middleware)) -> Dict[str, Any]:
    """
    Require authenticated user.
    
    Args:
        token: Token data
        
    Returns:
        User information
        
    Raises:
        HTTPException: If user is not authenticated
    """
    return token

def admin_required(token: Dict[str, Any] = Depends(auth_middleware)) -> Dict[str, Any]:
    """
    Require admin user.
    
    Args:
        token: Token data
        
    Returns:
        User information
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not token.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    
    return token

def moderator_required(token: Dict[str, Any] = Depends(auth_middleware)) -> Dict[str, Any]:
    """
    Require moderator or admin user.
    
    Args:
        token: Token data
        
    Returns:
        User information
        
    Raises:
        HTTPException: If user is not a moderator or admin
    """
    if not (token.get("is_admin") or token.get("is_moderator")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator role required"
        )
    
    return token

def scopes_required(required_scopes: list) -> Callable:
    """
    Require specific API key scopes.
    
    Args:
        required_scopes: Required scopes
        
    Returns:
        Dependency function
    """
    def dependency(token: Dict[str, Any] = Depends(auth_middleware)) -> Dict[str, Any]:
        # Check if using API key
        if "scopes" in token:
            has_scopes = all(scope in token["scopes"] for scope in required_scopes)
            if not has_scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required scopes: {', '.join(required_scopes)}"
                )
        
        # If using JWT, admin can access everything
        elif not token.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required scopes: {', '.join(required_scopes)}"
            )
        
        return token
    
    return dependency