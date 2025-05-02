"""
API routes.
"""
from fastapi import APIRouter

from .routers import documents, conversations, tags, auth, admin, api_keys

# Create API router
api_router = APIRouter()

# Include routers
api_router.include_router(auth.router)
api_router.include_router(documents.router)
api_router.include_router(conversations.router)
api_router.include_router(tags.router)
api_router.include_router(admin.router)
api_router.include_router(api_keys.router)