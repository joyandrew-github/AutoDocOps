import redis
from typing import Optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RedisClient:
    """Redis client wrapper."""
    
    def __init__(self) -> None:
        self.client: Optional[redis.Redis] = None
    
    def connect(self) -> None:
        """Establish connection to Redis."""
        try:
            self.client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30,
            )
            # Test connection
            self.client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def close(self) -> None:
        """Close Redis connection."""
        if self.client:
            self.client.close()
            logger.info("Redis connection closed")
    
    def get_client(self) -> redis.Redis:
        """Get Redis client instance."""
        if not self.client:
            raise RuntimeError("Redis client not initialized. Call connect() first.")
        return self.client


# Global Redis client instance
redis_client = RedisClient()


def get_redis_client() -> RedisClient:
    """Get Redis client instance."""
    return redis_client


def init_redis() -> None:
    """Initialize Redis connection."""
    redis_client.connect()
