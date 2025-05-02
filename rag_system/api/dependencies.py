"""
API dependencies.
"""
from typing import Callable

from fastapi import Depends
from sqlalchemy.orm import Session

from ..database.document_store import get_db
from ..data_processing.vector_store_service import VectorStoreService
from ..generation.llm_service import LLMService
from ..integration.cache_manager import CacheManager
from ..config import settings

# Cache manager instance
cache_manager = CacheManager({
    "query_cache": {
        "ttl": settings.CACHE_TTL,
        "max_size": 1000
    },
    "document_cache": {
        "cache_dir": "./cache/documents",
        "ttl": 86400,
        "max_size_mb": 1024
    },
    "embedding_cache": {
        "use_disk_cache": True,
        "cache_dir": "./cache/embeddings",
        "ttl": 604800,  # 7 days
        "max_size_mb": 2048
    },
    "redis_cache": {
        "enabled": settings.CACHE_TYPE == "redis",
        "host": settings.REDIS_HOST,
        "port": settings.REDIS_PORT,
        "password": settings.REDIS_PASSWORD,
        "db": settings.REDIS_DB,
        "prefix": "rag:",
        "ttl": settings.CACHE_TTL
    }
})

def get_vector_store_service(db: Session = Depends(get_db)) -> VectorStoreService:
    """
    Get vector store service.
    
    Args:
        db: Database session
        
    Returns:
        Vector store service
    """
    return VectorStoreService(
        db=db,
        index_path=settings.VECTOR_INDEX_PATH,
        dimension=settings.VECTOR_DIMENSION
    )

def get_llm_service(
    db: Session = Depends(get_db),
    vector_store: VectorStoreService = Depends(get_vector_store_service)
) -> LLMService:
    """
    Get LLM service.
    
    Args:
        db: Database session
        vector_store: Vector store service
        
    Returns:
        LLM service
    """
    return LLMService(
        db=db,
        vector_store=vector_store,
        model=settings.LLM_MODEL,
        provider=settings.LLM_PROVIDER
    )

def get_cache_manager() -> CacheManager:
    """
    Get cache manager.
    
    Returns:
        Cache manager
    """
    return cache_manager