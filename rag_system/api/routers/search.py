"""
API endpoints for search functionality.
"""
import logging
import time
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ...database.document_store import get_db
from ...database.models import Document
from ...auth.middleware import user_required
from ...data_processing.vector_store_service import VectorStoreService
from ...utils.db_logger import DBLogger
from ..dependencies import get_vector_store_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/search",
    tags=["search"],
    responses={404: {"description": "Not found"}},
)

# Models
class SearchFilters(BaseModel):
    """Search filters model."""
    document_ids: Optional[List[str]] = None
    content_types: Optional[List[str]] = None
    date_range: Optional[Dict[str, str]] = None
    languages: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    custom_filters: Optional[Dict[str, Any]] = None


class SearchResult(BaseModel):
    """Search result model."""
    id: str
    content: str
    score: float
    document_id: str
    chunk_index: int
    metadata: Optional[Dict[str, Any]] = None
    document: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    """Search response model."""
    query: str
    results: List[SearchResult]
    total: int
    took: float


@router.get("/", response_model=SearchResponse)
async def search(
    query: str = Query(..., min_length=1, description="Search query"),
    k: int = Query(5, ge=1, le=100, description="Number of results"),
    filters: SearchFilters = None,
    use_cache: bool = Query(True, description="Whether to use cache"),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db),
    vector_store: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Search for documents based on query.
    """
    start_time = time.time()
    db_logger = DBLogger(db)
    
    try:
        # Prepare filters
        search_filters = {}
        
        if filters:
            # Only search user's documents
            if token.get("user_id"):
                search_filters["user_id"] = token.get("user_id")
            
            # Apply other filters
            if filters.document_ids:
                search_filters["document_id"] = filters.document_ids
            
            if filters.content_types:
                search_filters["content_type"] = filters.content_types
            
            if filters.languages:
                search_filters["language"] = filters.languages
            
            if filters.tags:
                search_filters["tags"] = filters.tags
            
            if filters.date_range:
                search_filters["date_range"] = filters.date_range
            
            if filters.custom_filters:
                search_filters.update(filters.custom_filters)
        else:
            # Default to only user's documents
            if token.get("user_id"):
                search_filters["user_id"] = token.get("user_id")
        
        # Perform search
        search_results = vector_store.search(
            query=query,
            k=k,
            filters=search_filters,
            use_cache=use_cache
        )
        
        # Format results
        results = []
        for result in search_results:
            # Ensure document info is included
            document_info = result.get("document", {})
            if "id" in result and not document_info:
                # Try to get document info from database
                document = db.query(Document).filter(Document.id == result["document_id"]).first()
                if document:
                    document_info = {
                        "id": document.id,
                        "filename": document.filename,
                        "title": document.metadata.get("title", document.filename) if document.metadata else document.filename
                    }
            
            results.append({
                "id": result.get("id", ""),
                "content": result.get("content", ""),
                "score": result.get("score", 0.0),
                "document_id": result.get("document_id", ""),
                "chunk_index": result.get("chunk_index", 0),
                "metadata": result.get("metadata", {}),
                "document": document_info
            })
        
        elapsed_time = time.time() - start_time
        
        # Log search
        db_logger.log_search(
            query=query,
            user_id=token.get("user_id"),
            result_count=len(results),
            latency=elapsed_time
        )
        
        return {
            "query": query,
            "results": results,
            "total": len(results),
            "took": elapsed_time
        }
    
    except Exception as e:
        elapsed_time = time.time() - start_time
        
        logger.error(f"Search error: {str(e)}")
        db_logger.log_error(
            operation="search",
            error_message=str(e),
            user_id=token.get("user_id"),
            latency=elapsed_time
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search error: {str(e)}"
        )


@router.get("/similar-documents/{document_id}")
async def find_similar_documents(
    document_id: str = Path(..., description="Document ID"),
    k: int = Query(5, ge=1, le=100, description="Number of results"),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db),
    vector_store: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Find documents similar to the specified document.
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
    
    # Get document embeddings
    embeddings_result = vector_store.get_document_embeddings(document_id)
    
    if embeddings_result.get("status") == "error":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=embeddings_result.get("error", "No embeddings found for document")
        )
    
    # Find similar documents
    similar_docs = {}
    
    # For each chunk, find similar documents
    for chunk in embeddings_result["chunks"]:
        # Search using chunk embedding
        search_results = vector_store.vector_index.search(
            query_vector=chunk["embedding"],
            k=k
        )
        
        # Collect unique documents
        for result in search_results:
            doc_id = result.get("metadata", {}).get("document_id")
            if doc_id and doc_id != document_id:
                if doc_id not in similar_docs:
                    similar_docs[doc_id] = {
                        "document_id": doc_id,
                        "score": result.get("score", 0),
                        "matching_chunks": []
                    }
                
                # Track matching chunks
                similar_docs[doc_id]["matching_chunks"].append({
                    "chunk_id": result.get("id"),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0)
                })
                
                # Use max score across chunks
                if result.get("score", 0) > similar_docs[doc_id]["score"]:
                    similar_docs[doc_id]["score"] = result.get("score", 0)
    
    # Convert to list and sort by score
    similar_docs_list = list(similar_docs.values())
    similar_docs_list.sort(key=lambda x: x["score"], reverse=True)
    
    # Limit to top k
    similar_docs_list = similar_docs_list[:k]
    
    # Add document info
    for doc in similar_docs_list:
        similar_document = db.query(Document).filter(Document.id == doc["document_id"]).first()
        if similar_document:
            doc["document"] = {
                "id": similar_document.id,
                "filename": similar_document.filename,
                "title": similar_document.metadata.get("title", similar_document.filename) if similar_document.metadata else similar_document.filename,
                "content_type": similar_document.content_type
            }
    
    return {
        "document_id": document_id,
        "similar_documents": similar_docs_list
    }


@router.get("/autocomplete")
async def autocomplete(
    query: str = Query(..., min_length=1, description="Partial query"),
    limit: int = Query(5, ge=1, le=20, description="Number of suggestions"),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Get query autocomplete suggestions.
    """
    # This is a simple implementation that could be enhanced with a proper autocomplete service
    
    # Get recent successful searches by this user
    recent_searches = db.query(
        DBLogger.data["query"].as_string()
    ).filter(
        DBLogger.operation == "search",
        DBLogger.user_id == token.get("user_id"),
        DBLogger.status_code == 200
    ).order_by(
        DBLogger.timestamp.desc()
    ).limit(100).all()
    
    # Extract queries
    queries = [row[0] for row in recent_searches if row[0]]
    
    # Filter by query prefix
    suggestions = [q for q in queries if q.lower().startswith(query.lower())]
    
    # Remove duplicates and limit results
    unique_suggestions = []
    for suggestion in suggestions:
        if suggestion not in unique_suggestions:
            unique_suggestions.append(suggestion)
            if len(unique_suggestions) >= limit:
                break
    
    return {"suggestions": unique_suggestions}