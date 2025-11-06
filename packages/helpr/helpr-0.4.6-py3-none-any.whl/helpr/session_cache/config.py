import redis
from typing import Optional


class SessionCacheConfig:
    """Configuration class for SessionCache to manage Redis client."""
    
    _default_redis_client: Optional[redis.Redis] = None
    
    @classmethod
    def configure(cls, redis_client: redis.Redis):
        """
        Configure the default Redis client for SessionCache operations.
        
        Args:
            redis_client: Redis client instance to use for all SessionCache operations
        """
        if not isinstance(redis_client, redis.Redis):
            raise ValueError("redis_client must be an instance of redis.Redis")
        cls._default_redis_client = redis_client
    
    @classmethod
    def get_redis_client(cls) -> redis.Redis:
        """
        Get the configured Redis client.
        
        Returns:
            Redis client instance
            
        Raises:
            ValueError: If no Redis client has been configured
        """
        if cls._default_redis_client is None:
            raise ValueError(
                "Redis client not configured. Call SessionCacheConfig.configure(redis_client) first."
            )
        return cls._default_redis_client
    
    @classmethod
    def is_configured(cls) -> bool:
        """
        Check if Redis client has been configured.
        
        Returns:
            True if configured, False otherwise
        """
        return cls._default_redis_client is not None