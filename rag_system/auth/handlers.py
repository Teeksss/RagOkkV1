"""
Authentication API handlers.
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator

from ..database.models import User
from ..database.document_store import get_db
from .password import get_password_hash, verify_password
from .jwt import create_tokens, Token, get_current_user, refresh_tokens, TokenRefresh

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


class UserCreate(BaseModel):
    """User registration model."""
    email: EmailStr
    password: str
    password_confirm: str
    name: Optional[str] = None
    
    @validator("password")
    def password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Şifre en az 8 karakter uzunluğunda olmalıdır")
        if not any(c.isupper() for c in v):
            raise ValueError("Şifre en az bir büyük harf içermelidir")
        if not any(c.islower() for c in v):
            raise ValueError("Şifre en az bir küçük harf içermelidir")
        if not any(c.isdigit() for c in v):
            raise ValueError("Şifre en az bir rakam içermelidir")
        return v
    
    @validator("password_confirm")
    def passwords_match(cls, v, values, **kwargs):
        """Validate that passwords match."""
        if "password" in values and v != values["password"]:
            raise ValueError("Şifreler eşleşmiyor")
        return v


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    name: Optional[str] = None
    role: str
    created_at: datetime
    last_login: Optional[datetime] = None


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu e-posta adresi zaten kullanılıyor",
        )
    
    # Create username from email
    username = user_data.email.split("@")[0]
    
    # Check if username exists
    existing_username = db.query(User).filter(User.username == username).first()
    if existing_username:
        # Append a random number if username exists
        import random
        username = f"{username}{random.randint(1, 9999)}"
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=username,
        hashed_password=hashed_password,
        name=user_data.name,
        role="user",  # Default role
        created_at=datetime.utcnow(),
    )
    
    # Save to database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"New user registered: {new_user.email}")
    
    return new_user


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login to get access token.
    """
    # Find user by username or email
    user = db.query(User).filter(
        (User.username == form_data.username) | (User.email == form_data.username)
    ).first()
    
    # Check if user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz kullanıcı adı veya şifre",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hesap etkin değil",
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create tokens
    tokens = create_tokens(user.id, user.username, user.role)
    
    return tokens


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get current user information.
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı",
        )
    
    return user


@router.post("/token/refresh", response_model=Token)
async def refresh_access_token(refresh_data: TokenRefresh, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token.
    """
    return refresh_tokens(refresh_data.refresh_token, db)