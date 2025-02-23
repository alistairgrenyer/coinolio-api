"""Test cases for the coins endpoints"""
from unittest.mock import AsyncMock, patch

import pytest

from app.models.enums import SubscriptionTier

# Test data
MOCK_PRICES_DATA = {
    "data": [
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
}

MOCK_HISTORY_DATA = {
    "prices": [[1623456789000, 50000]],
    "market_caps": [[1623456789000, 1000000000000]],
    "total_volumes": [[1623456789000, 60000000000]]
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
def mock_deps():
    """Mock all dependencies for endpoints"""
    cache_mock = AsyncMock()
    cache_mock.get = AsyncMock(return_value=None)  # Default to cache miss
    cache_mock.set = AsyncMock()
    cache_mock.delete = AsyncMock()
    
    coingecko_mock = AsyncMock()
    coingecko_mock.get_coins_markets = AsyncMock(return_value=MOCK_PRICES_DATA)
    coingecko_mock.get_coin_history = AsyncMock(return_value=MOCK_HISTORY_DATA)  # Fixed method name
    coingecko_mock.get_trending_coins = AsyncMock(return_value=MOCK_TRENDING_DATA)
    
    with patch("app.api.v1.endpoints.coins.cache", cache_mock), \
         patch("app.api.v1.endpoints.coins.coingecko", coingecko_mock):
        yield {
            "cache": cache_mock,
            "coingecko": coingecko_mock
        }

class TestCoinPrices:
    """Test cases for /coins/prices endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_coin_prices_cache_miss(self, authorized_client, mock_deps):
        """Test getting coin prices when not in cache"""
        response = authorized_client.get("/api/v1/coins/prices?ids=bitcoin,ethereum")
        assert response.status_code == 200
        assert response.json() == MOCK_PRICES_DATA
        
        mock_deps["coingecko"].get_coins_markets.assert_called_once()
        mock_deps["cache"].set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_coin_prices_cache_hit(self, authorized_client, mock_deps):
        """Test getting coin prices when in cache"""
        mock_deps["cache"].get.return_value = MOCK_PRICES_DATA
        
        response = authorized_client.get("/api/v1/coins/prices?ids=bitcoin,ethereum")
        assert response.status_code == 200
        assert response.json() == MOCK_PRICES_DATA
        
        mock_deps["coingecko"].get_coins_markets.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_coin_prices_invalid_ids(self, authorized_client):
        """Test getting prices with invalid coin IDs"""
        response = authorized_client.get("/api/v1/coins/prices?ids=")
        assert response.status_code == 422

class TestCoinHistory:
    """Test cases for /coins/historical endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_coin_history_premium_user(self, premium_authorized_client, mock_deps, test_premium_user):
        """Test getting coin history as premium user"""
        
        response = premium_authorized_client.get("/api/v1/coins/historical/bitcoin?days=365")
        assert response.status_code == 200
        assert response.json() == MOCK_HISTORY_DATA
        
        mock_deps["coingecko"].get_coin_history.assert_called_once()  # Fixed method name
        mock_deps["cache"].set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_coin_history_free_user_limit(self, authorized_client, mock_deps, test_user):
        """Test historical data limits for free users"""
        test_user.subscription_tier = SubscriptionTier.FREE
        
        response = authorized_client.get("/api/v1/coins/historical/bitcoin?days=31")
        assert response.status_code == 403

class TestTrendingCoins:
    """Test cases for /coins/trending endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_trending_coins_cache_miss(self, authorized_client, mock_deps):
        """Test getting trending coins when not in cache"""
        response = authorized_client.get("/api/v1/coins/trending")
        assert response.status_code == 200
        assert response.json() == MOCK_TRENDING_DATA
        
        mock_deps["coingecko"].get_trending_coins.assert_called_once()
        mock_deps["cache"].set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_trending_coins_cache_hit(self, authorized_client, mock_deps):
        """Test getting trending coins when in cache"""
        mock_deps["cache"].get.return_value = MOCK_TRENDING_DATA
        
        response = authorized_client.get("/api/v1/coins/trending")
        assert response.status_code == 200
        assert response.json() == MOCK_TRENDING_DATA
        
        mock_deps["coingecko"].get_trending_coins.assert_not_called()