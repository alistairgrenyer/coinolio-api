import json
from typing import Any, Optional

import redis

from app.core.config import get_settings

settings = get_settings()

class RedisCache:
    def __init__(self):
        self.redis = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
        self.default_expire = settings.CACHE_EXPIRE_MINUTES * 60  # Convert to seconds

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        data = self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """Set value in cache"""
        expire = expire or self.default_expire
        self.redis.setex(
            key,
            expire,
            json.dumps(value)
        )

    async def delete(self, key: str) -> None:
        """Delete value from cache"""
        self.redis.delete(key)

    async def clear(self) -> None:
        """Clear all cache"""
        self.redis.flushdb()
