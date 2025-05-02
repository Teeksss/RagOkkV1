"""
Rate limiting middleware for API endpoints.
"""
import time
from typing import Dict, Tuple, Optional, Callable
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

logger = logging.getLogger(__name__)

class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass

class RateLimiter:
    """Rate limiter implementation."""
    
    def __init__(self, rate_limit: int, time_window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            rate_limit: Maximum number of requests allowed in time window
            time_window: Time window in seconds
        """
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.requests: Dict[str, Tuple[int, float]] = {}  # client_id -> (count, start_time)
    
    def is_rate_limited(self, client_id: str) -> bool:
        """
        Check if client is rate limited.
        
        Args:
            client_id: Client identifier (IP address or API key)
            
        Returns:
            True if rate limited, False otherwise
        """
        current_time = time.time()
        
        # Get current count and start time for client
        count, start_time = self.requests.get(client_id, (0, current_time))
        
        # Check if time window has elapsed
        if current_time - start_time > self.time_window:
            # Reset counter for new time window
            self.requests[client_id] = (1, current_time)
            return False
        
        # Check if rate limit is exceeded
        if count >= self.rate_limit:
            return True
        
        # Increment counter
        self.requests[client_id] = (count + 1, start_time)
        return False
    
    def get_remaining(self, client_id: str) -> Tuple[int, int]:
        """
        Get remaining requests and reset time.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Tuple of (remaining requests, seconds until reset)
        """
        current_time = time.time()
        count, start_time = self.requests.get(client_id, (0, current_time))
        
        if current_time - start_time > self.time_window:
            return self.rate_limit, 0
        
        remaining = max(0, self.rate_limit - count)
        reset_in = int(self.time_window - (current_time - start_time))
        
        return remaining, reset_in


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests."""
    
    def __init__(self, app, rate_limit: int = 100, time_window: int = 60,
                 exempt_paths: Optional[list] = None,
                 get_client_id: Optional[Callable] = None):
        """
        Initialize rate limit middleware.
        
        Args:
            app: FastAPI application
            rate_limit: Maximum number of requests allowed in time window
            time_window: Time window in seconds
            exempt_paths: List of paths exempt from rate limiting
            get_client_id: Function to extract client ID from request
        """
        super().__init__(app)
        self.rate_limiter = RateLimiter(rate_limit, time_window)
        self.exempt_paths = exempt_paths or ["/health", "/docs", "/redoc", "/openapi.json"]
        self.get_client_id = get_client_id or self._default_client_id
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request with rate limiting.
        
        Args:
            request: FastAPI request
            call_next: Next middleware in chain
            
        Returns:
            Response
        """
        # Skip rate limiting for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        # Get client ID
        client_id = self.get_client_id(request)
        
        # Check rate limit
        if self.rate_limiter.is_rate_limited(client_id):
            # Get reset time
            _, reset_in = self.rate_limiter.get_remaining(client_id)
            
            # Log rate limit exceeded
            logger.warning(f"Rate limit exceeded for client {client_id}")
            
            # Return 429 Too Many Requests
            return Response(
                content={"error": "Rate limit exceeded"},
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "Retry-After": str(reset_in),
                    "X-RateLimit-Reset": str(reset_in),
                }
            )
        
        # Get remaining requests
        remaining, reset_in = self.rate_limiter.get_remaining(client_id)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_in)
        
        return response
    
    def _default_client_id(self, request: Request) -> str:
        """
        Extract client ID from request.
        Default implementation uses IP address.
        
        Args:
            request: FastAPI request
            
        Returns:
            Client ID string
        """
        # Try to get API key from header
        api_key = request.headers.get("X-API-KEY")
        if api_key:
            return f"api:{api_key}"
        
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        return request.client.host