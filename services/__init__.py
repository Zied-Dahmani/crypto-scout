"""Services module."""

from .matching import MatchingService, RecommendationEngine
from .trend_sources import BaseTrendSource, TwitterTrendSource, RedditTrendSource
from .crypto_sources import BaseCryptoSource, CoinGeckoSource
from .notifications import (
    BaseNotificationService,
    TelegramNotificationService,
    WhatsAppNotificationService,
)

__all__ = [
    "MatchingService",
    "RecommendationEngine",
    "BaseTrendSource",
    "TwitterTrendSource",
    "RedditTrendSource",
    "BaseCryptoSource",
    "CoinGeckoSource",
    "BaseNotificationService",
    "TelegramNotificationService",
    "WhatsAppNotificationService",
]
