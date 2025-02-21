"""Mock rate limiter implementation for testing."""
from fastapi import Request, HTTPException
from .redis_mock import MockRedis

class MockRateLimiter:
    """Simple in-memory mock of RateLimiter for testing"""
    def __init__(self, redis_client: MockRedis):
        self.redis = redis_client
        self.public_rate_limit = 30  # requests per minute
        self.window = 60  # 1 minute window

    async def check_rate_limit(self, request: Request, is_authenticated: bool = False):
        """Check rate limit for a request"""
        if is_authenticated:
            return  # No rate limit for authenticated users
        
        client_ip = request.client.host if request.client else "127.0.0.1"
        key = f"rate_limit:{client_ip}"
        
        # Get current count
        current = self.redis.get(key)
        current_count = int(current.decode('utf-8')) if current else 0
        
        if current_count >= self.public_rate_limit:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please register for higher limits."
            )
        
        # Use pipeline for atomic increment and expire
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.window)
        pipe.execute()
