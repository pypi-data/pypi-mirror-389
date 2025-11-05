"""
Enhanced logging middleware for FastAPI Industry Template.

Provides structured request/response logging with correlation IDs,
performance tracking, and security event logging.
"""

import time
import uuid
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import performance_logger, security_logger

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Enhanced logging middleware with structured logging and correlation IDs.
    
    Features:
    - Correlation ID generation and tracking
    - Request/response logging with performance metrics
    - Security event logging
    - Error context capture
    - User activity tracking
    """
    
    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with enhanced logging."""
        
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        
        # Add correlation ID to request state
        request.state.correlation_id = correlation_id
        
        # Get request details
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else None
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # Get user ID if available (from JWT token)
        user_id = getattr(request.state, 'user_id', None)
        
        # Start timing
        start_time = time.time()
        
        # Log request start
        logger.info(
            "Request started",
            method=method,
            path=path,
            query_params=query_params,
            client_ip=client_ip,
            user_agent=user_agent,
            user_id=user_id,
            correlation_id=correlation_id,
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log request completion
            logger.info(
                "Request completed",
                method=method,
                path=path,
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
                client_ip=client_ip,
                user_id=user_id,
                correlation_id=correlation_id,
            )
            
            # Log performance metrics
            performance_logger.log_request_performance(
                method=method,
                path=path,
                status_code=response.status_code,
                duration=duration,
                correlation_id=correlation_id,
                user_id=user_id,
                client_ip=client_ip,
            )
            
            # Log security events for authentication endpoints
            if self._is_auth_endpoint(path):
                security_logger.log_authentication_attempt(
                    email=self._extract_email_from_request(request),
                    success=response.status_code < 400,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    correlation_id=correlation_id,
                )
            
            # Log suspicious activity
            if self._is_suspicious_request(request, response):
                security_logger.log_suspicious_activity(
                    activity_type="suspicious_request",
                    details={
                        "method": method,
                        "path": path,
                        "status_code": response.status_code,
                        "user_agent": user_agent,
                    },
                    ip_address=client_ip,
                    correlation_id=correlation_id,
                )
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except Exception as e:
            # Calculate duration for error case
            duration = time.time() - start_time
            
            # Log error with full context
            logger.error(
                "Request failed",
                method=method,
                path=path,
                duration_ms=round(duration * 1000, 2),
                client_ip=client_ip,
                user_id=user_id,
                correlation_id=correlation_id,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            
            # Re-raise the exception
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request headers.
        
        Checks multiple headers to handle load balancers and proxies.
        """
        # Check common headers for real IP
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        if hasattr(request.client, 'host'):
            return request.client.host
        
        return "unknown"
    
    def _is_auth_endpoint(self, path: str) -> bool:
        """Check if the path is an authentication endpoint."""
        auth_paths = ["/auth/login", "/auth/register", "/auth/refresh", "/auth/logout"]
        return any(auth_path in path for auth_path in auth_paths)
    
    def _extract_email_from_request(self, request: Request) -> str:
        """
        Extract email from request body for authentication logging.
        
        Note: This is a simplified implementation. In production,
        you might want to parse the request body more carefully.
        """
        # This would need to be implemented based on your auth structure
        # For now, return a placeholder
        return "unknown"
    
    def _is_suspicious_request(self, request: Request, response: Response) -> bool:
        """
        Detect suspicious request patterns.
        
        This is a basic implementation. In production, you'd want
        more sophisticated detection logic.
        """
        # Check for common suspicious patterns
        suspicious_patterns = [
            # Multiple failed authentication attempts
            request.url.path.startswith("/auth/") and response.status_code == 401,
            # Requests to non-existent endpoints
            response.status_code == 404 and not request.url.path.startswith("/static/"),
            # Requests with suspicious user agents
            "bot" in request.headers.get("user-agent", "").lower() and 
            not any(allowed in request.headers.get("user-agent", "").lower() 
                   for allowed in ["googlebot", "bingbot"]),
        ]
        
        return any(suspicious_patterns)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Simple middleware to add correlation ID to request state.
    
    This can be used independently if you don't need full logging middleware.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add correlation ID to request state."""
        
        # Check if correlation ID already exists (from external source)
        correlation_id = request.headers.get("X-Correlation-ID")
        
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Add to request state
        request.state.correlation_id = correlation_id
        
        # Process request
        response = await call_next(request)
        
        # Add to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response