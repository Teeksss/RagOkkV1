"""
Role-based authorization middleware.
"""
import logging
from functools import wraps
from typing import List, Dict, Any, Optional, Callable, TypeVar, cast

from fastapi import Depends, HTTPException, status

from .middleware import get_current_user, user_required
from ..database.models import User

logger = logging.getLogger(__name__)

# Type variables for generics
T = TypeVar('T')


def requires_role(required_roles: List[str]):
    """
    Dependency for role-based access control.
    
    Args:
        required_roles: List of required roles
    """
    async def dependency(token: Dict[str, Any] = Depends(user_required)) -> Dict[str, Any]:
        """
        Check if user has required role.
        
        Args:
            token: User token data
            
        Returns:
            User token data
            
        Raises:
            HTTPException: If user doesn't have required role
        """
        # Get user roles
        user_roles = []
        
        if token.get("is_admin"):
            user_roles.append("admin")
        
        if token.get("is_moderator"):
            user_roles.append("moderator")
        
        # Add default role
        user_roles.append("user")
        
        # Check if user has any of the required roles
        if not any(role in required_roles for role in user_roles):
            logger.warning(f"User {token.get('user_id')} missing required roles: {required_roles}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return token
    
    return dependency


def admin_only(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for admin-only endpoint functions.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        # Get user token from kwargs
        token = kwargs.get("token", {})
        
        # Check if user is admin
        if not token.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Call original function
        return await func(*args, **kwargs)
    
    return wrapper


def moderator_or_admin(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for moderator or admin endpoint functions.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        # Get user token from kwargs
        token = kwargs.get("token", {})
        
        # Check if user is admin or moderator
        if not (token.get("is_admin", False) or token.get("is_moderator", False)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Moderator or admin access required"
            )
        
        # Call original function
        return await func(*args, **kwargs)
    
    return wrapper


async def check_api_key(api_key: str, required_scopes: List[str] = None) -> Dict[str, Any]:
    """
    Check API key validity and scopes.
    
    Args:
        api_key: API key
        required_scopes: Required scopes
        
    Returns:
        API key data
        
    Raises:
        HTTPException: If API key is invalid or missing required scopes
    """
    # This would typically query the database to validate the API key
    # and check if it has the required scopes
    
    # For demonstration purposes, we'll use a mock implementation
    if not api_key or not api_key.startswith("API_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Parse API key to get prefix
    try:
        prefix = api_key.split("_")[1]
    except:
        prefix = "UNKNOWN"
    
    # In a real implementation, you would:
    # 1. Query the APIKey model using the prefix
    # 2. Verify the key hash
    # 3. Check expiration
    # 4. Check scopes
    # 5. Update last_used_at
    
    # Mock data for demonstration
    api_key_data = {
        "id": "mock-api-key-id",
        "prefix": prefix,
        "scopes": ["read", "write"],
        "user_id": "mock-user-id",
    }
    
    # Check scopes if required
    if required_scopes:
        if not all(scope in api_key_data["scopes"] for scope in required_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API key missing required scopes",
                headers={"WWW-Authenticate": "ApiKey"},
            )
    
    return api_key_data