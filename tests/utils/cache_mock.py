"""Mock cache implementation for testing."""
from typing import Any, Optional
from .redis_mock import MockRedis

class MockCache:
    """Cache adapter using MockRedis"""
    def __init__(self, redis_client: MockRedis):
        self.redis = redis_client

    async def get(self, key: str):
        """Get value from cache"""
        return await self.redis.get_async(key)

    async def set(self, key: str, value: Any, expire: Optional[int] = None):
        """Set value in cache"""
        await self.redis.set_async(key, value)

    async def delete(self, key: str):
        """Delete value from cache"""
        await self.redis.delete(key)

    async def clear(self):
        """Clear all cache"""
        self.redis.clear()
