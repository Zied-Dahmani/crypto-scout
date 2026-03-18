"""Social mention validation — mock data.

Returns a fixed mention count per keyword used to weight trend momentum.
Twitter scraping is blocked by Cloudflare from all server/proxy IPs.

To upgrade to real data in the future, see README — Twitter Setup.
"""

from utils.logger import get_logger

logger = get_logger(__name__)

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


def get_twitter_mentions(keyword: str) -> int:
    count = _MOCK_MENTIONS.get(keyword.lower(), 500)
    logger.debug(f"twitter: mock mentions for '{keyword}' = {count:,}")
    return count
