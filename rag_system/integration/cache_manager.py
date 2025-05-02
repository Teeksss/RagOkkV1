"""
Cache manager for different caching strategies.
"""
import logging
import os
import time
import json
import pickle
from typing import Dict, Any, Optional, Union, Generic, TypeVar, Callable
import hashlib

logger = logging.getLogger(__name__)

# Type variables
T = TypeVar('T')


class MemoryCache:
    """
    In-memory cache.
    """
    
    def __init__(self, ttl: int = 3600, max_size: int = 1000):
        """
        Initialize memory cache.
        
        Args:
            ttl: Time-to-live in seconds
            max_size: Maximum cache size
        """
        self.ttl = ttl
        self.max_size = max_size
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, key: str) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if key in self._cache:
            # Check if expired
            if self._cache[key]["expires_at"] < time.time():
                # Remove expired entry
                del self._cache[key]
                return None
            
            # Return value
            return self._cache[key]["value"]
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (overrides default)
        """
        # Prune cache if needed
        if len(self._cache) >= self.max_size:
            self._prune_cache()
        
        # Set value
        self._cache[key] = {
            "value": value,
            "expires_at": time.time() + (ttl or self.ttl)
        }
    
    def delete(self, key: str) -> None:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
        """
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """Clear cache."""
        self._cache.clear()
    
    def _prune_cache(self) -> None:
        """Prune cache by removing expired and oldest entries."""
        # Remove expired entries
        current_time = time.time()
        expired_keys = [
            k for k, v in self._cache.items() 
            if v["expires_at"] < current_time
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        # If still too large, remove oldest entries
        if len(self._cache) >= self.max_size:
            # Sort by expiration time
            sorted_items = sorted(
                self._cache.items(), 
                key=lambda x: x[1]["expires_at"]
            )
            
            # Remove oldest 20%
            num_to_remove = int(len(sorted_items) * 0.2)
            for key, _ in sorted_items[:num_to_remove]:
                del self._cache[key]


class DiskCache:
    """
    Disk-based cache.
    """
    
    def __init__(self, 
                cache_dir: str = "./cache", 
                ttl: int = 86400, 
                max_size_mb: int = 1024):
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
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
    
    def get(self, key: str) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        # Generate file path
        file_path = self._get_file_path(key)
        
        if not os.path.exists(file_path):
            return None
        
        try:
            # Check if expired
            if self._is_expired(file_path):
                # Remove expired file
                os.remove(file_path)
                return None
            
            # Read file
            with open(file_path, "rb") as f:
                value = pickle.load(f)
            
            return value
        
        except Exception as e:
            logger.error(f"Error reading from disk cache: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (overrides default)
        """
        # Prune cache if needed
        if self._get_cache_size_mb() > self.max_size_mb:
            self._prune_cache()
        
        # Generate file path
        file_path = self._get_file_path(key)
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write file
            with open(file_path, "wb") as f:
                pickle.dump(value, f)
            
            # Set expiration time
            expiration_time = time.time() + (ttl or self.ttl)
            with open(f"{file_path}.meta", "w") as f:
                json.dump({"expires_at": expiration_time}, f)
        
        except Exception as e:
            logger.error(f"Error writing to disk cache: {str(e)}")
    
    def delete(self, key: str) -> None:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
        """
        # Generate file path
        file_path = self._get_file_path(key)
        
        try:
            # Remove files
            if os.path.exists(file_path):
                os.remove(file_path)
            
            if os.path.exists(f"{file_path}.meta"):
                os.remove(f"{file_path}.meta")
        
        except Exception as e:
            logger.error(f"Error deleting from disk cache: {str(e)}")
    
    def clear(self) -> None:
        """Clear cache."""
        try:
            # Remove all files in cache directory
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    os.remove(os.path.join(root, file))
        
        except Exception as e:
            logger.error(f"Error clearing disk cache: {str(e)}")
    
    def _get_file_path(self, key: str) -> str:
        """
        Get file path for key.
        
        Args:
            key: Cache key
            
        Returns:
            File path
        """
        # Hash key
        key_hash = hashlib.md5(key.encode()).hexdigest()
        
        # Split hash for directory structure
        hash_dirs = [key_hash[i:i+2] for i in range(0, 6, 2)]
        
        # Generate path
        path_parts = [self.cache_dir] + hash_dirs + [key_hash[6:]]
        
        return os.path.join(*path_parts)
    
    def _is_expired(self, file_path: str) -> bool:
        """
        Check if file is expired.
        
        Args:
            file_path: File path
            
        Returns:
            Whether file is expired
        """
        meta_path = f"{file_path}.meta"
        
        if not os.path.exists(meta_path):
            return True
        
        try:
            with open(meta_path, "r") as f:
                meta = json.load(f)
            
            return meta.get("expires_at", 0) < time.time()
        
        except:
            return True
    
    def _get_cache_size_mb(self) -> float:
        """
        Get cache size in MB.
        
        Returns:
            Cache size in MB
        """
        total_size = 0
        
        for root, dirs, files in os.walk(self.cache_dir):
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
        
        return total_size / (1024 * 1024)
    
    def _prune_cache(self) -> None:
        """Prune cache by removing expired and oldest entries."""
        # Get all files with metadata
        all_files = []
        
        for root, dirs, files in os.walk(self.cache_dir):
            for file in files:
                if not file.endswith(".meta"):
                    file_path = os.path.join(root, file)
                    meta_path = f"{file_path}.meta"
                    
                    if os.path.exists(meta_path):
                        try:
                            with open(meta_path, "r") as f:
                                meta = json.load(f)
                            
                            all_files.append({
                                "path": file_path,
                                "meta_path": meta_path,
                                "expires_at": meta.get("expires_at", 0),
                                "size": os.path.getsize(file_path) + os.path.getsize(meta_path)
                            })
                        
                        except:
                            pass
        
        # Remove expired files
        current_time = time.time()
        for file_info in all_files:
            if file_info["expires_at"] < current_time:
                try:
                    os.remove(file_info["path"])
                    os.remove(file_info["meta_path"])
                except:
                    pass
        
        # If still too large, remove oldest files
        if self._get_cache_size_mb() > self.max_size_mb:
            # Sort by expiration time
            all_files = [f for f in all_files if os.path.exists(f["path"])]
            all_files.sort(key=lambda x: x["expires_at"])
            
            # Remove oldest files until under limit
            for file_info in all_files:
                try:
                    os.remove(file_info["path"])
                    os.remove(file_info["meta_path"])
                except:
                    pass
                
                if self._get_cache_size_mb() <= self.max_size_mb:
                    break


class RedisCache:
    """
    Redis-based cache.
    """
    
    def __init__(self, 
                host: str = "localhost", 
                port: int = 6379, 
                db: int = 0, 
                password: Optional[str] = None,
                prefix: str = "cache:",
                ttl: int = 3600):
        """
        Initialize Redis cache.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database
            password: Redis password
            prefix: Key prefix
            ttl: Time-to-live in seconds
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.prefix = prefix
        self.ttl = ttl
        self._redis = None
    
    def _connect(self) -> None:
        """Connect to Redis."""
        try:
            import redis
            
            self._redis = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=False
            )
            
            # Test connection
            self._redis.ping()
        
        except ImportError:
            logger.error("Redis package not installed. Please install with: pip install redis")
            raise
        
        except Exception as e:
            logger.error(f"Error connecting to Redis: {str(e)}")
            self._redis = None
            raise
    
    def get(self, key: str) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self._redis:
            try:
                self._connect()
            except:
                return None
        
        try:
            # Get value
            value = self._redis.get(f"{self.prefix}{key}")
            
            if value is None:
                return None
            
            # Deserialize
            return pickle.loads(value)
        
        except Exception as e:
            logger.error(f"Error getting from Redis cache: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (overrides default)
        """
        if not self._redis:
            try:
                self._connect()
            except:
                return
        
        try:
            # Serialize
            serialized = pickle.dumps(value)
            
            # Set value
            self._redis.set(
                f"{self.prefix}{key}",
                serialized,
                ex=(ttl or self.ttl)
            )
        
        except Exception as e:
            logger.error(f"Error setting in Redis cache: {str(e)}")
    
    def delete(self, key: str) -> None:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
        """
        if not self._redis:
            try:
                self._connect()
            except:
                return
        
        try:
            # Delete key
            self._redis.delete(f"{self.prefix}{key}")
        
        except Exception as e:
            logger.error(f"Error deleting from Redis cache: {str(e)}")
    
    def clear(self) -> None:
        """Clear cache."""
        if not self._redis:
            try:
                self._connect()
            except:
                return
        
        try:
            # Delete all keys with prefix
            cursor = 0
            while True:
                cursor, keys = self._redis.scan(cursor, f"{self.prefix}*", 100)
                
                if keys:
                    self._redis.delete(*keys)
                
                if cursor == 0:
                    break
        
        except Exception as e:
            logger.error(f"Error clearing Redis cache: {str(e)}")


class CacheManager:
    """
    Cache manager for different caching strategies.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize cache manager.
        
        Args:
            config: Cache configuration
        """
        self.config = config or {}
        
        # Memory caches
        self.query_cache = MemoryCache(
            ttl=self.config.get("query_cache", {}).get("ttl", 3600),
            max_size=self.config.get("query_cache", {}).get("max_size", 1000)
        )
        
        # Disk cache for documents
        self.document_cache = DiskCache(
            cache_dir=self.config.get("document_cache", {}).get("cache_dir", "./cache/documents"),
            ttl=self.config.get("document_cache", {}).get("ttl", 86400),
            max_size_mb=self.config.get("document_cache", {}).get("max_size_mb", 1024)
        )
        
        # Either memory or disk cache for embeddings
        use_disk_cache = self.config.get("embedding_cache", {}).get("use_disk_cache", False)
        
        if use_disk_cache:
            self.embedding_cache = DiskCache(
                cache_dir=self.config.get("embedding_cache", {}).get("cache_dir", "./cache/embeddings"),
                ttl=self.config.get("embedding_cache", {}).get("ttl", 604800),  # 7 days
                max_size_mb=self.config.get("embedding_cache", {}).get("max_size_mb", 2048)
            )
        else:
            self.embedding_cache = MemoryCache(
                ttl=self.config.get("embedding_cache", {}).get("ttl", 3600 * 24),
                max_size=self.config.get("embedding_cache", {}).get("max_size", 10000)
            )
        
        # Redis cache
        redis_config = self.config.get("redis_cache", {})
        if redis_config.get("enabled", False):
            try:
                self.redis_cache = RedisCache(
                    host=redis_config.get("host", "localhost"),
                    port=redis_config.get("port", 6379),
                    db=redis_config.get("db", 0),
                    password=redis_config.get("password"),
                    prefix=redis_config.get("prefix", "rag:"),
                    ttl=redis_config.get("ttl", 3600)
                )
            except:
                self.redis_cache = None
        else:
            self.redis_cache = None
    
    def get_query_cache(self) -> MemoryCache:
        """
        Get query cache.
        
        Returns:
            Query cache
        """
        return self.query_cache
    
    def get_document_cache(self) -> DiskCache:
        """
        Get document cache.
        
        Returns:
            Document cache
        """
        return self.document_cache
    
    def get_embedding_cache(self) -> Union[MemoryCache, DiskCache]:
        """
        Get embedding cache.
        
        Returns:
            Embedding cache
        """
        return self.embedding_cache
    
    def get_redis_cache(self) -> Optional[RedisCache]:
        """
        Get Redis cache.
        
        Returns:
            Redis cache or None
        """
        return self.redis_cache
    
    def clear_all_caches(self) -> None:
        """Clear all caches."""
        self.query_cache.clear()
        self.document_cache.clear()
        self.embedding_cache.clear()
        
        if self.redis_cache:
            self.redis_cache.clear()


# Define a decorator for caching function results
def cache_result(cache: Union[MemoryCache, DiskCache, RedisCache], ttl: Optional[int] = None) -> Callable:
    """
    Decorator for caching function results.
    
    Args:
        cache: Cache to use
        ttl: Time-to-live in seconds
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Generate cache key
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            key_hash = hashlib.md5(key.encode()).hexdigest()
            
            # Check if result is in cache
            result = cache.get(key_hash)
            if result is not None:
                return result
            
            # Call function
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(key_hash, result, ttl)
            
            return result
        
        return wrapper
    
    return decorator