"""
Password hashing and verification.
"""
import logging
from typing import Tuple

from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# Create password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash password.
    
    Args:
        password: Plain password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password.
    
    Args:
        plain_password: Plain password
        hashed_password: Hashed password
        
    Returns:
        Whether password is correct
    """
    return pwd_context.verify(plain_password, hashed_password)


def generate_password_hash_with_salt(password: str) -> Tuple[str, str]:
    """
    Generate password hash with salt.
    
    Args:
        password: Plain password
        
    Returns:
        Tuple of (hash, salt)
    """
    hashed_password = hash_password(password)
    return hashed_password, "salt"  # In bcrypt, salt is included in the hash