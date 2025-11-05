"""
FastAPI Industry Template - Main Application

Enterprise-grade FastAPI application with comprehensive monitoring,
observability, and production features.
"""

import time
from contextlib import asynccontextmanager
from typing import Dict, Any

import sentry_sdk
import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.logging import setup_logging
from app.middleware.cors import setup_cors
from app.middleware.logging import LoggingMiddleware
from app.middleware.metrics import MetricsMiddleware
from app.middleware.security import SecurityMiddleware

# Setup structured logging
setup_logging()
logger = structlog.get_logger()

# Prometheus metrics are handled by MetricsMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting FastAPI Industry application", version=settings.VERSION)
    
    # Initialize Sentry for error tracking
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                FastApiIntegration(auto_enabling_integrations=False),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            environment=settings.ENVIRONMENT,
            release=settings.VERSION,
        )
        logger.info("Sentry error tracking initialized")
    
    # Test database connection
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        logger.info("Database connection established")
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI Industry application")
    await engine.dispose()


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise FastAPI application with full production features",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.ENVIRONMENT != "production" else None,
    docs_url=f"{settings.API_V1_STR}/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url=f"{settings.API_V1_STR}/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# Setup CORS
setup_cors(app)

# Add middleware (order matters - last added is executed first)
app.add_middleware(SecurityMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(LoggingMiddleware)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for load balancers and monitoring systems.
    
    Returns:
        Dict containing health status and system information
    """
    try:
        # Test database connection
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error("Health check database error", error=str(e))
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "timestamp": time.time(),
    }


@app.get("/health/ready")
async def readiness_check() -> Dict[str, str]:
    """
    Readiness check for Kubernetes deployments.
    
    Returns:
        Dict indicating if the application is ready to serve traffic
    """
    # Add any readiness checks here (database migrations, external services, etc.)
    return {"status": "ready"}


@app.get("/health/live")
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check for Kubernetes deployments.
    
    Returns:
        Dict indicating if the application is alive
    """
    return {"status": "alive"}


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Returns:
        Prometheus formatted metrics
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint with basic application information.
    
    Returns:
        Dict with welcome message and API information
    """
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs_url": f"{settings.API_V1_STR}/docs" if settings.ENVIRONMENT != "production" else "disabled",
        "health_url": "/health",
        "metrics_url": "/metrics",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_config=None,  # Use our custom logging setup
    )