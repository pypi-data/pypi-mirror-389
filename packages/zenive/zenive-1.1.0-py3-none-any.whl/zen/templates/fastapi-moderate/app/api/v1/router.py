"""
API v1 router configuration.
"""
from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router

# Create API v1 router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["authentication"]
)

api_router.include_router(
    users_router,
    prefix="/users",
    tags=["users"]
)