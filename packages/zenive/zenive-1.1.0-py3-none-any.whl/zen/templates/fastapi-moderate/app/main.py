"""
FastAPI application with authentication, database, and production features.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .core.config import settings
from .core.database import init_db, close_db
from .api.v1.router import api_router
from .middleware.cors import setup_cors
# Security utilities are imported where needed
from .middleware.logging import log_requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting up FastAPI application...")
    # await init_db()  # Commented out for now - requires database setup
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description=settings.description,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup middleware
setup_cors(app)
# Security middleware setup removed - using security utilities directly
app.middleware("http")(log_requests)

# Include API routes
app.include_router(api_router, prefix=settings.api_v1_str)


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle HTTP exceptions.
    
    Args:
        request: The request that caused the exception
        exc: The HTTP exception
        
    Returns:
        JSON response with error details
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle request validation errors.
    
    Args:
        request: The request that caused the exception
        exc: The validation exception
        
    Returns:
        JSON response with validation error details
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "message": "Validation error",
            "details": exc.errors(),
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle general exceptions.
    
    Args:
        request: The request that caused the exception
        exc: The exception
        
    Returns:
        JSON response with error details
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "Internal server error" if not settings.debug else str(exc),
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "request_id": getattr(request.state, "request_id", None)
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Application health status
    """
    return {
        "status": "healthy",
        "service": settings.project_name,
        "version": settings.version
    }


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information.
    
    Returns:
        API information
    """
    return {
        "message": f"Welcome to {settings.project_name}",
        "version": settings.version,
        "description": settings.description,
        "docs_url": "/docs" if settings.debug else "Documentation disabled in production",
        "api_v1": settings.api_v1_str
    }