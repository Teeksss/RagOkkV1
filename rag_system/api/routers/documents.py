"""
API endpoints for document management.
"""
import logging
import os
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from pydantic import BaseModel, Field

from ...database.document_store import get_db
from ...database.models import Document, DocumentChunk
from ...auth.middleware import user_required, admin_or_moderator
from ...data_ingestion.multilingual_processor import MultilingualDocumentProcessor
from ...data_processing.vector_store_service import VectorStoreService
from ...utils.db_logger import DBLogger
from ..dependencies import get_vector_store_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={404: {"description": "Not found"}},
)

# Models
class DocumentMetadata(BaseModel):
    """Document metadata model."""
    title: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    language: Optional[str] = None
    source: Optional[str] = None
    custom_metadata: Optional[Dict[str, Any]] = None


class DocumentCreate(BaseModel):
    """Document creation model."""
    filename: str
    metadata: Optional[DocumentMetadata] = None


class DocumentResponse(BaseModel):
    """Document response model."""
    id: str
    filename: str
    content_type: str
    file_size: int
    created_at: datetime
    processing_status: str
    metadata: Optional[Dict[str, Any]] = None


class DocumentUpdate(BaseModel):
    """Document update model."""
    metadata: DocumentMetadata


@router.post("/upload", response_model=Dict[str, Any])
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None,
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db),
    vector_store: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Upload a document.
    """
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join("uploads", token.get("user_id", "anonymous"))
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(upload_dir, filename)
    
    # Save uploaded file
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error saving file"
        )
    
    # Determine content type
    content_type = file.content_type or "application/octet-stream"
    
    # Prepare metadata
    metadata = {
        "title": title or file.filename,
        "description": description,
        "tags": tags.split(",") if tags else [],
        "language": language,
        "upload_date": datetime.now().isoformat()
    }
    
    # Create document record
    try:
        document = Document(
            user_id=token.get("user_id"),
            filename=file.filename,
            content_type=content_type,
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            created_at=datetime.now(),
            processing_status="pending",
            metadata=metadata
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Process document in background
        if background_tasks:
            # Initialize document processor
            document_processor = MultilingualDocumentProcessor(db)
            
            # Schedule processing task
            background_tasks.add_task(
                document_processor.process_document,
                document.id
            )
            
            # Update status to processing
            document.processing_status = "processing"
            db.commit()
        
        return {
            "status": "success",
            "message": "Document uploaded successfully",
            "document_id": document.id,
            "filename": document.filename
        }
    
    except Exception as e:
        logger.error(f"Error creating document record: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating document record: {str(e)}"
        )


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filter by processing status"),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    List documents.
    """
    # Build query
    query = db.query(Document).filter(
        Document.user_id == token.get("user_id"),
        Document.deleted == False
    )
    
    # Apply status filter
    if status:
        query = query.filter(Document.processing_status == status)
    
    # Get total count
    total_count = query.count()
    
    # Apply pagination and order
    documents = query.order_by(desc(Document.created_at)).offset(skip).limit(limit).all()
    
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str = Path(..., description="Document ID"),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Get document by ID.
    """
    # Get document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == token.get("user_id"),
        Document.deleted == False
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str = Path(..., description="Document ID"),
    document_update: DocumentUpdate = None,
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Update document metadata.
    """
    # Get document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == token.get("user_id"),
        Document.deleted == False
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Update metadata
    if document_update and document_update.metadata:
        # Get existing metadata
        current_metadata = document.metadata or {}
        
        # Convert Pydantic model to dict, excluding None values
        update_dict = document_update.metadata.dict(exclude_none=True)
        
        # Update metadata fields
        for key, value in update_dict.items():
            if key == "custom_metadata" and value:
                # Handle custom metadata separately to merge
                current_custom = current_metadata.get("custom_metadata", {})
                current_custom.update(value)
                current_metadata["custom_metadata"] = current_custom
            else:
                current_metadata[key] = value
        
        # Update document
        document.metadata = current_metadata
        document.last_updated_at = datetime.now()
        
        db.commit()
        db.refresh(document)
    
    return document


