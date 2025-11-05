"""
Rate limiting middleware for FastAPI Industry Template.

Implements sliding window rate limiting with Redis backend,
IP-based and user-based limits, and configurable rules.
"""

import time
from typing import Dict, Optional, Tuple, Callable

import structlog
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.cache import cache_manager

logger = structlog.get_logger(__name__)


class AdvancedRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Advanced rate limiting middleware with multiple strategies.
    
    Features:
    - IP-based rate limiting
    - User-based rate limiting
    - Endpoint-specific limits
    - Sliding window algorithm
    - Burst protection
    - Whitelist/blacklist support
    """
    
    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self.default_requests = settings.RATE_LIMIT_REQUESTS
        self.default_window = settings.RATE_LIMIT_WINDOW
        
        # Endpoint-specific rate limits
        self.endpoint_limits = {
            "/auth/login": {"requests": 5, "window": 300},  # 5 requests per 5 minutes
            "/auth/register": {"requests": 3, "window": 3600},  # 3 requests per hour
            "/auth/forgot-password": {"requests": 3, "window": 3600},
            "/api/v1/upload": {"requests": 10, "window": 60},  # 10 uploads per minute
        }
        
        # IP whitelist (no rate limiting)
        self.ip_whitelist = {
            "127.0.0.1",
            "::1",
            # Add your monitoring/health check IPs here
        }
        
        # IP blacklist (always blocked)
        self.ip_blacklist = set()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting to requests."""
        
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check blacklist
        if client_ip in self.ip_blacklist:
            logger.warning("Blocked request from blacklisted IP", ip=client_ip)
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Skip rate limiting for whitelisted IPs
        if client_ip in self.ip_whitelist:
            return await call_next(request)
        
        # Get rate limit configuration for this endpoint
        path = request.url.path
        rate_config = self._get_rate_limit_config(path)
        
        # Apply rate limiting
        try:
            await self._check_rate_limit(request, client_ip, rate_config)
        except RateLimitExceeded as e:
            logger.warning(
                "Rate limit exceeded",
                ip=client_ip,
                path=path,
                method=request.method,
                limit=rate_config["requests"],
                window=rate_config["window"]
            )
            
            # Add rate limit headers
            response = Response(
                content=f"Rate limit exceeded: {e.detail}",
                status_code=429,
                headers={
                    "X-RateLimit-Limit": str(rate_config["requests"]),
                    "X-RateLimit-Window": str(rate_config["window"]),
                    "X-RateLimit-Reset": str(int(time.time()) + rate_config["window"]),
                    "Retry-After": str(rate_config["window"]),
                }
            )
            return response
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        remaining = await self._get_remaining_requests(client_ip, rate_config)
        response.headers["X-RateLimit-Limit"] = str(rate_config["requests"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(rate_config["window"])
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        # Check X-Forwarded-For header first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        if hasattr(request.client, 'host'):
            return request.client.host
        
        return "unknown"
    
    def _get_rate_limit_config(self, path: str) -> Dict[str, int]:
        """Get rate limit configuration for a specific path."""
        # Check for exact path match
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]
        
        # Check for pattern matches
        for pattern, config in self.endpoint_limits.items():
            if path.startswith(pattern):
                return config
        
        # Return default configuration
        return {
            "requests": self.default_requests,
            "window": self.default_window
        }
    
    async def _check_rate_limit(
        self,
        request: Request,
        client_ip: str,
        rate_config: Dict[str, int]
    ) -> None:
        """Check if request exceeds rate limit."""
        
        # Create rate limit key
        path = request.url.path
        method = request.method
        window = rate_config["window"]
        max_requests = rate_config["requests"]
        
        # Use different keys for different rate limiting strategies
        keys = []
        
        # IP-based rate limiting
        ip_key = f"rate_limit:ip:{client_ip}:{path}:{method}:{window}"
        keys.append((ip_key, max_requests))
        
        # User-based rate limiting (if authenticated)
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            user_key = f"rate_limit:user:{user_id}:{path}:{method}:{window}"
            # Users get higher limits
            user_max_requests = max_requests * 2
            keys.append((user_key, user_max_requests))
        
        # Check all rate limits
        for key, limit in keys:
            current_count = await self._get_current_count(key, window)
            
            if current_count >= limit:
                raise RateLimitExceeded(
                    detail=f"Rate limit exceeded: {current_count}/{limit} requests per {window} seconds"
                )
            
            # Increment counter
            await self._increment_counter(key, window)
    
    async def _get_current_count(self, key: str, window: int) -> int:
        """Get current request count for a key."""
        try:
            count = await cache_manager.get(key, 0)
            return int(count) if count is not None else 0
        except Exception as e:
            logger.error("Error getting rate limit count", key=key, error=str(e))
            return 0
    
    async def _increment_counter(self, key: str, window: int) -> None:
        """Increment request counter for a key."""
        try:
            # Use Redis INCR for atomic increment
            if cache_manager.redis_client:
                current = await cache_manager.redis_client.incr(key)
                if current == 1:
                    # Set expiration only for new keys
                    await cache_manager.redis_client.expire(key, window)
            else:
                # Fallback to cache manager
                current = await cache_manager.get(key, 0)
                await cache_manager.set(key, current + 1, window)
                
        except Exception as e:
            logger.error("Error incrementing rate limit counter", key=key, error=str(e))
    
    async def _get_remaining_requests(
        self,
        client_ip: str,
        rate_config: Dict[str, int]
    ) -> int:
        """Get remaining requests for client."""
        try:
            window = rate_config["window"]
            max_requests = rate_config["requests"]
            
            ip_key = f"rate_limit:ip:{client_ip}:*:{window}"
            current = await self._get_current_count(ip_key, window)
            
            return max(0, max_requests - current)
        except Exception:
            return 0


class BurstProtectionMiddleware(BaseHTTPMiddleware):
    """
    Burst protection middleware to prevent rapid-fire requests.
    
    Implements a token bucket algorithm for burst protection.
    """
    
    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self.burst_limit = 10  # Maximum burst requests
        self.refill_rate = 1   # Tokens per second
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply burst protection."""
        
        client_ip = self._get_client_ip(request)
        
        # Check burst protection
        if not await self._check_burst_limit(client_ip):
            logger.warning("Burst limit exceeded", ip=client_ip)
            return Response(
                content="Too many requests in burst",
                status_code=429,
                headers={"Retry-After": "1"}
            )
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        if hasattr(request.client, 'host'):
            return request.client.host
        
        return "unknown"
    
    async def _check_burst_limit(self, client_ip: str) -> bool:
        """Check if client exceeds burst limit using token bucket."""
        
        bucket_key = f"burst_bucket:{client_ip}"
        now = time.time()
        
        try:
            # Get current bucket state
            bucket_data = await cache_manager.get(bucket_key)
            
            if bucket_data is None:
                # Initialize new bucket
                bucket_data = {
                    "tokens": self.burst_limit,
                    "last_refill": now
                }
            
            # Calculate tokens to add based on time elapsed
            time_elapsed = now - bucket_data["last_refill"]
            tokens_to_add = time_elapsed * self.refill_rate
            
            # Update bucket
            bucket_data["tokens"] = min(
                self.burst_limit,
                bucket_data["tokens"] + tokens_to_add
            )
            bucket_data["last_refill"] = now
            
            # Check if we have tokens available
            if bucket_data["tokens"] >= 1:
                bucket_data["tokens"] -= 1
                await cache_manager.set(bucket_key, bucket_data, 3600)  # 1 hour TTL
                return True
            else:
                await cache_manager.set(bucket_key, bucket_data, 3600)
                return False
                
        except Exception as e:
            logger.error("Error in burst protection", ip=client_ip, error=str(e))
            # Allow request on error
            return True


# Simple rate limiter using slowapi
def get_rate_limiter() -> Limiter:
    """Get configured rate limiter instance."""
    
    def rate_limit_key_func(request: Request) -> str:
        """Generate rate limit key from request."""
        # Use user ID if authenticated, otherwise use IP
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Get client IP
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[0].strip()}"
        
        if hasattr(request.client, 'host'):
            return f"ip:{request.client.host}"
        
        return "ip:unknown"
    
    return Limiter(
        key_func=rate_limit_key_func,
        storage_uri=settings.REDIS_URL,
        default_limits=[f"{settings.RATE_LIMIT_REQUESTS}/minute"]
    )


# Global rate limiter instance
limiter = get_rate_limiter()