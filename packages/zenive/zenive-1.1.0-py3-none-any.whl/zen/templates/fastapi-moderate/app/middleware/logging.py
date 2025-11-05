"""
Request logging middleware.
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.routing import Match
import logging

# Setup logger
logger = logging.getLogger("api")


async def log_requests(request: Request, call_next: Callable) -> Response:
    """
    Middleware to log HTTP requests and responses.
    
    Args:
        request: The incoming request
        call_next: The next middleware or route handler
        
    Returns:
        The response from the next handler
    """
    # Generate request ID
    request_id = str(uuid.uuid4())
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    # Log request start
    start_time = time.time()
    
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Get route info
    route = None
    for r in request.app.routes:
        match, _ = r.matches({"type": "http", "path": request.url.path, "method": request.method})
        if match == Match.FULL:
            route = r.path
            break
    
    logger.info(
        f"Request started - ID: {request_id} | "
        f"Method: {request.method} | "
        f"Path: {request.url.path} | "
        f"Route: {route} | "
        f"Client: {client_ip} | "
        f"User-Agent: {request.headers.get('user-agent', 'unknown')}"
    )
    
    # Process request
    try:
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"Request completed - ID: {request_id} | "
            f"Status: {response.status_code} | "
            f"Duration: {process_time:.3f}s"
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as e:
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log error
        logger.error(
            f"Request failed - ID: {request_id} | "
            f"Error: {str(e)} | "
            f"Duration: {process_time:.3f}s"
        )
        
        # Re-raise the exception
        raise