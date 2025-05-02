"""
Caching utilities for improved performance.
"""
import logging
import time
import json
import hashlib
import os
import pickle
from typing import Dict, Any, Optional, Callable, TypeVar, cast
from functools import wraps, lru_cache
import threading
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)

# Type variables for generics
T = TypeVar('T')
R = TypeVar('R')

class TTLCache:
    """
    Time-to-live (TTL) cache.
    """
    
    def __init__(self, ttl: int = 3600, max_size: int = 1000):
        """
        Initialize TTL cache.
        
        Args:
            ttl: Time-to-live in seconds
            max_size: Maximum cache size
        """
        self.ttl = ttl
        self.max_size = max_size
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
    
    def get(self, key: str) -> tuple[Any, bool]:
        """
        Get item from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Tuple of (cached value, hit status)
        """
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                # Check if entry has expired
                if entry["expiry"] > time.time():
                    return entry["value"], True
                else:
                    # Remove expired entry
                    del self.cache[key]
            
            return None, False
    
    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Put item in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional custom TTL
        """
        with self.lock:
            # Check if cache is full and evict if necessary
            if len(self.cache) >= self.max_size:
                self._evict_oldest()
            
            # Set expiry time
            expiry = time.time() + (ttl if ttl is not None else self.ttl)
            
            # Add to cache
            self.cache[key] = {
                "value": value,
                "expiry": expiry,
                "created": time.time()
            }
    
    def delete(self, key: str) -> bool:
        """
        Delete item from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Whether key was deleted
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
    
    def _evict_oldest(self) -> None:
        """Evict oldest cache entry."""
        with self.lock:
            if not self.cache:
                return
            
            # Find oldest entry
            oldest_key = min(self.cache, key=lambda k: self.cache[k]["created"])
            
            # Remove oldest entry
            del self.cache[oldest_key]
    
    def _cleanup_loop(self) -> None:
        """Background thread for cleaning up expired entries."""
        while True:
            time.sleep(60)  # Check every minute
            self._cleanup_expired()
    
    def _cleanup_expired(self) -> None:
        """Clean up expired cache entries."""
        try:
            with self.lock:
                now = time.time()
                # Find expired keys
                expired_keys = [
                    key for key, entry in self.cache.items()
                    if entry["expiry"] <= now
                ]
                
                # Remove expired entries
                for key in expired_keys:
                    del self.cache[key]
                
                if expired_keys:
                    logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
        except Exception as e:
            logger.error(f"Error during cache cleanup: {str(e)}")


