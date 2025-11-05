"""
CORS middleware configuration.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ..core.config import settings


def setup_cors(app: FastAPI) -> None:
    """
    Setup CORS middleware for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
    )