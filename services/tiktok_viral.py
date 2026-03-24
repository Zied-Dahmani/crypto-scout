"""Social validation — TikTok viral video count via Apify.

Searches each trending keyword on TikTok and counts how many recent videos
have gone viral (>500k plays). This replaces Twitter mention counts as the
social signal in the trend momentum score.

Requires APIFY_API_KEY. Falls back to a neutral score if unavailable.
"""

import time

import requests

import config
from utils.logger import get_logger

logger = get_logger(__name__)

_ACTOR_ID = "clockworks~tiktok-scraper"
_VIRAL_THRESHOLD = 500_000   # plays
_SCALE = 10_000              # multiply count to match momentum normalisation


def _count_viral_videos(keyword: str) -> int:
    """Search TikTok for keyword, return count of viral videos * scale."""
    resp = requests.post(
        f"https://api.apify.com/v2/acts/{_ACTOR_ID}/run-sync-get-dataset-items",
        params={
            "token": config.APIFY_API_KEY,
            "timeout": 60,
            "memory": 512,
        },
        json={
            "searchQueries": [keyword],
            "maxItems": 20,
            "shouldDownloadVideos": False,
            "shouldDownloadCovers": False,
        },
        timeout=90,
    )
    resp.raise_for_status()
    items = resp.json()

    viral = sum(
        1 for item in items
        if (item.get("playCount") or item.get("stats", {}).get("playCount") or 0) >= _VIRAL_THRESHOLD
    )
    scaled = viral * _SCALE
    logger.info(f"tiktok viral: '{keyword}' → {viral} viral videos (scaled={scaled:,})")
    return scaled


def get_twitter_mentions(keyword: str) -> int:
    """Return TikTok viral video count for a keyword (used as social signal).

    Priority: Apify TikTok search → neutral fallback (5,000)
    """
    if config.APIFY_API_KEY:
        try:
            return _count_viral_videos(keyword)
        except Exception as e:
            logger.warning(f"tiktok viral: failed for '{keyword}' ({e})")

    logger.debug(f"tiktok viral: no API key, using neutral score for '{keyword}'")
    return 5_000
