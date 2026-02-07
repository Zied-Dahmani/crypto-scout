"""Base class for trend sources."""

from abc import ABC, abstractmethod
from typing import Optional

from models.trend import Trend, TrendSource


class BaseTrendSource(ABC):
    """Abstract base class for trend detection sources."""

    source_type: TrendSource

    @abstractmethod
    async def fetch_trends(self, limit: int = 50) -> list[Trend]:
        """
        Fetch current trending topics.

        Args:
            limit: Maximum number of trends to return

        Returns:
            List of Trend objects
        """
        pass

    @abstractmethod
    async def search_keyword(self, keyword: str, limit: int = 100) -> dict:
        """
        Search for mentions of a specific keyword.

        Args:
            keyword: Keyword to search for
            limit: Maximum results to return

        Returns:
            Dictionary with search results and metrics
        """
        pass

    @abstractmethod
    def calculate_virality_score(self, raw_data: dict) -> float:
        """
        Calculate virality score from raw metrics.

        Args:
            raw_data: Raw data from the source

        Returns:
            Virality score between 0 and 1
        """
        pass

    @abstractmethod
    def calculate_growth_rate(self, raw_data: dict) -> float:
        """
        Calculate growth rate from raw metrics.

        Args:
            raw_data: Raw data from the source

        Returns:
            Growth rate (mentions per hour or similar)
        """
        pass

    def is_configured(self) -> bool:
        """Check if the source is properly configured with API keys."""
        return True

    async def health_check(self) -> bool:
        """Check if the source API is accessible."""
        return True
