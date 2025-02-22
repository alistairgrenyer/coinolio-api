from fastapi import HTTPException, Request, status
from redis import asyncio as aioredis
import time
from typing import Optional

from app.core.config import get_settings
from app.models.enums import SubscriptionTier, TierPrivileges

settings = get_settings()

class RateLimiter:
    def __init__(self):
        self.redis = aioredis.from_url(settings.REDIS_URL)
        self.window = 60  # 1 minute window
        self.blacklist_duration = 3600  # 1 hour
    
    async def is_blacklisted(self, identifier: str) -> bool:
        """Check if a user/guest is blacklisted"""
        return await self.redis.get(f"blacklist:{identifier}") is not None
    
    async def blacklist_identifier(self, identifier: str):
        """Blacklist a user/guest for 1 hour"""
        await self.redis.setex(f"blacklist:{identifier}", self.blacklist_duration, "1")
    
    async def check_concurrent_requests(self, identifier: str, tier: SubscriptionTier) -> bool:
        """Check and update concurrent request count"""
        key = f"concurrent:{identifier}"
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, 10)  # Reset after 10 seconds
        return current <= TierPrivileges.get_rate_limits(tier)['concurrent_requests']
    
    async def check_rate_limit(
        self,
        request: Request,
        identifier: str,
        tier: Optional[SubscriptionTier] = None,
        payload_size: Optional[int] = None
    ) -> None:
        """Check rate limit for a request"""
        # Get limits for the tier
        tier = tier or SubscriptionTier.GUEST
        limits = TierPrivileges.get_rate_limits(tier)
        
        # Check if blacklisted
        if await self.is_blacklisted(identifier):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You have been temporarily blocked due to excessive requests"
            )
        
        # Check payload size
        if payload_size and payload_size > limits['max_payload_size']:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Request payload too large. Maximum size is {limits['max_payload_size'] // 1024}kb"
            )
        
        # Check concurrent requests
        if not await self.check_concurrent_requests(identifier, tier):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many concurrent requests"
            )
        
        # Get current timestamp
        now = int(time.time())
        window_key = f"ratelimit:{identifier}:{now // self.window}"
        
        # Get and increment request count
        requests = await self.redis.incr(window_key)
        if requests == 1:
            await self.redis.expire(window_key, self.window)
        
        # Check rate limit
        if requests > limits['requests_per_min']:
            # If significantly exceeded, blacklist the identifier
            if requests > limits['requests_per_min'] * 2:
                await self.blacklist_identifier(identifier)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You have been temporarily blocked due to excessive requests"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Please try again in {self.window - (now % self.window)} seconds",
                    headers={
                        'X-RateLimit-Limit': str(limits['requests_per_min']),
                        'X-RateLimit-Remaining': '0',
                        'X-RateLimit-Reset': str(self.window - (now % self.window))
                    }
                )
        
        # Set rate limit headers
        request.state.rate_limit_headers = {
            'X-RateLimit-Limit': str(limits['requests_per_min']),
            'X-RateLimit-Remaining': str(limits['requests_per_min'] - requests),
            'X-RateLimit-Reset': str(self.window - (now % self.window))
        }

rate_limiter = RateLimiter()
