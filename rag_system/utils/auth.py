"""
Authentication utilities.
"""
import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def validate_password(password: str) -> Dict[str, Any]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        Dictionary with validation results
    """
    # Password must be at least 8 characters
    if len(password) < 8:
        return {
            "valid": False,
            "message": "Password must be at least 8 characters long"
        }
    
    # Password must contain at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return {
            "valid": False,
            "message": "Password must contain at least one lowercase letter"
        }
    
    # Password must contain at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return {
            "valid": False,
            "message": "Password must contain at least one uppercase letter"
        }
    
    # Password must contain at least one digit
    if not re.search(r'\d', password):
        return {
            "valid": False,
            "message": "Password must contain at least one digit"
        }
    
    # Password must contain at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return {
            "valid": False,
            "message": "Password must contain at least one special character"
        }
    
    return {
        "valid": True,
        "message": "Password is valid"
    }

def validate_username(username: str) -> Dict[str, Any]:
    """
    Validate username format.
    
    Args:
        username: Username to validate
        
    Returns:
        Dictionary with validation results
    """
    # Username must be at least 3 characters
    if len(username) < 3:
        return {
            "valid": False,
            "message": "Username must be at least 3 characters long"
        }
    
    # Username must be at most 64 characters
    if len(username) > 64:
        return {
            "valid": False,
            "message": "Username must be at most 64 characters long"
        }
    
    # Username must only contain alphanumeric characters, dots, underscores, and hyphens
    if not re.match(r'^[a-zA-Z0-9._-]+$', username):
        return {
            "valid": False,
            "message": "Username must only contain letters, numbers, dots, underscores, and hyphens"
        }
    
    # Username must not start with a dot, underscore, or hyphen
    if re.match(r'^[._-]', username):
        return {
            "valid": False,
            "message": "Username must not start with a dot, underscore, or hyphen"
        }
    
    # Username must not end with a dot, underscore, or hyphen
    if re.match(r'[._-]$', username):
        return {
            "valid": False,
            "message": "Username must not end with a dot, underscore, or hyphen"
        }
    
    return {
        "valid": True,
        "message": "Username is valid"
    }

def validate_email(email: str) -> Dict[str, Any]:
    """
    Validate email format.
    
    Args:
        email: Email to validate
        
    Returns:
        Dictionary with validation results
    """
    # Very basic email validation
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return {
            "valid": False,
            "message": "Invalid email format"
        }
    
    return {
        "valid": True,
        "message": "Email is valid"
    }

def sanitize_username(username: str) -> str:
    """
    Sanitize username for display.
    
    Args:
        username: Username to sanitize
        
    Returns:
        Sanitized username
    """
    # Remove any HTML tags
    username = re.sub(r'<[^>]*>', '', username)
    
    # Replace any special characters with underscore
    username = re.sub(r'[^\w\s.-]', '_', username)
    
    return username

def mask_email(email: str) -> str:
    """
    Mask email for display.
    
    Args:
        email: Email to mask
        
    Returns:
        Masked email
    """
    if not email or '@' not in email:
        return email
    
    # Split email into username and domain parts
    username, domain = email.split('@')
    
    # If username is very short, show only the first character
    if len(username) <= 2:
        masked_username = username[0] + '*'
    # Otherwise, show first and last character with asterisks in between
    else:
        masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
    
    # Split domain into parts
    domain_parts = domain.split('.')
    domain_prefix = '.'.join(domain_parts[:-1])
    domain_suffix = domain_parts[-1]
    
    # If domain prefix is very short, show only the first character
    if len(domain_prefix) <= 2:
        masked_domain_prefix = domain_prefix[0] + '*'
    # Otherwise, show first and last character with asterisks in between
    else:
        masked_domain_prefix = domain_prefix[0] + '*' * (len(domain_prefix) - 2) + domain_prefix[-1]
    
    return f"{masked_username}@{masked_domain_prefix}.{domain_suffix}"

def get_safe_user_data(user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get safe user data for API responses.
    
    Args:
        user: User data
        
    Returns:
        Safe user data
    """
    return {
        "id": user.get("id", ""),
        "username": user.get("username", ""),
        "email": user.get("email", ""),
        "full_name": user.get("full_name", ""),
        "is_active": user.get("is_active", True),
        "is_admin": user.get("is_admin", False),
        "is_moderator": user.get("is_moderator", False),
        "created_at": user.get("created_at", ""),
        "last_login": user.get("last_login", "")
    }