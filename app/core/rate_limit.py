from fastapi import HTTPException, Request
from redis import Redis
import time
from app.core.config import get_settings

settings = get_settings()

class RateLimiter:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.public_rate_limit = 30  # requests per minute for public endpoints
        self.window = 60  # 1 minute window

    async def check_rate_limit(self, request: Request, is_authenticated: bool = False):
        if is_authenticated:
            return  # No rate limit for authenticated users
        
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        
        # Get current count
        current = self.redis.get(key)
        current_count = int(current) if current else 0
        
        if current_count >= self.public_rate_limit:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please register for higher limits."
            )
        
        pipe = self.redis.pipeline()
        if not current:
            pipe.setex(key, self.window, 1)
        else:
            pipe.incr(key)
        pipe.execute()

rate_limiter = RateLimiter(Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True
))
