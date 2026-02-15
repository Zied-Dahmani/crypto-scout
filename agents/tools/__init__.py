"""Agent tools module."""

from .trend_tools import (
    discover_twitter_trends,
    search_social_topic,
    TREND_TOOLS,
)
from .crypto_tools import (
    fetch_low_cap_cryptos,
    search_crypto,
    get_crypto_details,
    CRYPTO_TOOLS,
)
from .analysis_tools import (
    analyze_trend_match,
    calculate_investment_score,
    generate_recommendation,
    ANALYSIS_TOOLS,
)

ALL_TOOLS = TREND_TOOLS + CRYPTO_TOOLS + ANALYSIS_TOOLS

__all__ = [
    "discover_twitter_trends",
    "search_social_topic",
    "fetch_low_cap_cryptos",
    "search_crypto",
    "get_crypto_details",
    "analyze_trend_match",
    "calculate_investment_score",
    "generate_recommendation",
    "TREND_TOOLS",
    "CRYPTO_TOOLS",
    "ANALYSIS_TOOLS",
    "ALL_TOOLS",
]
