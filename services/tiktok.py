"""Trend keyword source — Apify TikTok scraper with mock fallback.

Real data: Apify runs clockworks/tiktok-scraper on their infrastructure,
returning actual trending hashtags with view counts. No IP blocks, no auth issues.

Fallback: fixed mock keywords when APIFY_API_KEY is not set.

To enable real data:
  1. Sign up at apify.com (free tier — $5/month credit)
  2. Go to Settings → Integrations → copy your API token
  3. Add APIFY_API_KEY=<token> to .env and GitHub secrets
"""

import config
from utils.logger import get_logger

logger = get_logger(__name__)

_ACTOR_ID = "clockworks~tiktok-scraper"
_MIN_VIEWS = 500_000
_TOP_N = 10


def _fetch_from_apify() -> list[dict]:
    import requests

    logger.info("tiktok: fetching trending from Apify")

    run_input = {
        "searchSection": "/trending",
        "maxItems": 50,
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False,
        "shouldDownloadSubtitles": False,
    }

    resp = requests.post(
        f"https://api.apify.com/v2/acts/{_ACTOR_ID}/run-sync-get-dataset-items",
        params={"token": config.APIFY_API_KEY, "timeout": 120, "memory": 512},
        json=run_input,
        timeout=150,
    )
    resp.raise_for_status()
    items = resp.json()

    if not items:
        logger.warning("tiktok: Apify returned 0 items")
        return []

    from collections import defaultdict
    import re

    keyword_stats: dict = defaultdict(lambda: {"views": 0, "video_count": 0})

    for item in items:
        views = item.get("playCount") or item.get("stats", {}).get("playCount") or 0
        text = item.get("text") or item.get("desc") or ""
        tags = re.findall(r"#(\w+)", text)
        for tag in tags:
            kw = tag.lower()
            keyword_stats[kw]["views"] += views
            keyword_stats[kw]["video_count"] += 1

    trends = []
    for kw, stats in keyword_stats.items():
        if stats["views"] < _MIN_VIEWS:
            continue
        avg_views = stats["views"] / max(stats["video_count"], 1)
        trends.append({
            "keyword": kw,
            "hashtags": [f"#{kw}"],
            "views": stats["views"],
            "growth_rate": round(min(avg_views / 1_000_000 * 100, 999.0), 1),
            "source": "tiktok",
        })

    trends.sort(key=lambda x: x["views"], reverse=True)
    result = trends[:_TOP_N]
    logger.info(f"tiktok: {len(result)} trending keywords from Apify")
    return result


def fetch_tiktok_trends() -> list[dict]:
    if config.APIFY_API_KEY:
        try:
            trends = _fetch_from_apify()
            if trends:
                return trends
        except Exception as e:
            logger.warning(f"tiktok: Apify failed ({e}), falling back to mock")

    logger.info("tiktok: using mock keyword seeds (set APIFY_API_KEY for real data)")
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
