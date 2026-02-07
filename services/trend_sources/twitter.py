"""Twitter/X trend source implementation."""

import hashlib
from datetime import datetime
from typing import Optional

import tweepy
from tweepy import TweepyException

from config.settings import config
from models.trend import Trend, TrendSource
from utils.logger import get_logger
from .base import BaseTrendSource

logger = get_logger(__name__)


class TwitterTrendSource(BaseTrendSource):
    """Twitter/X trend detection using the Twitter API v2."""

    source_type = TrendSource.TWITTER

    def __init__(self):
        self.config = config.twitter
        self.client: Optional[tweepy.Client] = None
        self._init_client()

    def _init_client(self) -> None:
        """Initialize the Twitter API client."""
        if not self.is_configured():
            logger.warning("Twitter API not configured, using mock data")
            return

        try:
            self.client = tweepy.Client(
                bearer_token=self.config.bearer_token,
                consumer_key=self.config.api_key,
                consumer_secret=self.config.api_secret,
                access_token=self.config.access_token,
                access_token_secret=self.config.access_token_secret,
                wait_on_rate_limit=True,
            )
            logger.info("Twitter client initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Twitter client", error=str(e))
            self.client = None

    def is_configured(self) -> bool:
        """Check if Twitter API is configured."""
        return bool(self.config.bearer_token)

    async def fetch_trends(self, limit: int = 50) -> list[Trend]:
        """
        Fetch trending topics from Twitter.

        Note: Twitter API v2 has limited trending endpoint access.
        This implementation searches for crypto-related trending terms.
        """
        if not self.client:
            logger.warning("Twitter client not available, returning mock trends")
            return self._get_mock_trends(limit)

        trends = []
        crypto_keywords = [
            "crypto", "bitcoin", "ethereum", "memecoin", "defi",
            "nft", "web3", "altcoin", "token", "blockchain"
        ]

        try:
            for keyword in crypto_keywords[:5]:  # Limit API calls
                response = self.client.search_recent_tweets(
                    query=f"{keyword} -is:retweet lang:en",
                    max_results=min(limit, 100),
                    tweet_fields=["created_at", "public_metrics", "entities"],
                )

                if response.data:
                    trend = self._process_search_results(keyword, response)
                    if trend:
                        trends.append(trend)

        except TweepyException as e:
            logger.error("Twitter API error", error=str(e))
        except Exception as e:
            logger.error("Unexpected error fetching Twitter trends", error=str(e))

        return trends[:limit]

    def _process_search_results(self, keyword: str, response) -> Optional[Trend]:
        """Process Twitter search results into a Trend object."""
        tweets = response.data or []
        if not tweets:
            return None

        total_engagement = 0
        hashtags = set()

        for tweet in tweets:
            metrics = tweet.public_metrics or {}
            total_engagement += (
                metrics.get("like_count", 0) +
                metrics.get("retweet_count", 0) * 2 +
                metrics.get("reply_count", 0)
            )

            if tweet.entities and tweet.entities.get("hashtags"):
                for ht in tweet.entities["hashtags"]:
                    hashtags.add(ht["tag"].lower())

        raw_data = {
            "tweet_count": len(tweets),
            "total_engagement": total_engagement,
            "hashtags": list(hashtags),
        }

        return Trend(
            id=self._generate_trend_id(keyword),
            keyword=keyword,
            related_keywords=list(hashtags)[:10],
            source=self.source_type,
            virality_score=self.calculate_virality_score(raw_data),
            growth_rate=self.calculate_growth_rate(raw_data),
            volume=len(tweets),
            sentiment_score=0.5,  # Would need NLP for real sentiment
            raw_data=raw_data,
        )

    async def search_keyword(self, keyword: str, limit: int = 100) -> dict:
        """Search for specific keyword mentions on Twitter."""
        if not self.client:
            return {"error": "Twitter client not configured"}

        try:
            response = self.client.search_recent_tweets(
                query=f"{keyword} -is:retweet",
                max_results=min(limit, 100),
                tweet_fields=["created_at", "public_metrics"],
            )

            tweets = response.data or []
            return {
                "keyword": keyword,
                "count": len(tweets),
                "tweets": [
                    {
                        "text": t.text[:200],
                        "metrics": t.public_metrics,
                        "created_at": t.created_at.isoformat() if t.created_at else None,
                    }
                    for t in tweets[:20]
                ],
            }

        except TweepyException as e:
            logger.error("Twitter search error", keyword=keyword, error=str(e))
            return {"error": str(e)}

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
        """Check Twitter API connectivity."""
        if not self.client:
            return False

        try:
            self.client.get_me()
            return True
        except Exception:
            return False
