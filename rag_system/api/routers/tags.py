"""
API endpoints for tag management.
"""
import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel

from ...database.document_store import get_db
from ...database.models import Tag, DocumentTag, Document
from ...auth.middleware import user_required, admin_required

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/tags",
    tags=["tags"],
    responses={404: {"description": "Not found"}},
)

# Models
class TagCreate(BaseModel):
    """Tag creation model."""
    name: str


class TagResponse(BaseModel):
    """Tag response model."""
    id: str
    name: str
    document_count: int


@router.get("", response_model=List[str])
async def get_all_tags(
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Get all available tags.
    """
    # Get all tags for the user's documents
    query = db.query(Tag.name).distinct()
    
    # If not admin, filter by user's documents
    if not token.get("is_admin"):
        query = query.join(DocumentTag, DocumentTag.tag_id == Tag.id)\
                    .join(Document, Document.id == DocumentTag.document_id)\
                    .filter(Document.user_id == token.get("user_id"))
    
    # Execute query
    tags = query.all()
    
    # Extract tag names
    tag_names = [tag[0] for tag in tags]
    
    return sorted(tag_names)


@router.get("/popular", response_model=List[TagResponse])
async def get_popular_tags(
    limit: int = Query(10, ge=1, le=100),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Get most popular tags with document counts.
    """
    # Build query
    query = db.query(
        Tag.id,
        Tag.name,
        func.count(DocumentTag.document_id).label("document_count")
    ).join(
        DocumentTag, DocumentTag.tag_id == Tag.id
    ).join(
        Document, Document.id == DocumentTag.document_id
    )
    
    # If not admin, filter by user's documents
    if not token.get("is_admin"):
        query = query.filter(Document.user_id == token.get("user_id"))
    
    # Group by tag and order by document count
    popular_tags = query.group_by(Tag.id, Tag.name)\
                        .order_by(desc("document_count"))\
                        .limit(limit)\
                        .all()
    
    # Format response
    result = []
    for tag_id, tag_name, doc_count in popular_tags:
        result.append({
            "id": tag_id,
            "name": tag_name,
            "document_count": doc_count
        })
    
    return result


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Create a new tag (admin only).
    """
    # Check if tag already exists
    existing_tag = db.query(Tag).filter(func.lower(Tag.name) == func.lower(tag_data.name)).first()
    
    if existing_tag:
        return {
            "id": existing_tag.id,
            "name": existing_tag.name,
            "message": "Tag already exists"
        }
    
    # Create new tag
    new_tag = Tag(name=tag_data.name)
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    
    return {
        "id": new_tag.id,
        "name": new_tag.name,
        "message": "Tag created successfully"
    }


@router.delete("/{tag_id}")
async def delete_tag(
    tag_id: str = Path(..., description="Tag ID"),
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Delete a tag (admin only).
    """
    # Get tag
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    # Delete tag associations first
    db.query(DocumentTag).filter(DocumentTag.tag_id == tag_id).delete()
    
    # Delete tag
    db.delete(tag)
    db.commit()
    
    return {"message": "Tag deleted successfully"}