class DiskCache:
    """
    Disk-based cache for larger objects.
    """
    
    def __init__(self, cache_dir: str = ".cache", ttl: int = 86400, max_size_mb: int = 1024):
        """
        Initialize disk cache.
        
        Args:
            cache_dir: Cache directory
            ttl: Time-to-live in seconds
            max_size_mb: Maximum cache size in MB
        """
        self.cache_dir = cache_dir
        self.ttl = ttl
        self.max_size_mb = max_size_mb
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Create index file
        self.index_path = os.path.join(cache_dir, "index.json")
        if not os.path.exists(self.index_path):
            self._save_index({})
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
    
    def get(self, key: str) -> tuple[Any, bool]:
        """
        Get item from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Tuple of (cached value, hit status)
        """
        # Get safe filename
        safe_key = self._get_safe_key(key)
        file_path = os.path.join(self.cache_dir, f"{safe_key}.pkl")
        
        # Load index
        index = self._load_index()
        
        # Check if key exists in index
        if safe_key in index:
            entry = index[safe_key]
            
            # Check if entry has expired
            if entry["expiry"] > time.time():
                # Check if file exists
                if os.path.exists(file_path):
                    try:
                        # Load cached value
                        with open(file_path, "rb") as f:
                            value = pickle.load(f)
                        
                        return value, True
                    except Exception as e:
                        logger.warning(f"Error loading cached value: {str(e)}")
                        # Remove corrupted entry
                        self._remove_entry(safe_key)
                else:
                    # Remove entry if file doesn't exist
                    self._remove_entry(safe_key)
            else:
                # Remove expired entry
                self._remove_entry(safe_key)
        
        return None, False
    
    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Put item in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional custom TTL
        """
        # Get safe filename
        safe_key = self._get_safe_key(key)
        file_path = os.path.join(self.cache_dir, f"{safe_key}.pkl")
        
        # Set expiry time
        expiry = time.time() + (ttl if ttl is not None else self.ttl)
        
        try:
            # Save value to file
            with open(file_path, "wb") as f:
                pickle.dump(value, f)
            
            # Update index
            index = self._load_index()
            index[safe_key] = {
                "key": key,
                "expiry": expiry,
                "created": time.time(),
                "size": os.path.getsize(file_path)
            }
            self._save_index(index)
            
            # Check if cache is over size limit
            self._enforce_size_limit()
        
        except Exception as e:
            logger.error(f"Error caching value: {str(e)}")
    
    def delete(self, key: str) -> bool:
        """
        Delete item from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Whether key was deleted
        """
        # Get safe filename
        safe_key = self._get_safe_key(key)
        
        # Remove entry
        return self._remove_entry(safe_key)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        # Load index
        index = self._load_index()
        
        # Delete all cache files
        for safe_key in list(index.keys()):
            self._remove_entry(safe_key)
    
    def _get_safe_key(self, key: str) -> str:
        """
        Convert key to safe filename.
        
        Args:
            key: Cache key
            
        Returns:
            Safe filename
        """
        return hashlib.md5(key.encode()).hexdigest()
    
    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        """
        Load cache index.
        
        Returns:
            Cache index
        """
        try:
            with open(self.index_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading cache index: {str(e)}")
            return {}
    
    def _save_index(self, index: Dict[str, Dict[str, Any]]) -> None:
        """
        Save cache index.
        
        Args:
            index: Cache index
        """
        try:
            with open(self.index_path, "w") as f:
                json.dump(index, f)
        except Exception as e:
            logger.error(f"Error saving cache index: {str(e)}")
    
    def _remove_entry(self, safe_key: str) -> bool:
        """
        Remove cache entry.
        
        Args:
            safe_key: Safe key
            
        Returns:
            Whether entry was removed
        """
        # Load index
        index = self._load_index()
        
        # Check if key exists
        if safe_key not in index:
            return False
        
        # Remove file
        file_path = os.path.join(self.cache_dir, f"{safe_key}.pkl")
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Error removing cache file: {str(e)}")
        
        # Remove from index
        del index[safe_key]
        self._save_index(index)
        
        return True
    
    def _enforce_size_limit(self) -> None:
        """Enforce cache size limit."""
        # Load index
        index = self._load_index()
        
        # Calculate total size
        total_size_bytes = sum(entry.get("size", 0) for entry in index.values())
        total_size_mb = total_size_bytes / (1024 * 1024)
        
        # Check if over limit
        if total_size_mb > self.max_size_mb:
            # Sort entries by age (oldest first)
            sorted_entries = sorted(
                index.items(),
                key=lambda item: item[1]["created"]
            )
            
            # Remove entries until under limit
            for safe_key, _ in sorted_entries:
                self._remove_entry(safe_key)
                
                # Recalculate size
                index = self._load_index()
                total_size_bytes = sum(entry.get("size", 0) for entry in index.values())
                total_size_mb = total_size_bytes / (1024 * 1024)
                
                if total_size_mb <= self.max_size_mb:
                    break
    
    def _cleanup_loop(self) -> None:
        """Background thread for cleaning up expired entries."""
        while True:
            time.sleep(3600)  # Check every hour
            self._cleanup_expired()
    
    def _cleanup_expired(self) -> None:
        """Clean up expired cache entries."""
        try:
            # Load index
            index = self._load_index()
            now = time.time()
            
            # Find expired keys
            expired_keys = [
                safe_key for safe_key, entry in index.items()
                if entry["expiry"] <= now
            ]
            
            # Remove expired entries
            for safe_key in expired_keys:
                self._remove_entry(safe_key)
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired disk cache entries")
        
        except Exception as e:
            logger.error(f"Error during disk cache cleanup: {str(e)}")


def memoize(ttl: int = 3600, max_size: int = 1000):
    """
    Decorator for memoizing function results.
    
    Args:
        ttl: Time-to-live in seconds
        max_size: Maximum cache size
    """
    cache = TTLCache(ttl=ttl, max_size=max_size)
    
    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> R:
            # Generate cache key from function name and arguments
            key_parts = [func.__name__]
            
            # Add positional args
            for arg in args:
                key_parts.append(str(arg))
            
            # Add keyword args (sorted for consistency)
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")
            
            # Create cache key
            cache_key = ":".join(key_parts)
            
            # Check cache
            cached_value, hit = cache.get(cache_key)
            if hit:
                return cast(R, cached_value)
            
            # Calculate result
            result = func(*args, **kwargs)
            
            # Cache result
            cache.put(cache_key, result)
            
            return result
        
        # Add cache control functions
        wrapper.cache_clear = cache.clear  # type: ignore
        wrapper.cache_delete = cache.delete  # type: ignore
        
        return wrapper
    
    return decorator


def vector_cache(ttl: int = 3600, cache_dir: Optional[str] = None):
    """
    Decorator for caching vector search results.
    
    Args:
        ttl: Time-to-live in seconds
        cache_dir: Optional disk cache directory
    """
    # Use disk cache if directory provided, otherwise use memory cache
    if cache_dir:
        cache = DiskCache(cache_dir=cache_dir, ttl=ttl)
    else:
        cache = TTLCache(ttl=ttl)
    
    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> R:
            # Skip caching if explicitly disabled
            if kwargs.get("use_cache") is False:
                return func(*args, **kwargs)
            
            # Generate cache key
            key_parts = [func.__name__]
            
            # Find query parameter
            query = None
            if len(args) > 1:
                query = args[1]  # Assuming query is the second argument
            elif "query" in kwargs:
                query = kwargs["query"]
            
            if query is None:
                # Can't determine query, skip caching
                return func(*args, **kwargs)
            
            # Add query to key parts
            key_parts.append(str(query))
            
            # Add other key parameters
            k = kwargs.get("k", 5)
            key_parts.append(f"k={k}")
            
            # Add filters if present
            filters = kwargs.get("filters")
            if filters:
                # Sort filters for consistent keys
                try:
                    filter_str = json.dumps(filters, sort_keys=True)
                    key_parts.append(f"filters={filter_str}")
                except:
                    # Skip filters if not serializable
                    key_parts.append("filters=complex")
            
            # Create cache key
            cache_key = ":".join(key_parts)
            
            # Check cache
            cached_value, hit = cache.get(cache_key)
            if hit:
                logger.debug(f"Vector cache hit for query: {query}")
                return cast(R, cached_value)
            
            # Calculate result
            result = func(*args, **kwargs)
            
            # Cache result
            cache.put(cache_key, result)
            
            return result
        
        # Add cache control functions
        wrapper.cache_clear = cache.clear  # type: ignore
        wrapper.cache_delete = cache.delete  # type: ignore
        
        return wrapper
    
    return decorator


@lru_cache(maxsize=1024)
def get_embedding_cache_key(text: str) -> str:
    """
    Get embedding cache key for text.
    
    Args:
        text: Input text
        
    Returns:
        Cache key
    """
    # Generate hash of normalized text
    text = text.strip().lower()
    return hashlib.sha256(text.encode()).hexdigest()


class EmbeddingCache:
    """
    Cache for embeddings.
    """
    
    def __init__(self, 
                 use_disk_cache: bool = False, 
                 cache_dir: Optional[str] = None,
                 ttl: int = 86400 * 30,  # 30 days
                 max_size: int = 10000):
        """
        Initialize embedding cache.
        
        Args:
            use_disk_cache: Whether to use disk cache
            cache_dir: Cache directory (required if use_disk_cache is True)
            ttl: Time-to-live in seconds
            max_size: Maximum cache size
        """
        self.use_disk_cache = use_disk_cache
        
        if use_disk_cache:
            if not cache_dir:
                cache_dir = ".cache/embeddings"
            
            self.cache = DiskCache(cache_dir=cache_dir, ttl=ttl)
        else:
            self.cache = TTLCache(ttl=ttl, max_size=max_size)
    
    def get(self, text: str, model_name: str = "default") -> tuple[Optional[np.ndarray], bool]:
        """
        Get embedding from cache.
        
        Args:
            text: Input text
            model_name: Model name
            
        Returns:
            Tuple of (embedding, hit status)
        """
        # Generate cache key
        text_key = get_embedding_cache_key(text)
        cache_key = f"{model_name}:{text_key}"
        
        # Check cache
        cached_value, hit = self.cache.get(cache_key)
        
        return cached_value, hit
    
    def put(self, text: str, embedding: np.ndarray, model_name: str = "default") -> None:
        """
        Put embedding in cache.
        
        Args:
            text: Input text
            embedding: Embedding vector
            model_name: Model name
        """
        # Generate cache key
        text_key = get_embedding_cache_key(text)
        cache_key = f"{model_name}:{text_key}"
        
        # Store in cache
        self.cache.put(cache_key, embedding)
    
    def clear(self) -> None:
        """Clear cache."""
        self.cache.clear()