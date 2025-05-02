"""
Password hashing and verification.
"""
import bcrypt

def get_password_hash(password: str) -> str:
    """
    Hash a password for storage.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    # Generate salt
    salt = bcrypt.gensalt()
    
    # Hash password
    hashed = bcrypt.hashpw(password.encode(), salt)
    
    return hashed.decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        True if password is correct, False otherwise
    """
    return bcrypt.checkpw(
        plain_password.encode(),
        hashed_password.encode()
    )