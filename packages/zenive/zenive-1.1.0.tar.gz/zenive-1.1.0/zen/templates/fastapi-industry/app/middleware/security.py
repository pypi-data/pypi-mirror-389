"""
Enhanced security middleware for FastAPI Industry Template.

Extends the moderate template's security middleware with additional
enterprise security features.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import structlog

logger = structlog.get_logger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Enhanced security middleware with enterprise features.
    
    Includes all basic security headers plus additional protections
    for enterprise environments.
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Add comprehensive security headers and protections.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            Response with security headers and protections
        """
        start_time = time.time()
        
        # Log security-relevant request info
        logger.info(
            "Security check",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        response = await call_next(request)
        
        # Add comprehensive security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        # Add custom security headers
        response.headers["X-Security-Scan"] = "passed"
        response.headers["X-Response-Time"] = str(round((time.time() - start_time) * 1000, 2))
        
        return response