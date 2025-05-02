"""
Caching layer for query results.
"""
import logging
import json
import hashlib
import time
from typing import Dict, Any, Optional, List, Union
import redis

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, redis_url: str = "redis://localhost:6379/0",
                 default_ttl: int = 3600,
                 namespace: str = "rag:"):
        """
        Initialize cache manager.
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default TTL in seconds
            namespace: Key namespace
        """
        self.default_ttl = default_ttl
        self.namespace = namespace
        self.redis_client = None
        
        try:
            self.redis_client = redis.from_url(redis_url)
            logger.info(f"Connected to Redis at {redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self.redis_client:
            return None
        
        try:
            # Hash the key for consistent lookup
            hashed_key = self._hash_key(key)
            cache_key = f"{self.namespace}{hashed_key}"
            
            # Get from Redis
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                # Decode and deserialize
                return json.loads(cached_data.decode('utf-8'))
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting from cache: {str(e)}")
            return None
    
    def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (or default if None)
            
        Returns:
            Success status
        """
        if not self.redis_client:
            return False
        
        try:
            # Hash the key for consistent storage
            hashed_key = self._hash_key(key)
            cache_key = f"{self.namespace}{hashed_key}"
            
            # Serialize value
            serialized = json.dumps(value)
            
            # Set in Redis with TTL
            ttl_value = ttl if ttl is not None else self.default_ttl
            self.redis_client.setex(cache_key, ttl_value, serialized)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Success status
        """
        if not self.redis_client:
            return False
        
        try:
            # Hash the key for consistent lookup
            hashed_key = self._hash_key(key)
            cache_key = f"{self.namespace}{hashed_key}"
            
            # Delete from Redis
            self.redis_client.delete(cache_key)
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
            return False
    
    def flush_namespace(self) -> bool:
        """
        Flush all keys in the namespace.
        
        Returns:
            Success status
        """
        if not self.redis_client:
            return False
        
        try:
            # Get all keys in namespace
            pattern = f"{self.namespace}*"
            keys = self.redis_client.keys(pattern)
            
            # Delete all keys
            if keys:
                self.redis_client.delete(*keys)
            
            logger.info(f"Flushed {len(keys)} keys from namespace {self.namespace}")
            return True
            
        except Exception as e:
            logger.error(f"Error flushing namespace: {str(e)}")
            return False
    
    def _hash_key(self, key: str) -> str:
        """
        Hash a key for storage.
        
        Args:
            key: Original key
            
        Returns:
            Hashed key
        """
        return hashlib.md5(key.encode('utf-8')).hexdigest()


class QueryCache:
    def __init__(self, cache_manager: CacheManager, ttl: int = 3600):
        """
        Initialize query cache.
        
        Args:
            cache_manager: Cache manager
            ttl: TTL in seconds
        """
        self.cache = cache_manager
        self.ttl = ttl
    
    def get_search_results(self, query: str, 
                           filters: Optional[Dict[str, Any]] = None,
                           top_k: int = 5) -> Optional[Dict[str, Any]]:
        """
        Get cached search results.
        
        Args:
            query: Search query
            filters: Search filters
            top_k: Number of results
            
        Returns:
            Cached results or None
        """
        # Create cache key
        cache_key = self._create_search_key(query, filters, top_k)
        
        # Get from cache
        return self.cache.get(cache_key)
    
    def cache_search_results(self, query: str, 
                             filters: Optional[Dict[str, Any]],
                             top_k: int,
                             results: Dict[str, Any]) -> bool:
        """
        Cache search results.
        
        Args:
            query: Search query
            filters: Search filters
            top_k: Number of results
            results: Search results to cache
            
        Returns:
            Success status
        """
        # Create cache key
        cache_key = self._create_search_key(query, filters, top_k)
        
        # Add timestamp
        results["cached_at"] = time.time()
        
        # Set in cache
        return self.cache.set(cache_key, results, self.ttl)
    
    def _create_search_key(self, query: str, 
                          filters: Optional[Dict[str, Any]],
                          top_k: int) -> str:
        """
        Create a cache key for search results.
        
        Args:
            query: Search query
            filters: Search filters
            top_k: Number of results
            
        Returns:
            Cache key
        """
        # Normalize query
        normalized_query = query.lower().strip()
        
        # Convert filters to string
        filters_str = ""
        if filters:
            # Sort keys for consistent ordering
            sorted_filters = {k: filters[k] for k in sorted(filters.keys())}
            filters_str = json.dumps(sorted_filters)
        
        # Combine components
        return f"search:{normalized_query}:{filters_str}:{top_k}"