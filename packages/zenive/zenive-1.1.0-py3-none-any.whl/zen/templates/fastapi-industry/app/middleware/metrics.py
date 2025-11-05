"""
Metrics middleware for FastAPI Industry Template.

Collects Prometheus metrics for monitoring and observability.
"""

import time
from typing import Callable

import structlog
from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'version']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'version'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

REQUEST_SIZE = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint', 'version']
)

RESPONSE_SIZE = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint', 'status_code', 'version']
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Number of active HTTP requests'
)

DATABASE_CONNECTIONS = Gauge(
    'database_connections_active',
    'Number of active database connections'
)

CACHE_OPERATIONS = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'result']
)

BACKGROUND_TASKS = Counter(
    'background_tasks_total',
    'Total background tasks',
    ['task_name', 'status']
)

ERROR_COUNT = Counter(
    'application_errors_total',
    'Total application errors',
    ['error_type', 'endpoint', 'version']
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect Prometheus metrics for all HTTP requests.
    
    Collects:
    - Request count by method, endpoint, and status code
    - Request duration histograms
    - Request and response size histograms
    - Active request gauge
    - Error counts
    """
    
    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self.version = settings.VERSION
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics."""
        
        if not settings.METRICS_ENABLED:
            return await call_next(request)
        
        # Skip metrics collection for metrics endpoint itself
        if request.url.path == settings.METRICS_PATH:
            return await call_next(request)
        
        # Get request details
        method = request.method
        path = request.url.path
        
        # Normalize path for metrics (remove IDs and query params)
        normalized_path = self._normalize_path(path)
        
        # Get request size
        request_size = int(request.headers.get("content-length", 0))
        if request_size > 0:
            REQUEST_SIZE.labels(
                method=method,
                endpoint=normalized_path,
                version=self.version
            ).observe(request_size)
        
        # Track active requests
        ACTIVE_REQUESTS.inc()
        
        # Start timing
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Get response size
            response_size = 0
            if hasattr(response, 'body'):
                response_size = len(response.body)
            elif 'content-length' in response.headers:
                response_size = int(response.headers['content-length'])
            
            # Record metrics
            REQUEST_COUNT.labels(
                method=method,
                endpoint=normalized_path,
                status_code=response.status_code,
                version=self.version
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=normalized_path,
                version=self.version
            ).observe(duration)
            
            if response_size > 0:
                RESPONSE_SIZE.labels(
                    method=method,
                    endpoint=normalized_path,
                    status_code=response.status_code,
                    version=self.version
                ).observe(response_size)
            
            # Log slow requests
            if duration > 1.0:  # Log requests slower than 1 second
                logger.warning(
                    "Slow request detected",
                    method=method,
                    path=path,
                    duration=duration,
                    status_code=response.status_code
                )
            
            return response
            
        except Exception as e:
            # Record error metrics
            ERROR_COUNT.labels(
                error_type=type(e).__name__,
                endpoint=normalized_path,
                version=self.version
            ).inc()
            
            logger.error(
                "Request processing error",
                method=method,
                path=path,
                error=str(e),
                error_type=type(e).__name__
            )
            
            raise
        
        finally:
            # Always decrement active requests
            ACTIVE_REQUESTS.dec()
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize path for metrics to avoid high cardinality.
        
        Replaces path parameters with placeholders to prevent
        creating too many unique metric labels.
        """
        # Common patterns to normalize
        import re
        
        # Replace UUIDs
        path = re.sub(
            r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '/{uuid}',
            path,
            flags=re.IGNORECASE
        )
        
        # Replace numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)
        
        # Replace email addresses
        path = re.sub(r'/[^/]+@[^/]+\.[^/]+', '/{email}', path)
        
        # Limit path length and remove query parameters
        path = path.split('?')[0]
        if len(path) > 100:
            path = path[:100] + "..."
        
        return path


def record_cache_operation(operation: str, hit: bool) -> None:
    """Record cache operation metrics."""
    result = "hit" if hit else "miss"
    CACHE_OPERATIONS.labels(operation=operation, result=result).inc()


def record_background_task(task_name: str, success: bool) -> None:
    """Record background task metrics."""
    status = "success" if success else "failure"
    BACKGROUND_TASKS.labels(task_name=task_name, status=status).inc()


def update_database_connections(count: int) -> None:
    """Update database connections gauge."""
    DATABASE_CONNECTIONS.set(count)