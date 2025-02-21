from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.core.deps import get_optional_current_user, check_rate_limit
from app.services.coingecko import CoinGeckoService
from app.services.cache import RedisCache
from app.models.user import User
from app.models.enums import SubscriptionTier, TIER_LIMITS

router = APIRouter()
coingecko = CoinGeckoService()
cache = RedisCache()

# Cache durations
CACHE_DURATION = 60  # 1 minute for all users

@router.get("/prices")
async def get_coin_prices(
    ids: str = Query(..., description="Comma-separated list of coin ids"),
    vs_currency: str = Query(default="usd", description="The target currency of market data"),
    _: None = Depends(check_rate_limit),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> dict:
    """
    Get current prices for a list of coins.
    Public endpoint with rate limiting for unauthenticated users.
    """
    # Check cache first
    cache_key = f"prices:{ids}:{vs_currency}"
    cached_data = await cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # Get fresh data from CoinGecko
    coin_ids = ids.split(",")
    data = await coingecko.get_coins_markets(vs_currency=vs_currency, ids=coin_ids)
    
    # Cache the response with a single duration for all users
    await cache.set(cache_key, data, expire=CACHE_DURATION)
    
    return data

@router.get("/historical/{coin_id}")
async def get_coin_history(
    coin_id: str,
    days: int = Query(default=1, le=365, description="Number of days of historical data"),
    vs_currency: str = Query(default="usd", description="The target currency of market data"),
    _: None = Depends(check_rate_limit),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> dict:
    """
    Get historical price data for a coin.
    Public endpoint with rate limiting for unauthenticated users.
    Premium users get access to more historical data.
    """
    # Check user's data access limits
    max_days = TIER_LIMITS[
        current_user.subscription_tier if current_user 
        else SubscriptionTier.FREE
    ]["historical_data_days"]
    
    if days > max_days:
        days = max_days
    
    # Check cache
    cache_key = f"history:{coin_id}:{vs_currency}:{days}"
    cached_data = await cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # Get fresh data from CoinGecko
    data = await coingecko.get_coin_history(coin_id, vs_currency, days)
    
    # Cache the response with a single duration for all users
    await cache.set(cache_key, data, expire=CACHE_DURATION)
    
    return data

@router.get("/trending")
async def get_trending_coins(
    _: None = Depends(check_rate_limit),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> dict:
    """
    Get trending coins in the last 24 hours.
    Public endpoint with rate limiting for unauthenticated users.
    """
    cache_key = "trending_coins"
    cached_data = await cache.get(cache_key)
    if cached_data:
        return cached_data
    
    data = await coingecko.get_trending_coins()
    
    # Trending data can be cached longer since it updates less frequently
    await cache.set(cache_key, data, expire=300)  # 5 minutes for trending data
    
    return data
