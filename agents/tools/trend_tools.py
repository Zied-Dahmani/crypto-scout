"""
Trend discovery tools for the AI agents.
"""

from langchain_core.tools import tool

from services.trend_sources import TwitterTrendSource
from utils.logger import get_logger

logger = get_logger(__name__)

# Initialize sources
twitter_source = TwitterTrendSource()


@tool
async def discover_twitter_trends(limit: int = 10) -> str:
    """
    Discover viral trending topics from Twitter/X.
    Returns trending crypto-related hashtags and topics with virality scores.

    Args:
        limit: Maximum number of trends to return (default 10)

    Returns:
        List of trending topics with virality metrics
    """
    logger.info(f"Discovering Twitter trends (limit: {limit})")

    trends = await twitter_source.fetch_trends(limit=limit)

    if not trends:
        return "No Twitter trends found. API might not be configured or rate limited."

    result = f"🐦 **Twitter Trends** (Found {len(trends)}):\n\n"
    for t in trends:
        result += f"• **{t.keyword}**\n"
        result += f"  Virality: {t.virality_score:.0%} | "
        result += f"Volume: {t.volume:,} | "
        result += f"Growth: {t.growth_rate:.1f}/hr\n"
        if t.related_keywords:
            result += f"  Related: {', '.join(t.related_keywords[:5])}\n"
        result += "\n"

    return result


@tool
async def search_social_topic(topic: str) -> str:
    """
    Search for a specific topic on Twitter.
    Use this to investigate a particular keyword or trend deeper.

    Args:
        topic: The topic/keyword to search for

    Returns:
        Detailed search results with mention counts and examples
    """
    logger.info(f"Searching topic '{topic}' on Twitter")

    twitter_results = await twitter_source.search_keyword(topic)

    if "error" in twitter_results:
        return f"No results found for '{topic}'"

    result = f"## Search Results: '{topic}'\n\n"
    result += f"🐦 **Twitter Results:**\n"
    result += f"  Mentions: {twitter_results.get('count', 0)}\n"

    if twitter_results.get("tweets"):
        result += "\n  **Sample tweets:**\n"
        for tweet in twitter_results["tweets"][:3]:
            result += f"    • {tweet['text'][:80]}...\n"
            metrics = tweet.get("metrics", {})
            result += f"      ❤️ {metrics.get('like_count', 0)} | "
            result += f"🔄 {metrics.get('retweet_count', 0)} | "
            result += f"💬 {metrics.get('reply_count', 0)}\n"

    return result


@tool
async def discover_crypto_mentions(limit: int = 10) -> str:
    """
    Discover viral crypto-specific posts from Twitter/X.
    This scans for direct coin mentions like $PENGU, $PEPE, $WIF etc.
    Returns coins being actively discussed with sentiment and engagement metrics.

    Args:
        limit: Maximum number of coins to return (default 10)

    Returns:
        List of crypto coins being mentioned with virality metrics
    """
    logger.info(f"Discovering crypto mentions on Twitter (limit: {limit})")

    mentions = await twitter_source.fetch_crypto_mentions(limit=limit)

    if not mentions:
        return "No crypto mentions found."

    result = f"💰 **Crypto Twitter Mentions** (Found {len(mentions)} coins being discussed):\n\n"
    for m in mentions:
        result += f"• **${m['symbol']}** ({m['name']})\n"
        result += f"  Virality: {m['virality_score']:.0%} | "
        result += f"Mentions: {m['mentions']:,} | "
        result += f"Sentiment: {m['sentiment']:.0%} bullish\n"
        result += f"  Influencers talking: {m['influencer_mentions']} | "
        result += f"Avg engagement: {m['avg_engagement']}\n"
        if m.get('sample_tweets'):
            result += f"  📝 \"{m['sample_tweets'][0][:60]}...\"\n"
        result += "\n"

    return result


# Export all trend tools
TREND_TOOLS = [
    discover_twitter_trends,
    discover_crypto_mentions,
    search_social_topic,
]
