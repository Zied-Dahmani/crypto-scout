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
        """
        Return mock trends for testing without API access.

        Includes BOTH:
        - Mainstream viral topics (celebrities, events, memes, animals)
        - Crypto-specific trends

        The idea: catch ANY viral topic and find related memecoins.
        """
        mock_data = [
            # MAINSTREAM VIRAL TOPICS (non-crypto origin)
            {
                "keyword": "moo deng",
                "virality": 0.92,
                "volume": 45000,
                "category": "viral_animal",
                "context": "Baby pygmy hippo from Thailand zoo going viral",
                "related": ["baby hippo", "thailand", "cute animals", "moodeng"],
            },
            {
                "keyword": "hawk tuah",
                "virality": 0.88,
                "volume": 32000,
                "category": "viral_meme",
                "context": "Viral interview meme girl",
                "related": ["hawk tuah girl", "meme", "viral video"],
            },
            {
                "keyword": "chill guy",
                "virality": 0.85,
                "volume": 28000,
                "category": "viral_meme",
                "context": "Chill Guy meme character going viral on social media",
                "related": ["chill", "meme", "relatable", "cartoon dog"],
            },
            {
                "keyword": "griddy",
                "virality": 0.75,
                "volume": 18000,
                "category": "viral_dance",
                "context": "Dance celebration trend from sports",
                "related": ["dance", "celebration", "sports", "tiktok"],
            },
            {
                "keyword": "skibidi",
                "virality": 0.82,
                "volume": 25000,
                "category": "viral_meme",
                "context": "Skibidi toilet meme phenomenon",
                "related": ["skibidi toilet", "meme", "gen alpha", "youtube"],
            },
            # CRYPTO-ADJACENT TRENDS
            {
                "keyword": "penguin",
                "virality": 0.78,
                "volume": 15000,
                "category": "crypto_meme",
                "context": "Pudgy Penguins NFT and meme trend",
                "related": ["pudgy penguins", "nft", "cute", "crypto"],
            },
            {
                "keyword": "pepe",
                "virality": 0.72,
                "volume": 12000,
                "category": "crypto_meme",
                "context": "Classic meme with strong crypto presence",
                "related": ["frog", "meme", "rare pepe", "crypto"],
            },
            {
                "keyword": "dogwifhat",
                "virality": 0.68,
                "volume": 9500,
                "category": "crypto_meme",
                "context": "Dog with hat meme on Solana",
                "related": ["dog", "hat", "solana", "meme"],
            },
            # MORE MAINSTREAM TOPICS
            {
                "keyword": "trump",
                "virality": 0.90,
                "volume": 85000,
                "category": "politics",
                "context": "Political figure always trending",
                "related": ["election", "politics", "usa", "maga"],
            },
            {
                "keyword": "elon",
                "virality": 0.85,
                "volume": 52000,
                "category": "celebrity",
                "context": "Elon Musk tweets and news",
                "related": ["musk", "tesla", "x", "doge", "spacex"],
            },
            {
                "keyword": "baby shark",
                "virality": 0.65,
                "volume": 8000,
                "category": "viral_song",
                "context": "Children's song phenomenon",
                "related": ["shark", "kids", "song", "viral"],
            },
            {
                "keyword": "capybara",
                "virality": 0.70,
                "volume": 11000,
                "category": "viral_animal",
                "context": "Capybara memes and cute content",
                "related": ["ok i pull up", "chill", "animal", "meme"],
            },
        ]

        trends = []
        for data in mock_data[:limit]:
            trends.append(Trend(
                id=self._generate_trend_id(data["keyword"]),
                keyword=data["keyword"],
                related_keywords=data.get("related", [f"#{data['keyword']}"]),
                source=self.source_type,
                virality_score=data["virality"],
                growth_rate=data["volume"] / 24,
                volume=data["volume"],
                sentiment_score=0.65,
                raw_data={
                    "mock": True,
                    "type": "general_trend",
                    "category": data.get("category", "unknown"),
                    "context": data.get("context", ""),
                },
            ))

        return trends

    async def fetch_crypto_mentions(self, limit: int = 20) -> list[dict]:
        """
        Fetch crypto-specific posts mentioning coin symbols (mock data).

        This represents scanning crypto Twitter for direct coin mentions
        like $PENGU, $PEPE, $WIF etc.
        """
        logger.info(f"Fetching crypto mentions from Twitter (mock data, limit: {limit})")
        return self._get_mock_crypto_mentions(limit)

    def _get_mock_crypto_mentions(self, limit: int) -> list[dict]:
        """
        Return mock crypto-specific Twitter mentions.

        Includes coins related to BOTH:
        - Crypto-native memes (PEPE, WIF)
        - Mainstream viral trends (MOODENG, HAWKTUAH, CHILLGUY)
        """
        mock_mentions = [
            # MAINSTREAM TREND COINS (the alpha!)
            {
                "symbol": "MOODENG",
                "name": "Moo Deng",
                "mentions": 15000,
                "sentiment": 0.92,
                "sample_tweets": [
                    "🦛 $MOODENG is the play! Baby hippo taking over crypto!",
                    "Moo Deng went viral, $MOODENG going to $1 🚀",
                    "If you're not in $MOODENG you're ngmi, this hippo is everywhere",
                ],
                "influencer_mentions": 18,
                "avg_engagement": 720,
            },
            {
                "symbol": "HAWKTUAH",
                "name": "Hawk Tuah",
                "mentions": 9500,
                "sentiment": 0.85,
                "sample_tweets": [
                    "$HAWKTUAH memecoin launched! The meme girl has a token now 😂",
                    "Aping $HAWKTUAH, this meme is too viral to ignore",
                    "Hawk tuah girl coin pumping, degens are fast",
                ],
                "influencer_mentions": 12,
                "avg_engagement": 580,
            },
            {
                "symbol": "CHILLGUY",
                "name": "Chill Guy",
                "mentions": 11000,
                "sentiment": 0.88,
                "sample_tweets": [
                    "$CHILLGUY is the most relatable memecoin fr fr",
                    "Just being a chill guy and holding $CHILLGUY 😎",
                    "This meme is everywhere, $CHILLGUY easy 10x",
                ],
                "influencer_mentions": 15,
                "avg_engagement": 650,
            },
            {
                "symbol": "SKIBIDI",
                "name": "Skibidi Toilet",
                "mentions": 7200,
                "sentiment": 0.75,
                "sample_tweets": [
                    "$SKIBIDI for the gen alpha degens 🚽",
                    "Skibidi toilet meme won't die, neither will this coin",
                    "My kid showed me skibidi, now I'm buying $SKIBIDI",
                ],
                "influencer_mentions": 8,
                "avg_engagement": 420,
            },
            {
                "symbol": "CAPY",
                "name": "Capybara",
                "mentions": 5500,
                "sentiment": 0.82,
                "sample_tweets": [
                    "$CAPY ok I pull up 🫡",
                    "Capybara memes + crypto = $CAPY",
                    "Most chill animal, most chill coin $CAPY",
                ],
                "influencer_mentions": 6,
                "avg_engagement": 340,
            },
            # CRYPTO-NATIVE COINS
            {
                "symbol": "PENGU",
                "name": "Pudgy Penguins",
                "mentions": 8500,
                "sentiment": 0.82,
                "sample_tweets": [
                    "🚀 $PENGU breaking out! Pudgy Penguins community is insane!",
                    "$PENGU just got listed on a new DEX, volume pumping 📈",
                    "Bought more $PENGU, this penguin is going to Antarctica... I mean the moon 🐧🌙",
                ],
                "influencer_mentions": 12,
                "avg_engagement": 450,
            },
            {
                "symbol": "PEPE",
                "name": "Pepe",
                "mentions": 12000,
                "sentiment": 0.75,
                "sample_tweets": [
                    "$PEPE holders never sell! Diamond hands 💎🐸",
                    "The original memecoin $PEPE still has legs",
                    "$PEPE dip = buying opportunity, NFA",
                ],
                "influencer_mentions": 25,
                "avg_engagement": 890,
            },
            {
                "symbol": "WIF",
                "name": "dogwifhat",
                "mentions": 6200,
                "sentiment": 0.78,
                "sample_tweets": [
                    "$WIF is the next $DOGE, mark my words 🎩🐕",
                    "dogwifhat community strongest in Solana ecosystem",
                    "Just aped into $WIF, hat stays ON 🎩",
                ],
                "influencer_mentions": 8,
                "avg_engagement": 320,
            },
            {
                "symbol": "BONK",
                "name": "Bonk",
                "mentions": 4800,
                "sentiment": 0.70,
                "sample_tweets": [
                    "$BONK still the OG Solana memecoin 🦴",
                    "Bonk army assembling for the next leg up",
                    "$BONK undervalued at these levels imo",
                ],
                "influencer_mentions": 6,
                "avg_engagement": 280,
            },
            {
                "symbol": "TRUMP",
                "name": "MAGA Trump",
                "mentions": 18000,
                "sentiment": 0.72,
                "sample_tweets": [
                    "$TRUMP coin pumping after the rally 🇺🇸",
                    "Political memecoins are back, $TRUMP leading",
                    "Whether you love or hate him, $TRUMP prints money",
                ],
                "influencer_mentions": 20,
                "avg_engagement": 950,
            },
            {
                "symbol": "MOG",
                "name": "Mog Coin",
                "mentions": 2800,
                "sentiment": 0.80,
                "sample_tweets": [
                    "$MOG mogging all other memecoins rn 😎",
                    "The mog lifestyle is undefeated",
                    "$MOG chart looking beautiful, cup and handle forming",
                ],
                "influencer_mentions": 5,
                "avg_engagement": 380,
            },
        ]

        # Calculate virality score for each mention
        for mention in mock_mentions:
            mention["virality_score"] = self._calculate_mention_virality(mention)

        # Sort by virality
        mock_mentions.sort(key=lambda x: x["virality_score"], reverse=True)

        return mock_mentions[:limit]

    def _calculate_mention_virality(self, mention: dict) -> float:
        """Calculate virality score for crypto mentions."""
        # Factors: mention count, sentiment, influencer mentions, engagement
        mention_score = min(mention["mentions"] / 10000, 1.0) * 0.3
        sentiment_score = mention["sentiment"] * 0.2
        influencer_score = min(mention["influencer_mentions"] / 20, 1.0) * 0.25
        engagement_score = min(mention["avg_engagement"] / 500, 1.0) * 0.25

        return mention_score + sentiment_score + influencer_score + engagement_score

    async def health_check(self) -> bool:
        """Health check always returns True for mock data."""
        return True
