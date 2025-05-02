"""
API endpoints for document version management.
"""
import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, Query, Path, Body, HTTPException, status, BackgroundTasks, UploadFile, File
from sqlalchemy.orm import Session

from ...database.document_store import get_db
from ...auth.middleware import user_required, admin_or_moderator
from ...document_management.versioning import DocumentVersionManager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documents/{document_id}/versions",
    tags=["document-versions"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
async def list_versions(
    document_id: str = Path(..., description="Document ID"),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    List all versions of a document.
    """
    version_manager = DocumentVersionManager(db)
    result = version_manager.list_versions(document_id)
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    
    return result

@router.get("/{version}")
async def get_version(
    document_id: str = Path(..., description="Document ID"),
    version: int = Path(..., description="Version number"),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Get a specific version of a document.
    """
    version_manager = DocumentVersionManager(db)
    result = version_manager.get_version(document_id, version)
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    
    return result

@router.post("/")
async def create_version(
    document_id: str = Path(..., description="Document ID"),
    content: str = Body(..., description="Document content"),
    metadata: Optional[Dict[str, Any]] = Body(None, description="Document metadata"),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Create a new version of a document.
    """
    version_manager = DocumentVersionManager(db)
    result = version_manager.create_version(
        document_id=document_id,
        content=content,
        metadata=metadata,
        created_by=token.get("user_id")
    )
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    
    return result

@router.post("/upload")
async def upload_new_version(
    document_id: str = Path(..., description="Document ID"),
    file: UploadFile = File(...),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Upload a new version of a document.
    """
    # Read file content
    content = await file.read()
    
    # Convert bytes to string (assuming text content)
    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError:
        # Binary file, return error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only text files are supported for versioning"
        )
    
    # Create version
    version_manager = DocumentVersionManager(db)
    result = version_manager.create_version(
        document_id=document_id,
        content=text_content,
        metadata={"filename": file.filename},
        created_by=token.get("user_id")
    )
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    
    return result

@router.get("/compare")
async def compare_versions(
    document_id: str = Path(..., description="Document ID"),
    version1: int = Query(..., description="First version number"),
    version2: int = Query(..., description="Second version number"),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Compare two versions of a document.
    """
    version_manager = DocumentVersionManager(db)
    result = version_manager.compare_versions(document_id, version1, version2)
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    
    return result

@router.post("/revert/{version}")
async def revert_to_version(
    document_id: str = Path(..., description="Document ID"),
    version: int = Path(..., description="Version to revert to"),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Revert a document to a previous version.
    """
    version_manager = DocumentVersionManager(db)
    result = version_manager.revert_to_version(
        document_id=document_id,
        version_number=version,
        user_id=token.get("user_id")
    )
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    
    return result

@router.get("/history")
async def get_document_history(
    document_id: str = Path(..., description="Document ID"),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Get complete history of a document including versions and changes.
    """
    version_manager = DocumentVersionManager(db)
    result = version_manager.get_document_history(document_id)
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    
    return result