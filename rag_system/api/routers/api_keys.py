"""
API endpoints for API key management.
"""
import logging
import secrets
import string
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel, Field

from ...database.document_store import get_db
from ...database.models import User, APIKey
from ...auth.middleware import admin_required, user_required
from ...utils.db_logger import DBLogger

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api-keys",
    tags=["api-keys"],
    responses={404: {"description": "Not found"}},
)

# Models
class APIKeyCreate(BaseModel):
    """API key creation model."""
    name: str = Field(..., min_length=1, max_length=64)
    expires_in_days: Optional[int] = Field(30, ge=1, le=365)
    scopes: List[str] = Field(default=["read"])


class APIKeyResponse(BaseModel):
    """API key response model."""
    id: str
    name: str
    prefix: str
    scopes: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_by: str


class APIKeyFullResponse(APIKeyResponse):
    """API key full response model with token."""
    token: str


def generate_api_key() -> str:
    """
    Generate a random API key.
    
    Returns:
        API key
    """
    # Format: prefix_random
    prefix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    
    return f"{prefix}_{random_part}"


@router.post("", response_model=APIKeyFullResponse)
async def create_api_key(
    api_key_data: APIKeyCreate,
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Create a new API key (admin only).
    """
    # Generate API key
    key_value = generate_api_key()
    prefix = key_value.split('_')[0]
    
    # Calculate expiration
    expires_at = None
    if api_key_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=api_key_data.expires_in_days)
    
    # Create API key record
    api_key = APIKey(
        name=api_key_data.name,
        key_hash=key_value,  # In a real application, you would hash this
        prefix=prefix,
        scopes=api_key_data.scopes,
        created_by=token.get("user_id"),
        created_at=datetime.utcnow(),
        expires_at=expires_at
    )
    
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    # Log API key creation
    db_logger = DBLogger(db)
    db_logger.log_info(
        operation="api_key_create",
        message=f"API key created: {api_key.name}",
        user_id=token.get("user_id"),
        data={"api_key_id": api_key.id, "prefix": prefix}
    )
    
    # Return API key with full token
    # NOTE: This is the only time the full token is returned
    return {
        "id": api_key.id,
        "name": api_key.name,
        "prefix": api_key.prefix,
        "scopes": api_key.scopes,
        "created_at": api_key.created_at,
        "expires_at": api_key.expires_at,
        "last_used_at": api_key.last_used_at,
        "created_by": api_key.created_by,
        "token": key_value
    }


@router.get("", response_model=List[APIKeyResponse])
async def list_api_keys(
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    List API keys (admin only).
    """
    # Get API keys
    api_keys = db.query(APIKey).filter(
        APIKey.created_by == token.get("user_id")
    ).order_by(desc(APIKey.created_at)).all()
    
    return api_keys


@router.delete("/{api_key_id}")
async def revoke_api_key(
    api_key_id: str = Path(..., description="API key ID"),
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Revoke an API key (admin only).
    """
    # Get API key
    api_key = db.query(APIKey).filter(
        APIKey.id == api_key_id,
        APIKey.created_by == token.get("user_id")
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Delete API key
    db.delete(api_key)
    db.commit()
    
    # Log API key revocation
    db_logger = DBLogger(db)
    db_logger.log_info(
        operation="api_key_revoke",
        message=f"API key revoked: {api_key.name}",
        user_id=token.get("user_id"),
        data={"api_key_id": api_key.id, "prefix": api_key.prefix}
    )
    
    return {"status": "success", "message": "API key revoked"}