import json
import functools
from typing import Callable, Any
from app.db.redis import redis_client
from app.core.logging import get_logger

logger = get_logger(__name__)


def cache_get(key: str) -> Any | None:
    """Get value from Redis cache."""
    try:
        client = redis_client.get_client()
        val = client.get(f"cache:{key}")
        if val:
            return json.loads(val)
    except Exception as e:
        logger.warning(f"Cache get failed for {key}: {e}")
    return None


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Set value in Redis cache with TTL in seconds."""
    try:
        client = redis_client.get_client()
        client.setex(f"cache:{key}", ttl, json.dumps(value, default=str))
    except Exception as e:
        logger.warning(f"Cache set failed for {key}: {e}")


def cache_delete(key: str) -> None:
    """Delete key from cache."""
    try:
        client = redis_client.get_client()
        client.delete(f"cache:{key}")
    except Exception as e:
        logger.warning(f"Cache delete failed for {key}: {e}")


def cache_invalidate_pattern(pattern: str) -> None:
    """Invalidate all keys matching pattern."""
    try:
        client = redis_client.get_client()
        keys = client.keys(f"cache:{pattern}")
        if keys:
            client.delete(*keys)
    except Exception as e:
        logger.warning(f"Cache invalidate failed for {pattern}: {e}")


def cached(key_prefix: str, ttl: int = 300) -> Callable:
    """Decorator for caching function results."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_key = f"{key_prefix}:{hash(str(args) + str(sorted(kwargs.items())))}"
            result = cache_get(cache_key)
            if result is not None:
                return result
            result = func(*args, **kwargs)
            if result is not None:
                cache_set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
