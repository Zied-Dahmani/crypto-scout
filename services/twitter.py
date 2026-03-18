"""Twitter mention validation — free scraping via twscrape.

twscrape uses a regular free Twitter account (no paid API needed).
It hits Twitter's internal mobile API, same as the official app.

Fallback chain: twscrape → mock data
"""

import asyncio
from pathlib import Path

import config
from utils.logger import get_logger

logger = get_logger(__name__)

_DB_PATH = str(Path(__file__).parent.parent / ".twscrape_accounts.db")

_MOCK_MENTIONS: dict[str, int] = {
    "moo deng":      28_400,
    "chill guy":     52_100,
    "skibidi":       18_700,
    "hawk tuah":     35_600,
    "trump":        820_000,
    "pepe":          91_200,
    "dogwifhat":     44_800,
    "capybara":      12_300,
    "griddy":         8_900,
    "pudgy penguin": 31_500,
}

_scraper_ready: bool = False


async def _ensure_scraper_ready(api) -> bool:
    global _scraper_ready
    if _scraper_ready:
        return True

    username = config.TWITTER_SCRAPER_USERNAME
    password = config.TWITTER_SCRAPER_PASSWORD
    email = config.TWITTER_SCRAPER_EMAIL

    if not all([username, password, email]):
        return False

    try:
        await api.pool.add_account(username, password, email, email)
        await api.pool.login_all()
        _scraper_ready = True
        logger.info("twitter: scraper account logged in")
        return True
    except Exception as e:
        logger.warning(f"twitter: scraper login failed ({e})")
        return False


async def _scrape_mentions(keyword: str) -> int:
    from twscrape import API, gather

    api = API(_DB_PATH)
    if not await _ensure_scraper_ready(api):
        return 0

    try:
        query = f'"{keyword}" -is:retweet lang:en'
        tweets = await gather(api.search(query, limit=100))
        scaled = len(tweets) * 1_000
        logger.info(f"twitter: '{keyword}' → {len(tweets)} tweets (scaled={scaled:,})")
        return scaled
    except Exception as e:
        logger.warning(f"twitter: scrape failed for '{keyword}' ({e})")
        return 0


def get_twitter_mentions(keyword: str) -> int:
    """Return mention count for a keyword. Falls back to mock on failure."""
    has_scraper = all([
        config.TWITTER_SCRAPER_USERNAME,
        config.TWITTER_SCRAPER_PASSWORD,
        config.TWITTER_SCRAPER_EMAIL,
    ])

    if has_scraper:
        try:
            count = asyncio.run(_scrape_mentions(keyword))
            if count > 0:
                return count
        except Exception as e:
            logger.warning(f"twitter: asyncio error for '{keyword}' ({e})")

    count = _MOCK_MENTIONS.get(keyword.lower(), 500)
    logger.debug(f"twitter: mock mentions for '{keyword}' = {count:,}")
    return count
