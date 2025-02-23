from typing import Dict, List, Optional

import httpx

from app.core.config import get_settings

settings = get_settings()

class CoinGeckoService:
    def __init__(self):
        self.base_url = settings.COINGECKO_API_URL
        self.api_key = settings.COINGECKO_API_KEY
        self.headers = {"X-CG-Pro-API-Key": self.api_key} if self.api_key else {}

    async def get_coins_markets(self, vs_currency: str = "usd", ids: Optional[List[str]] = None) -> List[Dict]:
        """
        Get current data for multiple coins in a single request
        """
        params = {
            "vs_currency": vs_currency,
            "order": "market_cap_desc",
            "per_page": 250,
            "page": 1,
            "sparkline": False
        }
        if ids:
            params["ids"] = ",".join(ids)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/coins/markets",
                params=params,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_coin_price(self, coin_id: str, vs_currency: str = "usd") -> Dict:
        """
        Get current price of a single coin
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/simple/price",
                params={
                    "ids": coin_id,
                    "vs_currencies": vs_currency
                },
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_coin_history(
        self,
        coin_id: str,
        vs_currency: str = "usd",
        days: int = 1
    ) -> Dict:
        """
        Get historical market data for a coin
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/coins/{coin_id}/market_chart",
                params={
                    "vs_currency": vs_currency,
                    "days": days,
                    "interval": "daily" if days > 90 else "hourly"
                },
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_trending_coins(self) -> Dict:
        """
        Get trending coins data
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/search/trending",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
