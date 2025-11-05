"""
Redis caching layer for FastAPI Industry Template.

Provides high-performance caching with automatic serialization,
TTL management, and cache invalidation patterns.
"""

import json
import pickle
from typing import Any, Optional, Union, Dict, List
from datetime import timedelta

import redis.asyncio as redis
import structlog
from pydantic import BaseModel

from app.core.config import settings
from app.middleware.metrics import record_cache_operation

logger = structlog.get_logger(__name__)


class CacheManager:
    """
    Redis-based cache manager with automatic serialization and TTL management.
    
    Features:
    - Automatic JSON/Pickle serialization
    - TTL management with default and custom expiration
    - Cache invalidation patterns
    - Metrics collection
    - Connection pooling
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.default_ttl = settings.REDIS_CACHE_TTL
        self._connection_pool = None
    
    async def connect(self) -> None:
        """Initialize Redis connection with connection pooling."""
        try:
            self._connection_pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=20,
                retry_on_timeout=True,
                decode_responses=False,  # We handle encoding ourselves
            )
            
            self.redis_client = redis.Redis(
                connection_pool=self._connection_pool
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis cache connection established")
            
        except Exception as e:
            logger.error("Failed to connect to Redis cache", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis cache connection closed")
    
    async def get(
        self,
        key: str,
        default: Any = None,
        deserialize_json: bool = True
    ) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            deserialize_json: Whether to deserialize JSON automatically
            
        Returns:
            Cached value or default
        """
        if not self.redis_client:
            logger.warning("Redis client not connected")
            record_cache_operation("get", False)
            return default
        
        try:
            value = await self.redis_client.get(key)
            
            if value is None:
                record_cache_operation("get", False)
                return default
            
            # Deserialize based on content type
            if deserialize_json:
                try:
                    result = json.loads(value.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Fallback to pickle
                    result = pickle.loads(value)
            else:
                result = value.decode('utf-8')
            
            record_cache_operation("get", True)
            logger.debug("Cache hit", key=key)
            return result
            
        except Exception as e:
            logger.error("Cache get error", key=key, error=str(e))
            record_cache_operation("get", False)
            return default
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None,
        serialize_json: bool = True
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live (seconds or timedelta)
            serialize_json: Whether to serialize as JSON
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            logger.warning("Redis client not connected")
            return False
        
        try:
            # Serialize value
            if serialize_json:
                try:
                    serialized_value = json.dumps(value, default=str)
                except (TypeError, ValueError):
                    # Fallback to pickle for complex objects
                    serialized_value = pickle.dumps(value)
                    serialize_json = False
            else:
                serialized_value = str(value)
            
            # Set TTL
            if ttl is None:
                ttl = self.default_ttl
            elif isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            
            # Store in Redis
            await self.redis_client.setex(key, ttl, serialized_value)
            
            logger.debug("Cache set", key=key, ttl=ttl, json_serialized=serialize_json)
            return True
            
        except Exception as e:
            logger.error("Cache set error", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.delete(key)
            logger.debug("Cache delete", key=key, deleted=bool(result))
            return bool(result)
            
        except Exception as e:
            logger.error("Cache delete error", key=key, error=str(e))
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        
        Args:
            pattern: Redis pattern (e.g., "user:*", "session:123:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info("Cache pattern delete", pattern=pattern, deleted=deleted)
                return deleted
            return 0
            
        except Exception as e:
            logger.error("Cache pattern delete error", pattern=pattern, error=str(e))
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.exists(key)
            return bool(result)
        except Exception as e:
            logger.error("Cache exists error", key=key, error=str(e))
            return False
    
    async def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """Set expiration time for a key."""
        if not self.redis_client:
            return False
        
        try:
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            
            result = await self.redis_client.expire(key, ttl)
            return bool(result)
        except Exception as e:
            logger.error("Cache expire error", key=key, error=str(e))
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a numeric value in cache."""
        if not self.redis_client:
            return None
        
        try:
            result = await self.redis_client.incrby(key, amount)
            return result
        except Exception as e:
            logger.error("Cache increment error", key=key, error=str(e))
            return None
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache."""
        if not self.redis_client or not keys:
            return {}
        
        try:
            values = await self.redis_client.mget(keys)
            result = {}
            
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value.decode('utf-8'))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        result[key] = pickle.loads(value)
            
            hit_count = len(result)
            miss_count = len(keys) - hit_count
            
            for _ in range(hit_count):
                record_cache_operation("get", True)
            for _ in range(miss_count):
                record_cache_operation("get", False)
            
            return result
            
        except Exception as e:
            logger.error("Cache get_many error", keys=keys, error=str(e))
            return {}
    
    async def set_many(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set multiple values in cache."""
        if not self.redis_client or not mapping:
            return False
        
        try:
            # Serialize all values
            serialized_mapping = {}
            for key, value in mapping.items():
                try:
                    serialized_mapping[key] = json.dumps(value, default=str)
                except (TypeError, ValueError):
                    serialized_mapping[key] = pickle.dumps(value)
            
            # Use pipeline for atomic operation
            async with self.redis_client.pipeline() as pipe:
                await pipe.mset(serialized_mapping)
                
                # Set TTL for all keys if specified
                if ttl is not None:
                    if isinstance(ttl, timedelta):
                        ttl = int(ttl.total_seconds())
                    
                    for key in mapping.keys():
                        await pipe.expire(key, ttl)
                
                await pipe.execute()
            
            return True
            
        except Exception as e:
            logger.error("Cache set_many error", keys=list(mapping.keys()), error=str(e))
            return False


# Global cache manager instance
cache_manager = CacheManager()


# Convenience functions
async def get_cache(key: str, default: Any = None) -> Any:
    """Get value from cache."""
    return await cache_manager.get(key, default)


async def set_cache(
    key: str,
    value: Any,
    ttl: Optional[Union[int, timedelta]] = None
) -> bool:
    """Set value in cache."""
    return await cache_manager.set(key, value, ttl)


async def delete_cache(key: str) -> bool:
    """Delete key from cache."""
    return await cache_manager.delete(key)


async def invalidate_cache_pattern(pattern: str) -> int:
    """Delete all keys matching pattern."""
    return await cache_manager.delete_pattern(pattern)


# Cache decorators
def cache_result(
    key_prefix: str,
    ttl: Optional[Union[int, timedelta]] = None,
    key_builder: Optional[callable] = None
):
    """
    Decorator to cache function results.
    
    Args:
        key_prefix: Prefix for cache keys
        ttl: Time to live for cached results
        key_builder: Function to build cache key from function args
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default key building
                key_parts = [key_prefix]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_result = await get_cache(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await set_cache(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator