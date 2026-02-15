"""Services module."""

from .matching import MatchingService, RecommendationEngine
from .trend_sources import BaseTrendSource, TwitterTrendSource
from .crypto_sources import BaseCryptoSource, CoinGeckoSource
from .notifications import BaseNotificationService, WhatsAppNotificationService

__all__ = [
    "MatchingService",
    "RecommendationEngine",
    "BaseTrendSource",
    "TwitterTrendSource",
    "BaseCryptoSource",
    "CoinGeckoSource",
    "BaseNotificationService",
    "WhatsAppNotificationService",
]
