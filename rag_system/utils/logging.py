"""
Logging utilities.
"""
import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import Request
import time

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/rag_system.log", mode="a")
    ]
)

# Create logs directory if not exists
os.makedirs("logs", exist_ok=True)

# Create logger
logger = logging.getLogger("rag_system")


def get_logger(name: str) -> logging.Logger:
    """
    Get logger by name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_operation(message: str, user_id: Optional[str] = None, **kwargs) -> None:
    """
    Log operation with structured data.
    
    Args:
        message: Log message
        user_id: User ID
        **kwargs: Additional data
    """
    log_data = {
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        **kwargs
    }
    
    logger.info(json.dumps(log_data))


def log_request(request: Request, response_time: float, status_code: int) -> None:
    """
    Log HTTP request.
    
    Args:
        request: FastAPI request
        response_time: Response time in seconds
        status_code: HTTP status code
    """
    # Get user ID from request state if available
    user_id = getattr(request.state, "user_id", None)
    
    log_data = {
        "message": f"HTTP {request.method} {request.url.path}",
        "method": request.method,
        "path": request.url.path,
        "query_params": str(request.query_params),
        "client_host": request.client.host if request.client else None,
        "user_id": user_id,
        "response_time": response_time,
        "status_code": status_code
    }
    
    # Log at appropriate level based on status code
    if status_code >= 500:
        logger.error(json.dumps(log_data))
    elif status_code >= 400:
        logger.warning(json.dumps(log_data))
    else:
        logger.info(json.dumps(log_data))


class RequestLoggingMiddleware:
    """Middleware for logging requests."""
    
    async def __call__(self, request: Request, call_next):
        """
        Process request and log details.
        
        Args:
            request: FastAPI request
            call_next: Next middleware
            
        Returns:
            Response
        """
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Log request
        log_request(request, response_time, response.status_code)
        
        # Add timing header
        response.headers["X-Response-Time"] = str(response_time)
        
        return response