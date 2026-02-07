"""
Trend discovery tools for the AI agents.
"""

from langchain_core.tools import tool

from services.trend_sources import TwitterTrendSource, RedditTrendSource
from utils.logger import get_logger

logger = get_logger(__name__)

# Initialize sources
twitter_source = TwitterTrendSource()
reddit_source = RedditTrendSource()


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
async def discover_reddit_trends(limit: int = 10) -> str:
    """
    Discover viral trending topics from crypto Reddit communities.
    Scans subreddits like r/cryptocurrency, r/CryptoMoonShots, r/SatoshiStreetBets.

    Args:
        limit: Maximum number of trends to return (default 10)

    Returns:
        List of trending topics with engagement metrics
    """
    logger.info(f"Discovering Reddit trends (limit: {limit})")

    trends = await reddit_source.fetch_trends(limit=limit)

    if not trends:
        return "No Reddit trends found. API might not be configured."

    result = f"🔴 **Reddit Trends** (Found {len(trends)}):\n\n"
    for t in trends:
        result += f"• **{t.keyword}**\n"
        result += f"  Virality: {t.virality_score:.0%} | "
        result += f"Posts: {t.volume} | "
        result += f"Sentiment: {t.sentiment_score:.0%}\n"
        if t.raw_data.get("subreddits"):
            result += f"  Subreddits: {', '.join(t.raw_data['subreddits'][:3])}\n"
        result += "\n"

    return result


@tool
async def search_social_topic(topic: str, platform: str = "all") -> str:
    """
    Search for a specific topic across social media platforms.
    Use this to investigate a particular keyword or trend deeper.

    Args:
        topic: The topic/keyword to search for
        platform: Platform to search ('twitter', 'reddit', or 'all')

    Returns:
        Detailed search results with mention counts and examples
    """
    logger.info(f"Searching topic '{topic}' on {platform}")

    results = []

    if platform in ["twitter", "all"]:
        twitter_results = await twitter_source.search_keyword(topic)
        if "error" not in twitter_results:
            results.append(f"🐦 **Twitter Results:**\n"
                          f"  Mentions: {twitter_results.get('count', 0)}\n")

    if platform in ["reddit", "all"]:
        reddit_results = await reddit_source.search_keyword(topic)
        if "error" not in reddit_results:
            results.append(f"🔴 **Reddit Results:**\n"
                          f"  Posts: {reddit_results.get('count', 0)}\n")
            if reddit_results.get("posts"):
                results.append("  Top posts:\n")
                for post in reddit_results["posts"][:3]:
                    results.append(f"    • {post['title'][:60]}... "
                                  f"(↑{post['score']})\n")

    if not results:
        return f"No results found for '{topic}' on {platform}"

    return f"## Search Results: '{topic}'\n\n" + "\n".join(results)


# Export all trend tools
TREND_TOOLS = [
    discover_twitter_trends,
    discover_reddit_trends,
    search_social_topic,
]
