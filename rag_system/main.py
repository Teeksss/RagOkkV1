"""
Main application module for the RAG system.
"""
import logging
import time
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

from .config import settings
from .api import api_router
from .auth.middleware import get_current_user
from .database.document_store import get_db
from .utils.db_logger import DBLogger

logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Retrieval Augmented Generation System API",
    version=settings.APP_VERSION,
    docs_url=None,  # Custom docs URL
    redoc_url=None,  # Custom redoc URL
    openapi_url=f"/api/{settings.API_VERSION}/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to response."""
    start_time = time.time()
    
    # Default response in case of error
    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        
        # Log request
        if request.url.path not in ["/health", "/metrics"]:
            # Get DB session
            db = next(get_db())
            
            # Get user from request if authenticated
            user_id = None
            try:
                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.replace("Bearer ", "")
                    user = await get_current_user(token)
                    user_id = user.id if user else None
            except:
                # Ignore auth errors in middleware
                pass
            
            # Log request
            db_logger = DBLogger(db)
            db_logger.log_operation(
                level="INFO",
                message=f"{request.method} {request.url.path}",
                operation="request",
                user_id=user_id,
                request_path=str(request.url.path),
                request_method=request.method,
                status_code=response.status_code,
                response_time=process_time,
                ip_address=request.client.host if request.client else None
            )
        
        return response
    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        process_time = time.time() - start_time
        
        # Try to log error
        try:
            db = next(get_db())
            db_logger = DBLogger(db)
            db_logger.log_error(
                operation="request",
                error_message=str(e),
                request_path=str(request.url.path),
                request_method=request.method,
                status_code=500,
                latency=process_time,
                ip_address=request.client.host if request.client else None
            )
        except:
            # Ignore logging errors in error handler
            pass
        
        # Raise original exception
        raise

# Include API router
app.include_router(
    api_router,
    prefix=f"/api/{settings.API_VERSION}"
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }

# API version endpoint
@app.get("/version", tags=["info"])
async def version():
    """Get API version."""
    return {
        "version": settings.APP_VERSION,
        "api_version": settings.API_VERSION,
        "app_name": settings.APP_NAME
    }

# Custom Swagger UI
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI."""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )

# Custom ReDoc
@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """Custom ReDoc."""
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )

# Custom OpenAPI schema
def custom_openapi():
    """Custom OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Retrieval Augmented Generation System API",
        routes=app.routes,
    )
    
    # Custom schema modifications
    openapi_schema["info"]["x-logo"] = {
        "url": "/static/logo.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "rag_system.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )