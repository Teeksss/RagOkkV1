"""
Rate limiter for API endpoints.
"""
import time
import logging
from typing import Dict, Any, Optional
from threading import Lock

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Simple in-memory rate limiter.
    """
    
    def __init__(self, limit: int = 100, window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            limit: Maximum number of requests per window
            window: Time window in seconds
        """
        self.limit = limit
        self.window = window
        self.clients: Dict[str, list] = {}
        self.lock = Lock()
    
    def is_allowed(self, client_id: str) -> bool:
        """
        Check if request is allowed.
        
        Args:
            client_id: Client identifier (e.g., IP address)
            
        Returns:
            Whether request is allowed
        """
        with self.lock:
            current_time = time.time()
            
            # Initialize client if not exists
            if client_id not in self.clients:
                self.clients[client_id] = []
            
            # Remove old requests
            self.clients[client_id] = [
                timestamp for timestamp in self.clients[client_id]
                if current_time - timestamp < self.window
            ]
            
            # Check if limit exceeded
            if len(self.clients[client_id]) >= self.limit:
                logger.warning(f"Rate limit exceeded for {client_id}: {len(self.clients[client_id])} requests")
                return False
            
            # Add new request
            self.clients[client_id].append(current_time)
            
            # Cleanup old clients occasionally
            if len(self.clients) > 1000 and client_id.endswith('0'):  # random sampling for cleanup
                self._cleanup()
            
            return True
    
    def _cleanup(self) -> None:
        """
        Clean up old client entries.
        """
        current_time = time.time()
        clients_to_remove = []
        
        for client_id, timestamps in self.clients.items():
            # Check if client has any requests in current window
            if not any(current_time - timestamp < self.window for timestamp in timestamps):
                clients_to_remove.append(client_id)
        
        # Remove old clients
        for client_id in clients_to_remove:
            del self.clients[client_id]
        
        if clients_to_remove:
            logger.debug(f"Cleaned up {len(clients_to_remove)} inactive clients")


class RedisRateLimiter:
    """
    Redis-based rate limiter.
    
    Note: Requires redis package.
    """
    
    def __init__(self, 
                redis_url: str = "redis://localhost:6379/0", 
                limit: int = 100, 
                window: int = 60,
                prefix: str = "ratelimit:"):
        """
        Initialize Redis rate limiter.
        
        Args:
            redis_url: Redis URL
            limit: Maximum number of requests per window
            window: Time window in seconds
            prefix: Redis key prefix
        """
        self.redis_url = redis_url
        self.limit = limit
        self.window = window
        self.prefix = prefix
        self._redis = None
    
    def _get_redis(self):
        """
        Get Redis connection.
        
        Returns:
            Redis connection
        """
        if self._redis is None:
            try:
                import redis
                self._redis = redis.from_url(self.redis_url)
            except ImportError:
                logger.error("Redis package not installed. Please install with: pip install redis")
                raise
            except Exception as e:
                logger.error(f"Error connecting to Redis: {str(e)}")
                raise
        
        return self._redis
    
    def is_allowed(self, client_id: str) -> bool:
        """
        Check if request is allowed.
        
        Args:
            client_id: Client identifier (e.g., IP address)
            
        Returns:
            Whether request is allowed
        """
        try:
            redis_client = self._get_redis()
            
            # Generate key
            key = f"{self.prefix}{client_id}"
            
            # Get current count
            current_count = redis_client.get(key)
            
            if current_count is not None and int(current_count) >= self.limit:
                return False
            
            # Increment count and set expiry
            pipe = redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, self.window)
            pipe.execute()
            
            return True
        
        except Exception as e:
            logger.error(f"Error in Redis rate limiter: {str(e)}")
            # Fall back to allowing the request on error
            return True