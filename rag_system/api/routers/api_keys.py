"""
API endpoints for API key management.
"""
import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator

from ...database.document_store import get_db
from ...database.models import APIKey, User
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
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)
    scopes: List[str] = Field(..., min_items=1)
    
    @validator('scopes')
    def validate_scopes(cls, v):
        """Validate scopes."""
        allowed_scopes = ['read', 'write', 'admin']
        for scope in v:
            if scope not in allowed_scopes:
                raise ValueError(f"Invalid scope: {scope}. Allowed scopes: {', '.join(allowed_scopes)}")
        return v


class APIKeyResponse(BaseModel):
    """API key response model."""
    id: str
    name: str
    prefix: str
    scopes: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None


@router.get("", response_model=List[APIKeyResponse])
async def list_api_keys(
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    List API keys for the current user.
    """
    # Get user's API keys
    api_keys = db.query(APIKey).filter(
        APIKey.created_by == token.get("user_id")
    ).all()
    
    # Format API keys
    result = []
    for key in api_keys:
        result.append({
            "id": key.id,
            "name": key.name,
            "prefix": key.prefix,
            "scopes": key.scopes,
            "created_at": key.created_at,
            "expires_at": key.expires_at,
            "last_used_at": key.last_used_at
        })
    
    return result


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Create a new API key.
    """
    # Check if user has permission to create keys with these scopes
    if "admin" in key_data.scopes and not token.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create keys with admin scope"
        )
    
    # Generate API key
    api_key = secrets.token_urlsafe(32)
    prefix = api_key[:16]
    
    # Hash API key (in a real production system, you'd use a more secure method)
    key_hash = f"hashed_{api_key}"
    
    # Calculate expiration date
    expires_at = None
    if key_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)
    
    # Create API key record
    new_key = APIKey(
        id=str(uuid.uuid4()),
        name=key_data.name,
        key_hash=key_hash,
        prefix=prefix,
        scopes=key_data.scopes,
        created_by=token.get("user_id"),
        created_at=datetime.utcnow(),
        expires_at=expires_at
    )
    
    db.add(new_key)
    db.commit()
    db.refresh(new_key)
    
    # Log API key creation
    db_logger = DBLogger(db)
    db_logger.log_info(
        operation="api_key_create",
        message=f"API key created: {new_key.name}",
        user_id=token.get("user_id"),
        data={
            "key_id": new_key.id,
            "scopes": new_key.scopes,
            "expires_at": expires_at.isoformat() if expires_at else None
        }
    )
    
    # Return key details with the actual key
    # The client should save this key as it won't be returned again
    return {
        "id": new_key.id,
        "name": new_key.name,
        "prefix": new_key.prefix,
        "token": api_key,  # Return the raw token only on creation
        "scopes": new_key.scopes,
        "created_at": new_key.created_at,
        "expires_at": new_key.expires_at
    }


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: str = Path(..., description="API key ID"),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Revoke an API key.
    """
    # Get API key
    query = db.query(APIKey).filter(APIKey.id == key_id)
    
    # If not admin, only allow user to revoke their own keys
    if not token.get("is_admin"):
        query = query.filter(APIKey.created_by == token.get("user_id"))
    
    api_key = query.first()
    
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
        data={
            "key_id": api_key.id,
            "name": api_key.name
        }
    )
    
    return {"message": "API key revoked successfully"}