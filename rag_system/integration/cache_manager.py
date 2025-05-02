"""
Cache manager for coordinating different caching mechanisms.
"""
import logging
import time
import json
import hashlib
from typing import Dict, Any, Optional, List, Union, Tuple, Callable
import threading
import os
import pickle
import numpy as np

from ..utils.caching import TTLCache, DiskCache, EmbeddingCache

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Manager for coordinating different caching mechanisms.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize cache manager.
        
        Args:
            config: Cache configuration
        """
        self.config = config or {}
        
        # Initialize caches
        self._initialize_caches()
    
    def _initialize_caches(self) -> None:
        """Initialize different cache types."""
        # Query cache (in-memory)
        query_config = self.config.get("query_cache", {})
        self.query_cache = TTLCache(
            ttl=query_config.get("ttl", 300),  # 5 minutes
            max_size=query_config.get("max_size", 1000)
        )
        
        # Embedding cache
        embedding_config = self.config.get("embedding_cache", {})
        self.embedding_cache = EmbeddingCache(
            use_disk_cache=embedding_config.get("use_disk_cache", False),
            cache_dir=embedding_config.get("cache_dir"),
            ttl=embedding_config.get("ttl", 86400 * 7),  # 1 week
            max_size=embedding_config.get("max_size", 10000)
        )
        
        # Document cache (disk-based)
        document_config = self.config.get("document_cache", {})
        self.document_cache = DiskCache(
            cache_dir=document_config.get("cache_dir", ".cache/documents"),
            ttl=document_config.get("ttl", 86400 * 3),  # 3 days
            max_size_mb=document_config.get("max_size_mb", 1024)  # 1 GB
        )
        
        # Redis cache (optional)
        redis_config = self.config.get("redis_cache", {})
        self.redis_enabled = redis_config.get("enabled", False)
        
        if self.redis_enabled:
            self._initialize_redis(redis_config)
    
    def _initialize_redis(self, redis_config: Dict[str, Any]) -> None:
        """
        Initialize Redis cache.
        
        Args:
            redis_config: Redis configuration
        """
        try:
            import redis
            
            self.redis = redis.Redis(
                host=redis_config.get("host", "localhost"),
                port=redis_config.get("port", 6379),
                db=redis_config.get("db", 0),
                password=redis_config.get("password"),
                decode_responses=False,  # Keep binary for pickle compatibility
                socket_timeout=redis_config.get("socket_timeout", 5),
                socket_connect_timeout=redis_config.get("socket_connect_timeout", 5)
            )
            
            self.redis_prefix = redis_config.get("prefix", "rag:")
            self.redis_ttl = redis_config.get("ttl", 3600)  # 1 hour
            
            # Test connection
            self.redis.ping()
            logger.info("Redis cache initialized successfully")
            
        except ImportError:
            logger.warning("Redis package not installed, Redis caching disabled")
            self.redis_enabled = False
        
        except Exception as e:
            logger.warning(f"Failed to initialize Redis cache: {str(e)}")
            self.redis_enabled = False
    
    def get_query_cache_key(self, query: str, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate cache key for query.
        
        Args:
            query: Query string
            params: Query parameters
            
        Returns:
            Cache key
        """
        # Create key parts
        key_parts = ["query", query]
        
        # Add params if provided
        if params:
            # Sort params for consistent keys
            param_str = json.dumps(params, sort_keys=True)
            key_parts.append(param_str)
        
        # Join parts
        key = ":".join(key_parts)
        
        # Hash if key is too long
        if len(key) > 250:
            key = hashlib.md5(key.encode()).hexdigest()
        
        return key
    
    def get_query_result(self, 
                       query: str, 
                       params: Optional[Dict[str, Any]] = None) -> Tuple[Any, bool]:
        """
        Get query result from cache.
        
        Args:
            query: Query string
            params: Query parameters
            
        Returns:
            Tuple of (result, hit status)
        """
        # Generate cache key
        cache_key = self.get_query_cache_key(query, params)
        
        # Check in-memory cache first
        result, hit = self.query_cache.get(cache_key)
        if hit:
            logger.debug(f"Query cache hit: {query}")
            return result, True
        
        # If Redis enabled, check Redis
        if self.redis_enabled:
            try:
                redis_key = f"{self.redis_prefix}query:{cache_key}"
                
                # Get from Redis
                redis_result = self.redis.get(redis_key)
                
                if redis_result:
                    # Deserialize result
                    result = pickle.loads(redis_result)
                    
                    # Also cache in memory for faster access next time
                    self.query_cache.put(cache_key, result)
                    
                    logger.debug(f"Redis query cache hit: {query}")
                    return result, True
            
            except Exception as e:
                logger.warning(f"Error accessing Redis cache: {str(e)}")
        
        return None, False
    
    def set_query_result(self, 
                        query: str, 
                        result: Any, 
                        params: Optional[Dict[str, Any]] = None,
                        ttl: Optional[int] = None) -> None:
        """
        Set query result in cache.
        
        Args:
            query: Query string
            result: Query result
            params: Query parameters
            ttl: Time-to-live in seconds
        """
        # Generate cache key
        cache_key = self.get_query_cache_key(query, params)
        
        # Set in-memory cache
        self.query_cache.put(cache_key, result, ttl)
        
        # If Redis enabled, set in Redis too
        if self.redis_enabled:
            try:
                redis_key = f"{self.redis_prefix}query:{cache_key}"
                
                # Serialize result
                serialized = pickle.dumps(result)
                
                # Set in Redis
                self.redis.set(
                    redis_key,
                    serialized,
                    ex=ttl if ttl is not None else self.redis_ttl
                )
            
            except Exception as e:
                logger.warning(f"Error setting Redis cache: {str(e)}")
    
    def get_embedding(self, 
                    text: str, 
                    model_name: str = "default") -> Tuple[Optional[np.ndarray], bool]:
        """
        Get embedding from cache.
        
        Args:
            text: Input text
            model_name: Model name
            
        Returns:
            Tuple of (embedding, hit status)
        """
        return self.embedding_cache.get(text, model_name)
    
    def set_embedding(self, 
                    text: str, 
                    embedding: np.ndarray, 
                    model_name: str = "default") -> None:
        """
        Set embedding in cache.
        
        Args:
            text: Input text
            embedding: Embedding vector
            model_name: Model name
        """
        self.embedding_cache.put(text, embedding, model_name)
    
    def get_document(self, document_id: str) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Get document from cache.
        
        Args:
            document_id: Document ID
            
        Returns:
            Tuple of (document, hit status)
        """
        # Generate cache key
        cache_key = f"document:{document_id}"
        
        # Get from cache
        return self.document_cache.get(cache_key)
    
    def set_document(self, 
                   document_id: str, 
                   document: Dict[str, Any], 
                   ttl: Optional[int] = None) -> None:
        """
        Set document in cache.
        
        Args:
            document_id: Document ID
            document: Document data
            ttl: Time-to-live in seconds
        """
        # Generate cache key
        cache_key = f"document:{document_id}"
        
        # Set in cache
        self.document_cache.put(cache_key, document, ttl)
    
    def invalidate_query_cache(self, query_pattern: Optional[str] = None) -> None:
        """
        Invalidate query cache.
        
        Args:
            query_pattern: Optional query pattern to match (None for all)
        """
        # If no pattern, clear entire cache
        if query_pattern is None:
            self.query_cache.clear()
            
            # Clear Redis if enabled
            if self.redis_enabled:
                try:
                    # Delete all keys matching prefix
                    for key in self.redis.scan_iter(f"{self.redis_prefix}query:*"):
                        self.redis.delete(key)
                except Exception as e:
                    logger.warning(f"Error clearing Redis cache: {str(e)}")
        
        else:
            # TODO: Implement selective invalidation based on pattern
            # This is complex with current implementation, so we'll just clear all for now
            logger.warning("Selective cache invalidation not implemented, clearing all query cache")
            self.invalidate_query_cache()
    
    def invalidate_document_cache(self, document_id: Optional[str] = None) -> None:
        """
        Invalidate document cache.
        
        Args:
            document_id: Optional document ID (None for all)
        """
        if document_id is None:
            # Clear entire cache
            self.document_cache.clear()
        else:
            # Delete specific document
            cache_key = f"document:{document_id}"
            self.document_cache.delete(cache_key)
    
    def invalidate_embedding_cache(self) -> None:
        """Invalidate embedding cache."""
        self.embedding_cache.clear()
    
    def get_redis(self) -> Any:
        """
        Get Redis client.
        
        Returns:
            Redis client or None
        """
        if self.redis_enabled:
            return self.redis
        return None
    
    def is_redis_available(self) -> bool:
        """
        Check if Redis is available.
        
        Returns:
            Whether Redis is available
        """
        if not self.redis_enabled:
            return False
        
        try:
            self.redis.ping()
            return True
        except:
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Cache statistics
        """
        stats = {
            "query_cache": {
                "size": len(self.query_cache.cache),
                "max_size": self.query_cache.max_size,
                "ttl": self.query_cache.ttl
            },
            "redis_enabled": self.redis_enabled
        }
        
        # Add Redis stats if enabled
        if self.redis_enabled:
            try:
                info = self.redis.info()
                stats["redis"] = {
                    "used_memory_human": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients"),
                    "uptime_in_seconds": info.get("uptime_in_seconds")
                }
            except:
                stats["redis"] = {"status": "error"}
        
        return stats