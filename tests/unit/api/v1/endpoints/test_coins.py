import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from fastapi import HTTPException
from app.models.enums import SubscriptionTier
from app.core.rate_limit import rate_limiter

# Mock response data
MOCK_PRICES_DATA = [
    {
        "id": "bitcoin",
        "symbol": "btc",
        "current_price": 50000,
        "market_cap": 1000000000000
    },
    {
        "id": "ethereum",
        "symbol": "eth",
        "current_price": 3000,
        "market_cap": 500000000000
    }
]

MOCK_HISTORY_DATA = {
    "prices": [[datetime(2021, 2, 10, tzinfo=timezone.utc).timestamp() * 1000, 50000], [datetime(2021, 2, 11, tzinfo=timezone.utc).timestamp() * 1000, 51000]],
    "market_caps": [[datetime(2021, 2, 10, tzinfo=timezone.utc).timestamp() * 1000, 1000000000000], [datetime(2021, 2, 11, tzinfo=timezone.utc).timestamp() * 1000, 1020000000000]],
    "total_volumes": [[datetime(2021, 2, 10, tzinfo=timezone.utc).timestamp() * 1000, 60000000000], [datetime(2021, 2, 11, tzinfo=timezone.utc).timestamp() * 1000, 65000000000]]
}

MOCK_TRENDING_DATA = {
    "coins": [
        {
            "item": {
                "id": "bitcoin",
                "name": "Bitcoin",
                "symbol": "BTC",
                "market_cap_rank": 1
            }
        }
    ]
}

@pytest.fixture
def mock_coingecko():
    with patch("app.api.v1.endpoints.coins.coingecko") as mock:
        mock.get_coins_markets = AsyncMock(return_value=MOCK_PRICES_DATA)
        mock.get_coin_history = AsyncMock(return_value=MOCK_HISTORY_DATA)
        mock.get_trending_coins = AsyncMock(return_value=MOCK_TRENDING_DATA)
        yield mock


class TestCoinPrices:
    """Test cases for /coins/prices endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_coin_prices_cache_miss(self, client, mock_coingecko, mock_cache):
        """Test getting coin prices when not in cache"""
        async with client as async_client:
            response = await async_client.get("/api/v1/coins/prices?ids=bitcoin,ethereum")
            assert response.status_code == 200
            assert response.json() == MOCK_PRICES_DATA
            
            # Verify CoinGecko was called
            mock_coingecko.get_coins_markets.assert_called_once()
            
            # Verify data was cached
            cache_key = "prices:bitcoin,ethereum:usd"
            cached_data = await mock_cache.get(cache_key)
            assert cached_data == MOCK_PRICES_DATA

    @pytest.mark.asyncio
    async def test_get_coin_prices_cache_hit(self, client, mock_coingecko, mock_cache):
        """Test getting coin prices when in cache"""
        # Pre-populate cache
        cache_key = "prices:bitcoin,ethereum:usd"
        await mock_cache.set(cache_key, MOCK_PRICES_DATA)
        
        async with client as async_client:
            response = await async_client.get("/api/v1/coins/prices?ids=bitcoin,ethereum")
            assert response.status_code == 200
            assert response.json() == MOCK_PRICES_DATA
            
            # Verify CoinGecko was not called
            mock_coingecko.get_coins_markets.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_coin_prices_invalid_ids(self, client):
        """Test getting prices with invalid coin IDs"""
        async with client as async_client:
            response = await async_client.get("/api/v1/coins/prices?ids=")
            assert response.status_code == 422  # Validation error

class TestCoinHistory:
    """Test cases for /coins/historical endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_coin_history_cache_miss(self, client, mock_coingecko, mock_cache):
        """Test getting coin history when not in cache"""
        async with client as async_client:
            response = await async_client.get("/api/v1/coins/historical/bitcoin?days=7")
            assert response.status_code == 200
            assert response.json() == MOCK_HISTORY_DATA
            
            # Verify CoinGecko was called
            mock_coingecko.get_coin_history.assert_called_once()
            
            # Verify data was cached
            cache_key = "history:bitcoin:usd:7"
            cached_data = await mock_cache.get(cache_key)
            assert cached_data == MOCK_HISTORY_DATA

    @pytest.mark.asyncio
    async def test_get_coin_history_cache_hit(self, client, mock_coingecko, mock_cache):
        """Test getting coin history when in cache"""
        # Pre-populate cache
        cache_key = "history:bitcoin:usd:7"
        await mock_cache.set(cache_key, MOCK_HISTORY_DATA)
        
        async with client as async_client:
            response = await async_client.get("/api/v1/coins/historical/bitcoin?days=7")
            assert response.status_code == 200
            assert response.json() == MOCK_HISTORY_DATA
            
            # Verify CoinGecko was not called
            mock_coingecko.get_coin_history.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_coin_history_premium_user(self, authorized_client, mock_coingecko, mock_cache, test_user, db_session):
        """Test premium user accessing extended history"""
        # Upgrade user to premium
        test_user.subscription_tier = SubscriptionTier.PREMIUM
        db_session.commit()
        
        async with authorized_client as async_client:
            response = await async_client.get("/api/v1/coins/historical/bitcoin?days=365")
            assert response.status_code == 200
            assert response.json() == MOCK_HISTORY_DATA

    @pytest.mark.asyncio
    async def test_get_coin_history_free_user_limit(self, client):
        """Test free user cannot access extended history"""
        async with client as async_client:
            response = await async_client.get("/api/v1/coins/historical/bitcoin?days=365")
            assert response.status_code == 403

class TestTrendingCoins:
    """Test cases for /coins/trending endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_trending_coins_cache_miss(self, client, mock_coingecko, mock_cache):
        """Test getting trending coins when not in cache"""
        async with client as async_client:
            response = await async_client.get("/api/v1/coins/trending")
            assert response.status_code == 200
            assert response.json() == MOCK_TRENDING_DATA
            
            # Verify CoinGecko was called
            mock_coingecko.get_trending_coins.assert_called_once()
            
            # Verify data was cached
            cache_key = "trending:coins"
            cached_data = await mock_cache.get(cache_key)
            assert cached_data == MOCK_TRENDING_DATA

    @pytest.mark.asyncio
    async def test_get_trending_coins_cache_hit(self, client, mock_coingecko, mock_cache):
        """Test getting trending coins when in cache"""
        # Pre-populate cache
        cache_key = "trending:coins"
        await mock_cache.set(cache_key, MOCK_TRENDING_DATA)
        
        async with client as async_client:
            response = await async_client.get("/api/v1/coins/trending")
            assert response.status_code == 200
            assert response.json() == MOCK_TRENDING_DATA
            
            # Verify CoinGecko was not called
            mock_coingecko.get_trending_coins.assert_not_called()

class TestRateLimiting:
    """Test cases for rate limiting"""
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, client, mock_coingecko, mock_cache, mock_rate_limiter):
        """Test rate limiting for unauthenticated users"""
        # Simulate exceeding rate limit
        mock_rate_limiter.check_rate_limit.side_effect = HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please register for higher limits."
        )
        
        async with client as async_client:
            response = await async_client.get("/api/v1/coins/prices?ids=bitcoin")
            assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_authenticated_user_no_rate_limit(self, authorized_client, mock_coingecko, mock_cache, mock_rate_limiter):
        """Test authenticated users bypass rate limiting"""
        # Even with rate limit exceeded, authenticated users should pass
        mock_rate_limiter.check_rate_limit.return_value = None
        
        async with authorized_client as async_client:
            response = await async_client.get("/api/v1/coins/prices?ids=bitcoin")
            assert response.status_code == 200