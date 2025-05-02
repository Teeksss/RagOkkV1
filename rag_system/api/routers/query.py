"""
API endpoints for querying with LLM.
"""
import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ...generation.llm_service import LLMService
from ...database.document_store import get_db
from ..dependencies import get_current_user, get_llm_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/query",
    tags=["query"],
    responses={404: {"description": "Not found"}},
)


class QueryRequest(BaseModel):
    """Query request model."""
    query: str = Field(..., description="User query")
    model: Optional[str] = Field(None, description="Model to use for generation")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters")


class SourceInfo(BaseModel):
    """Source information model."""
    id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    score: float = Field(..., description="Relevance score")


class QueryResponse(BaseModel):
    """Query response model."""
    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    sources: List[SourceInfo] = Field([], description="Source documents")
    model: str = Field(..., description="Model used")
    timing: float = Field(..., description="Processing time in seconds")


@router.post("/", response_model=QueryResponse)
def process_query(
    request: QueryRequest,
    user_id: str = Depends(get_current_user),
    llm_service: LLMService = Depends(get_llm_service),
    db: Session = Depends(get_db)
):
    """
    Process a query with retrieval and LLM generation.
    """
    # Add user filter
    filters = request.filters or {}
    filters["user_id"] = user_id
    
    try:
        # Process query
        result = llm_service.process_query(
            query=request.query,
            model_name=request.model,
            filters=filters
        )
        
        return result
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.get("/models")
def get_available_models(
    user_id: str = Depends(get_current_user),
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    Get available LLM models.
    """
    models = list(llm_service.clients.keys())
    default_model = llm_service.default_model
    
    return {
        "models": models,
        "default": default_model
    }