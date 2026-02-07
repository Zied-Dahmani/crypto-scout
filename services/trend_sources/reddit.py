"""Reddit trend source implementation."""

import hashlib
from datetime import datetime
from typing import Optional

import praw
from praw.exceptions import PRAWException

from config.settings import config
from models.trend import Trend, TrendSource
from utils.logger import get_logger
from .base import BaseTrendSource

logger = get_logger(__name__)


class RedditTrendSource(BaseTrendSource):
    """Reddit trend detection using PRAW."""

    source_type = TrendSource.REDDIT

    def __init__(self):
        self.config = config.reddit
        self.reddit: Optional[praw.Reddit] = None
        self._init_client()

    def _init_client(self) -> None:
        """Initialize the Reddit API client."""
        if not self.is_configured():
            logger.warning("Reddit API not configured, using mock data")
            return

        try:
            self.reddit = praw.Reddit(
                client_id=self.config.client_id,
                client_secret=self.config.client_secret,
                user_agent=self.config.user_agent,
                check_for_async=False,
            )
            logger.info("Reddit client initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Reddit client", error=str(e))
            self.reddit = None

    def is_configured(self) -> bool:
        """Check if Reddit API is configured."""
        return bool(self.config.client_id and self.config.client_secret)

    async def fetch_trends(self, limit: int = 50) -> list[Trend]:
        """
        Fetch trending topics from crypto subreddits.

        Analyzes hot posts across configured subreddits to detect trends.
        """
        if not self.reddit:
            logger.warning("Reddit client not available, returning mock trends")
            return self._get_mock_trends(limit)

        trends_dict: dict[str, dict] = {}

        try:
            for subreddit_name in self.config.subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)

                    # Get hot posts
                    for post in subreddit.hot(limit=25):
                        keywords = self._extract_keywords(post.title)

                        for keyword in keywords:
                            if keyword not in trends_dict:
                                trends_dict[keyword] = {
                                    "posts": [],
                                    "total_score": 0,
                                    "total_comments": 0,
                                    "subreddits": set(),
                                }

                            trends_dict[keyword]["posts"].append({
                                "title": post.title,
                                "score": post.score,
                                "comments": post.num_comments,
                                "created": post.created_utc,
                            })
                            trends_dict[keyword]["total_score"] += post.score
                            trends_dict[keyword]["total_comments"] += post.num_comments
                            trends_dict[keyword]["subreddits"].add(subreddit_name)

                except PRAWException as e:
                    logger.warning(f"Error fetching from r/{subreddit_name}", error=str(e))
                    continue

        except Exception as e:
            logger.error("Unexpected error fetching Reddit trends", error=str(e))
            return self._get_mock_trends(limit)

        # Convert to Trend objects
        trends = []
        for keyword, data in sorted(
            trends_dict.items(),
            key=lambda x: x[1]["total_score"],
            reverse=True
        )[:limit]:
            raw_data = {
                "post_count": len(data["posts"]),
                "total_score": data["total_score"],
                "total_comments": data["total_comments"],
                "subreddits": list(data["subreddits"]),
            }

            trends.append(Trend(
                id=self._generate_trend_id(keyword),
                keyword=keyword,
                related_keywords=list(data["subreddits"]),
                source=self.source_type,
                virality_score=self.calculate_virality_score(raw_data),
                growth_rate=self.calculate_growth_rate(raw_data),
                volume=len(data["posts"]),
                sentiment_score=self._estimate_sentiment(data["total_score"]),
                raw_data=raw_data,
            ))

        return trends

    def _extract_keywords(self, title: str) -> list[str]:
        """Extract potential crypto-related keywords from post title."""
        # Common words to filter out
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall",
            "can", "need", "dare", "ought", "used", "to", "of", "in",
            "for", "on", "with", "at", "by", "from", "as", "into",
            "through", "during", "before", "after", "above", "below",
            "between", "under", "again", "further", "then", "once",
            "here", "there", "when", "where", "why", "how", "all",
            "each", "few", "more", "most", "other", "some", "such",
            "no", "nor", "not", "only", "own", "same", "so", "than",
            "too", "very", "just", "and", "but", "if", "or", "because",
            "until", "while", "this", "that", "these", "those", "what",
            "which", "who", "whom", "your", "yours", "his", "her", "its",
            "our", "their", "my", "me", "him", "you", "it", "we", "they",
            "crypto", "cryptocurrency", "coin", "token", "price", "buy",
            "sell", "hold", "moon", "pump", "dump", "dip", "ath", "atl",
        }

        # Extract words, filter, and return potential keywords
        words = title.lower().split()
        keywords = []

        for word in words:
            # Clean the word
            clean_word = "".join(c for c in word if c.isalnum())

            if (
                len(clean_word) >= 3 and
                clean_word not in stop_words and
                not clean_word.isdigit()
            ):
                keywords.append(clean_word)

        # Also check for $TICKER patterns
        import re
        tickers = re.findall(r'\$([A-Za-z]{2,10})', title)
        keywords.extend([t.lower() for t in tickers])

        return list(set(keywords))[:5]  # Return up to 5 unique keywords

    async def search_keyword(self, keyword: str, limit: int = 100) -> dict:
        """Search for specific keyword mentions on Reddit."""
        if not self.reddit:
            return {"error": "Reddit client not configured"}

        results = []

        try:
            for subreddit_name in self.config.subreddits[:3]:  # Limit subreddits
                subreddit = self.reddit.subreddit(subreddit_name)

                for post in subreddit.search(keyword, limit=limit // 3, time_filter="week"):
                    results.append({
                        "title": post.title,
                        "subreddit": subreddit_name,
                        "score": post.score,
                        "comments": post.num_comments,
                        "url": post.url,
                        "created": datetime.fromtimestamp(post.created_utc).isoformat(),
                    })

        except PRAWException as e:
            logger.error("Reddit search error", keyword=keyword, error=str(e))
            return {"error": str(e)}

        return {
            "keyword": keyword,
            "count": len(results),
            "posts": results[:20],
        }

    def calculate_virality_score(self, raw_data: dict) -> float:
        """Calculate virality score based on Reddit metrics."""
        post_count = raw_data.get("post_count", 0)
        total_score = raw_data.get("total_score", 0)
        total_comments = raw_data.get("total_comments", 0)
        subreddit_count = len(raw_data.get("subreddits", []))

        if post_count == 0:
            return 0.0

        # Engagement score (upvotes + comments)
        avg_engagement = (total_score + total_comments * 2) / post_count
        engagement_score = min(avg_engagement / 500, 1.0)

        # Cross-subreddit presence score
        spread_score = min(subreddit_count / 5, 1.0)

        # Volume score
        volume_score = min(post_count / 20, 1.0)

        return 0.5 * engagement_score + 0.3 * spread_score + 0.2 * volume_score

    def calculate_growth_rate(self, raw_data: dict) -> float:
        """Calculate growth rate (posts per time window)."""
        return float(raw_data.get("post_count", 0))

    def _estimate_sentiment(self, total_score: int) -> float:
        """Estimate sentiment based on upvote ratio."""
        # Higher scores generally indicate positive sentiment on Reddit
        if total_score > 1000:
            return 0.8
        elif total_score > 100:
            return 0.65
        elif total_score > 0:
            return 0.55
        else:
            return 0.4

    def _generate_trend_id(self, keyword: str) -> str:
        """Generate unique trend ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H")
        return hashlib.md5(f"reddit_{keyword}_{timestamp}".encode()).hexdigest()[:12]

    def _get_mock_trends(self, limit: int) -> list[Trend]:
        """Return mock trends for testing without API access."""
        mock_data = [
            {"keyword": "pudgypenguins", "virality": 0.88, "volume": 45, "score": 12500},
            {"keyword": "bonk", "virality": 0.75, "volume": 38, "score": 8200},
            {"keyword": "wif", "virality": 0.70, "volume": 32, "score": 6800},
            {"keyword": "pepe", "virality": 0.65, "volume": 28, "score": 5500},
            {"keyword": "floki", "virality": 0.58, "volume": 22, "score": 3200},
            {"keyword": "shib", "virality": 0.52, "volume": 18, "score": 2800},
        ]

        trends = []
        for data in mock_data[:limit]:
            trends.append(Trend(
                id=self._generate_trend_id(data["keyword"]),
                keyword=data["keyword"],
                related_keywords=["cryptocurrency", "memecoin", "altcoin"],
                source=self.source_type,
                virality_score=data["virality"],
                growth_rate=data["volume"] / 6,  # Posts per hour estimate
                volume=data["volume"],
                sentiment_score=0.7,
                raw_data={"mock": True, "total_score": data["score"]},
            ))

        return trends

    async def health_check(self) -> bool:
        """Check Reddit API connectivity."""
        if not self.reddit:
            return False

        try:
            # Try to access a subreddit to verify connection
            self.reddit.subreddit("cryptocurrency").id
            return True
        except Exception:
            return False
