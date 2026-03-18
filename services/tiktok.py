"""Trend keyword source — mock data.

Returns a fixed list of viral keywords used as pipeline seeds.
Each keyword is validated against real Google Trends data in the next node,
so dead trends are automatically filtered out.

To upgrade to real TikTok data in the future, see README — TikTok Session.
"""

from utils.logger import get_logger

logger = get_logger(__name__)


def fetch_tiktok_trends() -> list[dict]:
    logger.info("trends: using mock keyword seeds (validated by Google Trends)")
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