@router.delete("/{document_id}")
async def delete_document(
    document_id: str = Path(..., description="Document ID"),
    permanently: bool = Query(False, description="Whether to permanently delete"),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db),
    vector_store: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Delete document.
    """
    # Get document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == token.get("user_id")
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if permanently:
        # Get chunks
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).all()
        
        # Delete chunks from vector index
        chunk_ids = [chunk.id for chunk in chunks]
        if chunk_ids:
            # Remove from vector index
            vector_store.vector_index.delete(chunk_ids)
        
        # Delete file if it exists
        if document.file_path and os.path.exists(document.file_path):
            try:
                os.remove(document.file_path)
            except Exception as e:
                logger.warning(f"Error deleting file {document.file_path}: {str(e)}")
        
        # Delete from database
        db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).delete()
        
        db.delete(document)
    else:
        # Soft delete
        document.deleted = True
        document.last_updated_at = datetime.now()
    
    db.commit()
    
    return {"status": "success", "message": "Document deleted successfully"}


@router.get("/{document_id}/download")
async def download_document(
    document_id: str = Path(..., description="Document ID"),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Download document file.
    """
    # Get document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == token.get("user_id"),
        Document.deleted == False
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if file exists
    if not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found"
        )
    
    return FileResponse(
        document.file_path,
        filename=document.filename,
        media_type=document.content_type
    )


@router.get("/{document_id}/chunks")
async def get_document_chunks(
    document_id: str = Path(..., description="Document ID"),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Get document chunks.
    """
    # Get document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == token.get("user_id"),
        Document.deleted == False
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Get chunks
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).order_by(DocumentChunk.chunk_index).all()
    
    # Format response
    result = []
    for chunk in chunks:
        result.append({
            "id": chunk.id,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "metadata": chunk.metadata,
            "embedding_stored": chunk.embedding_stored
        })
    
    return result


@router.post("/{document_id}/reprocess")
async def reprocess_document(
    document_id: str = Path(..., description="Document ID"),
    background_tasks: BackgroundTasks = None,
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Reprocess document.
    """
    # Get document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == token.get("user_id"),
        Document.deleted == False
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if file exists
    if not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found"
        )
    
    # Update status to processing
    document.processing_status = "processing"
    db.commit()
    
    # Process document in background
    if background_tasks:
        # Initialize document processor
        document_processor = MultilingualDocumentProcessor(db)
        
        # Schedule processing task
        background_tasks.add_task(
            document_processor.process_document,
            document.id
        )
    
    return {"status": "success", "message": "Document reprocessing started"}


@router.get("/stats/overview")
async def get_document_stats(
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Get document statistics.
    """
    # Get user's document stats
    user_id = token.get("user_id")
    
    # Total documents
    total_documents = db.query(func.count(Document.id)).filter(
        Document.user_id == user_id,
        Document.deleted == False
    ).scalar() or 0
    
    # Documents by status
    status_counts = db.query(
        Document.processing_status,
        func.count(Document.id)
    ).filter(
        Document.user_id == user_id,
        Document.deleted == False
    ).group_by(Document.processing_status).all()
    
    status_stats = {status: count for status, count in status_counts}
    
    # Documents by type
    type_counts = db.query(
        Document.content_type,
        func.count(Document.id)
    ).filter(
        Document.user_id == user_id,
        Document.deleted == False
    ).group_by(Document.content_type).all()
    
    type_stats = {content_type: count for content_type, count in type_counts}
    
    # Total chunks
    total_chunks = db.query(func.count(DocumentChunk.id)).join(
        Document, DocumentChunk.document_id == Document.id
    ).filter(
        Document.user_id == user_id,
        Document.deleted == False
    ).scalar() or 0
    
    return {
        "total_documents": total_documents,
        "total_chunks": total_chunks,
        "status_counts": status_stats,
        "type_counts": type_stats
    }