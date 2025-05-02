"""
API dependencies.
"""
import logging
from typing import Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from ..database.document_store import get_db
from ..data_processing.vector_store_service import VectorStoreService
from ..generation.llm_service import LLMService
from ..integration.cache_manager import CacheManager
from ..config import settings

logger = logging.getLogger(__name__)

# Global services
_vector_store_service: Optional[VectorStoreService] = None
_llm_service: Optional[LLMService] = None
_cache_manager: Optional[CacheManager] = None

def get_vector_store_service(db: Session = Depends(get_db)) -> VectorStoreService:
    """
    Get vector store service.
    
    Args:
        db: Database session
        
    Returns:
        Vector store service
    """
    global _vector_store_service
    
    if _vector_store_service is None:
        _vector_store_service = VectorStoreService(
            db=db,
            index_path=settings.VECTOR_INDEX_PATH,
            dimension=settings.VECTOR_DIMENSION
        )
    
    return _vector_store_service

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
    global _llm_service
    
    if _llm_service is None:
        _llm_service = LLMService(
            db=db,
            vector_store=vector_store,
            model=settings.LLM_MODEL,
            provider=settings.LLM_PROVIDER
        )
    
    return _llm_service

def get_cache_manager() -> CacheManager:
    """
    Get cache manager.
    
    Returns:
        Cache manager
    """
    global _cache_manager
    
    if _cache_manager is None:
        cache_config = {
            "query_cache": {
                "ttl": settings.CACHE_TTL,
                "max_size": 1000
            },
            "document_cache": {
                "cache_dir": os.path.join(settings.UPLOAD_DIR, ".cache", "documents"),
                "ttl": settings.CACHE_TTL * 3,
                "max_size_mb": 512
            },
            "embedding_cache": {
                "use_disk_cache": True,
                "cache_dir": os.path.join(settings.UPLOAD_DIR, ".cache", "embeddings"),
                "ttl": settings.CACHE_TTL * 7
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
        }
        
        _cache_manager = CacheManager(config=cache_config)
    
    return _cache_manager