"""Twitter/X trend source implementation (using mock data)."""

import hashlib
from datetime import datetime

from config.settings import config
from models.trend import Trend, TrendSource
from utils.logger import get_logger
from .base import BaseTrendSource

logger = get_logger(__name__)


class TwitterTrendSource(BaseTrendSource):
    """Twitter/X trend detection using mock data (API disabled for cost reduction)."""

    source_type = TrendSource.TWITTER

    def __init__(self):
        self.config = config.twitter
        # API client initialization disabled - using mock data only
        logger.info("Twitter source initialized (using mock data for cost reduction)")

    def is_configured(self) -> bool:
        """Always returns True since we use mock data."""
        return True

    async def fetch_trends(self, limit: int = 50) -> list[Trend]:
        """
        Fetch trending topics from Twitter (using mock data).

        Note: Real API calls are disabled for cost reduction.
        Returns simulated trending crypto topics with realistic metrics.
        """
        logger.info(f"Fetching Twitter trends (mock data, limit: {limit})")
        return self._get_mock_trends(limit)

    async def search_keyword(self, keyword: str, limit: int = 100) -> dict:
        """Search for specific keyword mentions on Twitter (mock data)."""
        logger.info(f"Searching Twitter for '{keyword}' (mock data)")

        return {
            "keyword": keyword,
            "count": 150,
            "tweets": [
                {
                    "text": f"🚀 {keyword.upper()} is going to the moon! #crypto #memecoin",
                    "metrics": {"like_count": 245, "retweet_count": 89, "reply_count": 32},
                    "created_at": datetime.utcnow().isoformat(),
                },
                {
                    "text": f"Just bought some ${keyword.upper()}! Let's go! 🔥",
                    "metrics": {"like_count": 128, "retweet_count": 45, "reply_count": 18},
                    "created_at": datetime.utcnow().isoformat(),
                },
                {
                    "text": f"${keyword.upper()} looking bullish today 📈",
                    "metrics": {"like_count": 87, "retweet_count": 23, "reply_count": 12},
                    "created_at": datetime.utcnow().isoformat(),
                },
            ],
        }

    def calculate_virality_score(self, raw_data: dict) -> float:
        """Calculate virality score based on engagement metrics."""
        tweet_count = raw_data.get("tweet_count", 0)
        engagement = raw_data.get("total_engagement", 0)

        if tweet_count == 0:
            return 0.0

        # Normalize engagement per tweet, max score at 1000 avg engagement
        avg_engagement = engagement / tweet_count
        engagement_score = min(avg_engagement / 1000, 1.0)

        # Volume score, max at 100 tweets
        volume_score = min(tweet_count / 100, 1.0)

        # Combined weighted score
        return 0.6 * engagement_score + 0.4 * volume_score

    def calculate_growth_rate(self, raw_data: dict) -> float:
        """Calculate growth rate (simplified as tweets per search window)."""
        return float(raw_data.get("tweet_count", 0))

    def _generate_trend_id(self, keyword: str) -> str:
        """Generate unique trend ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H")
        return hashlib.md5(f"twitter_{keyword}_{timestamp}".encode()).hexdigest()[:12]

    def _get_mock_trends(self, limit: int) -> list[Trend]:
        """Return mock trends for testing without API access."""
        mock_data = [
            {"keyword": "penguin", "virality": 0.85, "volume": 15000},
            {"keyword": "pepe", "virality": 0.72, "volume": 8500},
            {"keyword": "dogwifhat", "virality": 0.68, "volume": 6200},
            {"keyword": "bonk", "virality": 0.55, "volume": 4100},
            {"keyword": "memecoin", "virality": 0.50, "volume": 3500},
        ]

        trends = []
        for data in mock_data[:limit]:
            trends.append(Trend(
                id=self._generate_trend_id(data["keyword"]),
                keyword=data["keyword"],
                related_keywords=[f"#{data['keyword']}", "crypto", "memecoin"],
                source=self.source_type,
                virality_score=data["virality"],
                growth_rate=data["volume"] / 24,
                volume=data["volume"],
                sentiment_score=0.65,
                raw_data={"mock": True},
            ))

        return trends

    async def health_check(self) -> bool:
        """Health check always returns True for mock data."""
        return True
