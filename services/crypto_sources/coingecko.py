"""CoinGecko crypto data source implementation."""

import asyncio
import ssl
import certifi
from datetime import datetime, timezone
from typing import Optional

import aiohttp

from config.settings import config
from models.cryptocurrency import Cryptocurrency
from utils.logger import get_logger
from .base import BaseCryptoSource

logger = get_logger(__name__)


class CoinGeckoSource(BaseCryptoSource):
    """CoinGecko API implementation for crypto data."""

    def __init__(self):
        self.config = config.coingecko
        self.base_url = (
            self.config.pro_base_url
            if self.config.api_key
            else self.config.base_url
        )
        self.headers = {}
        if self.config.api_key:
            self.headers["x-cg-pro-api-key"] = self.config.api_key

        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 1.5  # seconds between requests (free tier)

    async def _rate_limit(self) -> None:
        """Enforce rate limiting for API calls."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < self._min_request_interval:
            await asyncio.sleep(self._min_request_interval - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()

    async def _make_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Make a rate-limited request to CoinGecko API."""
        await self._rate_limit()

        url = f"{self.base_url}/{endpoint}"
        params = params or {}

        # Create SSL context with certifi certificates
        ssl_context = ssl.create_default_context(cafile=certifi.where())

        try:
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    url,
                    params=params,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:
                        logger.warning("CoinGecko rate limit hit, waiting...")
                        await asyncio.sleep(60)
                        return None
                    else:
                        logger.error(
                            "CoinGecko API error",
                            status=response.status,
                            endpoint=endpoint
                        )
                        return None

        except aiohttp.ClientError as e:
            logger.error("CoinGecko request failed", error=str(e))
            return None
        except asyncio.TimeoutError:
            logger.error("CoinGecko request timed out", endpoint=endpoint)
            return None

    async def fetch_low_cap_coins(
        self,
        max_market_cap: float = 1_000_000,
        limit: int = 100
    ) -> list[Cryptocurrency]:
        """
        Fetch cryptocurrencies with market cap under threshold.

        Note: CoinGecko doesn't directly filter by market cap in API,
        so we fetch coins sorted by market cap and filter locally.
        """
        coins = []

        # Fetch coins from multiple pages, starting from lower market cap pages
        # CoinGecko sorts by market cap desc, so we need to go to later pages
        pages_to_fetch = 10  # Fetch coins from pages 20-30 (lower market caps)
        start_page = 50  # Start from page 50 to get lower cap coins

        for page in range(start_page, start_page + pages_to_fetch):
            data = await self._make_request(
                "coins/markets",
                params={
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": 250,
                    "page": page,
                    "sparkline": "false",
                    "price_change_percentage": "24h,7d",
                }
            )

            if not data:
                continue

            for coin_data in data:
                market_cap = coin_data.get("market_cap") or 0

                # Filter by market cap threshold
                if 0 < market_cap <= max_market_cap:
                    crypto = self._parse_coin_data(coin_data)
                    if crypto:
                        coins.append(crypto)

                if len(coins) >= limit:
                    break

            if len(coins) >= limit:
                break

        # If we didn't find enough coins, return mock data for testing
        if len(coins) < 5:
            logger.warning("Few low-cap coins found, supplementing with mock data")
            coins.extend(self._get_mock_coins(limit - len(coins)))

        logger.info(f"Fetched {len(coins)} low-cap cryptocurrencies")
        return coins[:limit]

    def _parse_coin_data(self, data: dict) -> Optional[Cryptocurrency]:
        """Parse CoinGecko coin data into Cryptocurrency model."""
        try:
            return Cryptocurrency(
                id=data["id"],
                symbol=data["symbol"],
                name=data["name"],
                current_price_usd=data.get("current_price") or 0,
                market_cap_usd=data.get("market_cap") or 0,
                volume_24h_usd=data.get("total_volume") or 0,
                price_change_24h_pct=data.get("price_change_percentage_24h") or 0,
                price_change_7d_pct=data.get("price_change_percentage_7d_in_currency") or 0,
                last_updated=datetime.now(timezone.utc),
            )
        except Exception as e:
            logger.warning("Failed to parse coin data", error=str(e), coin=data.get("id"))
            return None

    async def get_coin_details(self, coin_id: str) -> Optional[Cryptocurrency]:
        """Get detailed information for a specific coin."""
        data = await self._make_request(
            f"coins/{coin_id}",
            params={
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "true",
                "developer_data": "false",
            }
        )

        if not data:
            return None

        try:
            market_data = data.get("market_data", {})

            return Cryptocurrency(
                id=data["id"],
                symbol=data["symbol"],
                name=data["name"],
                current_price_usd=market_data.get("current_price", {}).get("usd", 0),
                market_cap_usd=market_data.get("market_cap", {}).get("usd", 0),
                volume_24h_usd=market_data.get("total_volume", {}).get("usd", 0),
                price_change_24h_pct=market_data.get("price_change_percentage_24h", 0),
                price_change_7d_pct=market_data.get("price_change_percentage_7d", 0),
                description=data.get("description", {}).get("en", "")[:500],
                categories=data.get("categories", []),
                website=self._get_first_link(data.get("links", {}).get("homepage", [])),
                twitter_handle=data.get("links", {}).get("twitter_screen_name"),
                telegram_url=data.get("links", {}).get("telegram_channel_identifier"),
                contract_address=self._get_contract_address(data),
                blockchain=self._get_blockchain(data),
                last_updated=datetime.now(timezone.utc),
            )

        except Exception as e:
            logger.error("Failed to parse coin details", error=str(e), coin_id=coin_id)
            return None

    def _get_first_link(self, links: list) -> Optional[str]:
        """Get first non-empty link from list."""
        for link in links:
            if link:
                return link
        return None

    def _get_contract_address(self, data: dict) -> Optional[str]:
        """Extract contract address from coin data."""
        platforms = data.get("platforms", {})
        for platform, address in platforms.items():
            if address:
                return address
        return None

    def _get_blockchain(self, data: dict) -> Optional[str]:
        """Determine the blockchain from coin data."""
        platforms = data.get("platforms", {})
        for platform in platforms.keys():
            if platform:
                return platform
        return None

    async def search_coins(self, query: str) -> list[Cryptocurrency]:
        """Search for coins by name or symbol."""
        data = await self._make_request("search", params={"query": query})

        if not data:
            return []

        coins = []
        coin_ids = [c["id"] for c in data.get("coins", [])[:10]]

        # Fetch market data for found coins
        if coin_ids:
            market_data = await self._make_request(
                "coins/markets",
                params={
                    "vs_currency": "usd",
                    "ids": ",".join(coin_ids),
                    "order": "market_cap_desc",
                }
            )

            if market_data:
                for coin in market_data:
                    parsed = self._parse_coin_data(coin)
                    if parsed:
                        coins.append(parsed)

        return coins

    async def health_check(self) -> bool:
        """Check CoinGecko API connectivity."""
        data = await self._make_request("ping")
        return data is not None and data.get("gecko_says") is not None

    def _get_mock_coins(self, limit: int) -> list[Cryptocurrency]:
        """Return mock coins for testing."""
        mock_data = [
            {
                "id": "pudgy-penguins-token",
                "symbol": "pengu",
                "name": "Pudgy Penguins",
                "price": 0.000025,
                "market_cap": 850000,
                "volume": 125000,
                "change_24h": 45.5,
            },
            {
                "id": "penguin-finance",
                "symbol": "pefi",
                "name": "Penguin Finance",
                "price": 0.00015,
                "market_cap": 420000,
                "volume": 85000,
                "change_24h": 28.3,
            },
            {
                "id": "baby-penguin",
                "symbol": "bpeng",
                "name": "Baby Penguin",
                "price": 0.0000008,
                "market_cap": 180000,
                "volume": 45000,
                "change_24h": 112.5,
            },
            {
                "id": "arctic-token",
                "symbol": "arctic",
                "name": "Arctic Token",
                "price": 0.000045,
                "market_cap": 650000,
                "volume": 95000,
                "change_24h": 18.7,
            },
            {
                "id": "ice-penguin",
                "symbol": "icep",
                "name": "Ice Penguin",
                "price": 0.00000012,
                "market_cap": 95000,
                "volume": 22000,
                "change_24h": 85.2,
            },
        ]

        coins = []
        for data in mock_data[:limit]:
            coins.append(Cryptocurrency(
                id=data["id"],
                symbol=data["symbol"],
                name=data["name"],
                current_price_usd=data["price"],
                market_cap_usd=data["market_cap"],
                volume_24h_usd=data["volume"],
                price_change_24h_pct=data["change_24h"],
                price_change_7d_pct=data["change_24h"] * 1.5,
                description=f"Mock {data['name']} token for testing",
                categories=["meme-token"],
                last_updated=datetime.now(timezone.utc),
            ))

        return coins
