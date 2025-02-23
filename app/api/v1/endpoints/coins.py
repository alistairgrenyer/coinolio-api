from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_token_data
from app.models.enums import TierPrivileges
from app.services.auth import TokenData
from app.services.cache import RedisCache
from app.services.coingecko import CoinGeckoService

router = APIRouter(
    dependencies=[Depends(get_token_data)]
)
coingecko = CoinGeckoService()
cache = RedisCache()

# Cache durations
CACHE_DURATION = 60  # 1 minute for all users

@router.get("/prices")
async def get_coin_prices(
    ids: str = Query(..., description="Comma-separated list of coin ids"),
    vs_currency: str = Query(default="usd", description="The target currency of market data"),
) -> dict:
    """
    Get current prices for a list of coins.
    Guest accessable endpoint.
    """
    if not ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No coin ids provided"
        )
    # Check cache first
    cache_key = f"prices:{ids}:{vs_currency}"
    cached_data = await cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # Get fresh data from CoinGecko
    coin_ids = ids.split(",")
    data = await coingecko.get_coins_markets(vs_currency=vs_currency, ids=coin_ids)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more coins not found"
        )
    
    # Cache the response with a single duration for all users
    await cache.set(cache_key, data, expire=CACHE_DURATION)
    
    return data

@router.get("/historical/{coin_id}")
async def get_coin_history(
    coin_id: str,
    days: int = Query(default=1, le=365, description="Number of days of historical data"),
    vs_currency: str = Query(default="usd", description="The target currency of market data"),
    token_data: TokenData = Depends(get_token_data)
) -> dict:
    """
    Get historical price data for a coin.
    Guest accessable endpoint.
    Premium users get access to more historical data.
    """
    # Check user's data access limits
    max_days = TierPrivileges.get_historical_data_days(token_data.subscription_tier)
    
    if days > max_days:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You have reached your historical data limit ({max_days} days). Upgrade to Premium for more data."
        )
    
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
    token_data: TokenData = Depends(get_token_data)
) -> dict:
    """
    Get trending coins in the last 24 hours.
    Guest accessable endpoint.
    """
    cache_key = "trending_coins"
    cached_data = await cache.get(cache_key)
    if cached_data:
        return cached_data
    
    data = await coingecko.get_trending_coins()
    
    # Trending data can be cached longer since it updates less frequently
    await cache.set(cache_key, data, expire=300)  # 5 minutes for trending data
    
    return data
