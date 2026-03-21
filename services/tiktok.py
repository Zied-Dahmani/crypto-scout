"""Trend keyword source — Google Trends RSS feed (real-time, free, no auth).

Fetches what's actually trending right now on Google (people, memes, events, news).
These are the early signals — someone launches a memecoin for a viral topic
before it hits mainstream crypto coverage.

Falls back to mock keywords if the feed is unavailable.
"""

import re
import xml.etree.ElementTree as ET

import requests

from utils.logger import get_logger

logger = get_logger(__name__)

_FEED_URLS = [
    "https://trends.google.com/trending/rss?geo=US",
    "https://trends.google.com/trending/rss?geo=GB",
    "https://trends.google.com/trending/rss?geo=FR",
    "https://trends.google.com/trending/rss?geo=DE",
    "https://trends.google.com/trending/rss?geo=JP",
    "https://trends.google.com/trending/rss?geo=KR",
    "https://trends.google.com/trending/rss?geo=BR",
    "https://trends.google.com/trending/rss?geo=IN",
]
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; crypto-scout/1.0)"}
_TOP_N = 20

# Keywords matching these patterns are sports fixtures — skip them
_SPORTS_PATTERNS = [
    # Match formats
    r"\bvs\b", r"\bvs\.\b", r" – ", r" - ", r" x ", r" \d+[-:]\d+",
    r"\bmma\b", r"\bmotogp\b", r"\bformula\b", r"\bf1\b", r"\bnascar\b",
    # Club suffixes
    r"\bfc\b", r"\bsc\b", r"\bac\b", r"\butd\b", r"\bunited\b",
    r"\bcity\b", r"\btown\b", r"\brovers\b", r"\bwanderers\b",
    r"\bhotspur\b", r"\balbion\b", r"\broyal\b",
    # Club names
    r"\bpsg\b", r"\bbayern\b", r"\bdortmund\b", r"\bjuventus\b",
    r"\binter\b", r"\bbarcelona\b", r"\bmadrid\b", r"\barsenal\b",
    r"\bchelsea\b", r"\bliverpool\b", r"\bmanchester\b", r"\bwrexham\b",
    r"\bwerder\b", r"\bwolfsburg\b", r"\bfalkir\b",
    # Leagues / competitions
    r"\bnhl\b", r"\bnfl\b", r"\bnba\b", r"\bmlb\b", r"\bnfl\b",
    r"\bpremier league\b", r"\blaliga\b", r"\bbundesliga\b",
    r"\bserie a\b", r"\bligue 1\b", r"\bchampions league\b",
    r"\bworld cup\b", r"\bfa cup\b", r"\beuropa\b", r"\bimsa\b",
    r"\bopta\b",
]


def _is_non_latin(keyword: str) -> bool:
    """Skip keywords in Arabic, Japanese, Korean etc. — DEXScreener won't match."""
    non_latin = sum(1 for c in keyword if ord(c) > 0x024F)
    return non_latin > len(keyword) * 0.2


def _is_sports(keyword: str) -> bool:
    kw = keyword.lower()
    return any(re.search(p, kw) for p in _SPORTS_PATTERNS)


def _parse_traffic(traffic_str: str) -> int:
    """Parse '500K+' or '1M+' into an integer."""
    s = traffic_str.replace("+", "").replace(",", "").strip().upper()
    if s.endswith("M"):
        return int(float(s[:-1]) * 1_000_000)
    if s.endswith("K"):
        return int(float(s[:-1]) * 1_000)
    return int(s) if s.isdigit() else 0


def _fetch_rss(url: str) -> list[str]:
    resp = requests.get(url, headers=_HEADERS, timeout=10)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    ns = {"ht": "https://trends.google.com/trending/rss"}
    keywords = []
    for item in root.findall(".//item"):
        title = item.findtext("title", "").strip().lower()
        if not title or _is_non_latin(title):
            continue
        traffic_raw = item.findtext("ht:approx_traffic", "0", ns)
        traffic = _parse_traffic(traffic_raw)
        is_sports = _is_sports(title)
        # Keep sports only if extraordinary traffic (500k+) — Super Bowl level
        if is_sports and traffic < 500_000:
            logger.debug(f"trends: skipping routine fixture '{title}' ({traffic_raw})")
            continue
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
