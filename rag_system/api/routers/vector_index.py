"""
API endpoints for vector index management.
"""
import logging
import time
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ...database.document_store import get_db
from ...auth.middleware import admin_required, admin_or_moderator, user_required
from ...data_processing.vector_store_service import VectorStoreService
from ...data_processing.advanced_vector_index import FAISSConfigFactory
from ..dependencies import get_vector_store_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/vector-index",
    tags=["vector-index"],
    responses={404: {"description": "Not found"}},
)

# Models
class IndexConfig(BaseModel):
    """Vector index configuration model."""
    index_type: str = Field(..., description="Index type (flat, ivf, hnsw)")
    metric: str = Field("cosine", description="Distance metric")
    parameters: Dict[str, Any] = Field({}, description="Index parameters")


class VectorSearchPayload(BaseModel):
    """Vector search payload model."""
    vector: List[float] = Field(..., description="Query vector")
    k: int = Field(5, ge=1, le=100, description="Number of results")
    filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")


@router.get("/info")
async def get_index_info(
    token: Dict[str, Any] = Depends(user_required),
    vector_store: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Get vector index information.
    """
    # Get index info
    info = vector_store.vector_index.get_index_info()
    
    return info


@router.get("/configs")
async def get_available_configs(
    token: Dict[str, Any] = Depends(user_required)
):
    """
    Get available vector index configurations.
    """
    # Get config factory
    config_factory = FAISSConfigFactory()
    
    # Get available configs
    configs = config_factory.get_available_configs()
    
    return {
        "available_configs": configs
    }


@router.post("/configs/recommended")
async def get_recommended_config(
    dimension: int = Body(..., ge=32, le=4096, description="Vector dimension"),
    dataset_size: int = Body(..., ge=100, description="Estimated dataset size"),
    token: Dict[str, Any] = Depends(user_required)
):
    """
    Get recommended vector index configuration.
    """
    # Get config factory
    config_factory = FAISSConfigFactory()
    
    # Get recommended config
    config = config_factory.get_recommended_config(
        dimension=dimension,
        dataset_size=dataset_size
    )
    
    return {
        "recommended_config": config
    }


@router.post("/rebuild")
async def rebuild_index(
    config: IndexConfig,
    token: Dict[str, Any] = Depends(admin_required),
    vector_store: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Rebuild vector index with new configuration.
    """
    # Rebuild index
    result = vector_store.rebuild_index_with_config({
        "index_type": config.index_type,
        "metric": config.metric,
        "parameters": config.parameters
    })
    
    return result


@router.post("/search")
async def search_by_vector(
    payload: VectorSearchPayload,
    token: Dict[str, Any] = Depends(user_required),
    vector_store: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Search by vector.
    """
    # Perform search
    results = vector_store.vector_index.search(
        query_vector=payload.vector,
        k=payload.k,
        filters=payload.filters
    )
    
    # Add document info
    db = next(get_db())
    
    for result in results:
        # Try to get document info from metadata
        document_id = result.get("metadata", {}).get("document_id")
        
        if document_id:
            # Check if user has access to this document
            document = db.query(Document).filter(
                Document.id == document_id,
                Document.user_id == token.get("user_id"),
                Document.deleted == False
            ).first()
            
            if document:
                result["document"] = {
                    "id": document.id,
                    "filename": document.filename,
                    "title": document.metadata.get("title", document.filename) if document.metadata else document.filename
                }
    
    return {
        "results": results
    }


@router.post("/optimize")
async def optimize_index(
    sample_size: int = Body(1000, ge=100, le=10000, description="Sample size for optimization"),
    token: Dict[str, Any] = Depends(admin_required),
    vector_store: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Optimize vector index configuration.
    """
    # Optimize index
    result = vector_store.optimize_index_config(sample_size=sample_size)
    
    return result


@router.get("/stats")
async def get_index_stats(
    token: Dict[str, Any] = Depends(admin_or_moderator),
    vector_store: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Get vector index statistics.
    """
    # Get index stats
    stats = vector_store.vector_index.get_stats()
    
    return stats


@router.post("/save")
async def save_index(
    filename: Optional[str] = Body(None, description="Index filename"),
    token: Dict[str, Any] = Depends(admin_required),
    vector_store: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Save vector index to disk.
    """
    # Save index
    saved_path = vector_store.save_index(filename)
    
    return {
        "status": "success",
        "path": saved_path
    }


@router.post("/load")
async def load_index(
    filename: str = Body(..., description="Index filename"),
    token: Dict[str, Any] = Depends(admin_required),
    vector_store: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Load vector index from disk.
    """
    # Load index
    success = vector_store.load_index(filename)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to load index"
        )
    
    return {
        "status": "success",
        "message": f"Loaded index from {filename}"
    }


@router.post("/convert-to-sharded")
async def convert_to_sharded_index(
    num_shards: int = Body(4, ge=2, le=16, description="Number of shards"),
    token: Dict[str, Any] = Depends(admin_required),
    vector_store: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Convert index to sharded index.
    """
    # Convert to sharded index
    result = vector_store.convert_to_sharded_index(num_shards=num_shards)
    
    return result