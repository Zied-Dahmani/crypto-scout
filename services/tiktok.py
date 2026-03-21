"""Trend keyword source — Google Trends RSS feed (real-time, free, no auth).

Fetches what's actually trending right now on Google (people, memes, events, news).
These are the early signals — someone launches a memecoin for a viral topic
before it hits mainstream crypto coverage.

Falls back to mock keywords if the feed is unavailable.
"""

import xml.etree.ElementTree as ET

import requests

from utils.logger import get_logger

logger = get_logger(__name__)

_FEED_URLS = [
    "https://trends.google.com/trending/rss?geo=US",
    "https://trends.google.com/trending/rss?geo=GB",
]
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; crypto-scout/1.0)"}
_TOP_N = 15


def _fetch_rss(url: str) -> list[str]:
    resp = requests.get(url, headers=_HEADERS, timeout=10)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    ns = {"ht": "https://trends.google.com/trending/rss"}
    keywords = []
    for item in root.findall(".//item"):
        title = item.findtext("title", "").strip().lower()
        if title:
            keywords.append(title)
    return keywords


def fetch_tiktok_trends() -> list[dict]:
    seen: set[str] = set()
    trends = []

    for url in _FEED_URLS:
        try:
            keywords = _fetch_rss(url)
            for kw in keywords:
                if kw not in seen:
                    seen.add(kw)
                    trends.append({
                        "keyword": kw,
                        "hashtags": [f"#{kw.replace(' ', '')}"],
                        "views": 5_000_000,
                        "growth_rate": 100.0,
                        "source": "google_trends_rss",
                    })
        except Exception as e:
            logger.warning(f"trends: RSS feed failed for {url} ({e})")

    if trends:
        result = trends[:_TOP_N]
        logger.info(f"trends: {len(result)} real-time trending topics from Google RSS")
        return result

    logger.info("trends: using mock keyword seeds (Google RSS unavailable)")
    return [
        {"keyword": "moo deng",      "hashtags": ["#moodeng"],      "views": 620_000_000,   "growth_rate": 345.0, "source": "mock"},
        {"keyword": "chill guy",     "hashtags": ["#chillguy"],      "views": 980_000_000,   "growth_rate": 412.0, "source": "mock"},
        {"keyword": "skibidi",       "hashtags": ["#skibidi"],        "views": 1_400_000_000, "growth_rate": 88.0,  "source": "mock"},
        {"keyword": "hawk tuah",     "hashtags": ["#hawktuah"],       "views": 780_000_000,   "growth_rate": 290.0, "source": "mock"},
        {"keyword": "trump",         "hashtags": ["#trump"],          "views": 2_100_000_000, "growth_rate": 520.0, "source": "mock"},
        {"keyword": "pepe",          "hashtags": ["#pepe"],           "views": 450_000_000,   "growth_rate": 180.0, "source": "mock"},
        {"keyword": "dogwifhat",     "hashtags": ["#dogwifhat"],      "views": 320_000_000,   "growth_rate": 210.0, "source": "mock"},
        {"keyword": "capybara",      "hashtags": ["#capybara"],       "views": 560_000_000,   "growth_rate": 95.0,  "source": "mock"},
        {"keyword": "griddy",        "hashtags": ["#griddy"],         "views": 290_000_000,   "growth_rate": 155.0, "source": "mock"},
        {"keyword": "pudgy penguin", "hashtags": ["#pudgypenguins"],  "views": 180_000_000,   "growth_rate": 230.0, "source": "mock"},
    ]
