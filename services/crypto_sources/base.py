"""Base class for crypto data sources."""

from abc import ABC, abstractmethod
from typing import Optional

from models.cryptocurrency import Cryptocurrency


class BaseCryptoSource(ABC):
    """Abstract base class for cryptocurrency data sources."""

    @abstractmethod
    async def fetch_low_cap_coins(
        self,
        max_market_cap: float = 1_000_000,
        limit: int = 100
    ) -> list[Cryptocurrency]:
        """
        Fetch cryptocurrencies under a market cap threshold.

        Args:
            max_market_cap: Maximum market cap in USD
            limit: Maximum number of coins to return

        Returns:
            List of Cryptocurrency objects
        """
        pass

    @abstractmethod
    async def get_coin_details(self, coin_id: str) -> Optional[Cryptocurrency]:
        """
        Get detailed information for a specific coin.

        Args:
            coin_id: Unique identifier for the coin

        Returns:
            Cryptocurrency object or None if not found
        """
        pass

    @abstractmethod
    async def search_coins(self, query: str) -> list[Cryptocurrency]:
        """
        Search for coins by name or symbol.

        Args:
            query: Search query string

        Returns:
            List of matching Cryptocurrency objects
        """
        pass

    def is_configured(self) -> bool:
        """Check if the source is properly configured."""
        return True

    async def health_check(self) -> bool:
        """Check if the source API is accessible."""
        return True
