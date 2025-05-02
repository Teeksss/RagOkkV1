"""
API module initialization.
"""
from fastapi import APIRouter

from .routers import (
    documents, 
    search, 
    vector_index, 
    document_versions, 
    metrics,
    users,
    admin,
    api_keys,
    conversations
)

# Create main API router
api_router = APIRouter()

# Include all routers
api_router.include_router(documents.router)
api_router.include_router(search.router)
api_router.include_router(vector_index.router)
api_router.include_router(document_versions.router)
api_router.include_router(metrics.router)
api_router.include_router(users.router)
api_router.include_router(admin.router)
api_router.include_router(api_keys.router)
api_router.include_router(conversations.router)