"""
Security middleware for headers and protection.
"""
from fastapi import FastAPI, Request, Response
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to responses.
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Add security headers to the response.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            Response with security headers added
        """
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response


def setup_security_middleware(app: FastAPI) -> None:
    """
    Setup security middleware for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Add trusted host middleware (configure hosts as needed)
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
    )
    
    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)