"""
Main application module.
"""
import logging
import os
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from .api import api_router
from .database.document_store import init_db
from .config import settings
from .utils.db_logger import DBLogger
from .database.document_store import get_db
from .auth.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="RAG System",
    description="Retrieval-Augmented Generation (RAG) system with document management and chat capabilities",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create rate limiter
rate_limiter = RateLimiter(
    limit=settings.RATE_LIMIT_REQUESTS,
    window=60  # 1 minute
)

# Add API router
app.include_router(api_router, prefix="/api/v1")

# Create upload directory if it doesn't exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Initialize database
@app.on_event("startup")
async def startup_event():
    logger.info("Starting application...")
    init_db()


# Rate limiter middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiter middleware."""
    if not settings.RATE_LIMIT_ENABLED:
        return await call_next(request)
    
    # Skip rate limiting for static files
    if request.url.path.startswith("/uploads"):
        return await call_next(request)
    
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Check rate limit
    if not rate_limiter.is_allowed(client_ip):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many requests"}
        )
    
    return await call_next(request)


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    # Log error
    try:
        db = next(get_db())
        db_logger = DBLogger(db)
        db_logger.log_error(
            operation="api_error",
            error_message=exc.detail,
            request_path=request.url.path,
            request_method=request.method,
            status_code=exc.status_code,
            ip_address=request.client.host if request.client else None
        )
    except:
        # If logging fails, just continue
        pass
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    # Log error
    logger.exception("Unhandled exception:")
    
    try:
        db = next(get_db())
        db_logger = DBLogger(db)
        db_logger.log_error(
            operation="server_error",
            error_message=str(exc),
            request_path=request.url.path,
            request_method=request.method,
            status_code=500,
            ip_address=request.client.host if request.client else None,
            exception=exc
        )
    except:
        # If logging fails, just continue
        pass
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# Application root
@app.get("/")
async def root():
    return {"message": "Welcome to RAG System API"}


# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


# Run application
if __name__ == "__main__":
    uvicorn.run(
        "rag_system.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )