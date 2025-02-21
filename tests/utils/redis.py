"""Mock Redis implementation for testing."""
from typing import Any, Optional
from unittest.mock import MagicMock
import json

class MockRedis:
    """Mock Redis for both cache and rate limiter"""
    def __init__(self):
        self.data = {}
        self.default_expire = 300  # 5 minutes in seconds
        self.pipeline_mock = None

    def get(self, key: str) -> Optional[str]:
        """Synchronous get for rate limiter"""
        if isinstance(key, bytes):
            key = key.decode('utf-8')
        value = self.data.get(key)
        return value.encode('utf-8') if value else None

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> None:
        """Synchronous set for rate limiter"""
        if isinstance(key, bytes):
            key = key.decode('utf-8')
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        self.data[key] = str(value)

    def pipeline(self, transaction=None):
        """Get pipeline for rate limiter"""
        if not self.pipeline_mock:
            self.pipeline_mock = MagicMock()
            self.pipeline_mock.incr = MagicMock(return_value=1)
            self.pipeline_mock.expire = MagicMock()
            self.pipeline_mock.execute = MagicMock(return_value=[1, True])
        return self.pipeline_mock

    async def get_async(self, key: str):
        """Async get for cache"""
        if key in self.data:
            return json.loads(self.data[key])
        return None

    async def set_async(self, key: str, value: Any, expire: Optional[int] = None):
        """Async set for cache"""
        self.data[key] = json.dumps(value)

    async def delete(self, key: str):
        """Delete value"""
        if key in self.data:
            del self.data[key]

    def clear(self):
        """Clear all data"""
        self.data = {}
        if self.pipeline_mock:
            self.pipeline_mock.reset_mock()
