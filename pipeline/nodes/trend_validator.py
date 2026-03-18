"""Node 2 — trend_validator: Cross-check trends using Google Trends + Twitter.

Keeps only trends with increasing momentum above the configured threshold.
"""

import config
from pipeline.state import PipelineState, ValidatedTrend
from services.google_trends import get_trend_score
from services.twitter import get_twitter_mentions
from utils.logger import get_logger

logger = get_logger(__name__)

_MAX_TWITTER_MENTIONS = 100_000  # normalization ceiling
_MAX_GROWTH_RATE = 500.0         # normalization ceiling


def _compute_momentum(google_score: int, twitter_mentions: int, growth_rate: float) -> float:
    google_norm = google_score / 100.0
    twitter_norm = min(twitter_mentions / _MAX_TWITTER_MENTIONS, 1.0)
    growth_norm = min(growth_rate / _MAX_GROWTH_RATE, 1.0)
    return round(0.40 * google_norm + 0.35 * twitter_norm + 0.25 * growth_norm, 4)


def trend_validator(state: PipelineState) -> dict:
    """Validate raw trends; keep only those with sufficient increasing momentum."""
    logger.info("trend_validator: validating trends")
    validated: list[ValidatedTrend] = []

    for trend in state.get("raw_trends", []):
        keyword = trend["keyword"]
        google = get_trend_score(keyword)
        mentions = get_twitter_mentions(keyword)
        momentum = _compute_momentum(google["score"], mentions, trend["growth_rate"])
        is_increasing = google["is_increasing"] and mentions > 1_000

        if momentum >= config.MIN_TREND_MOMENTUM and is_increasing:
            validated.append(
                {
                    "keyword": keyword,
                    "hashtags": trend["hashtags"],
                    "google_score": google["score"],
                    "twitter_mentions": mentions,
                    "momentum": momentum,
                    "is_increasing": is_increasing,
                }
            )
            logger.info(f"trend_validator: ✓ {keyword} (momentum={momentum})")
        else:
            logger.info(
                f"trend_validator: ✗ {keyword} "
                f"(momentum={momentum}, increasing={is_increasing})"
            )

    passed = len(validated)
    total = len(state.get("raw_trends", []))
    logger.info(f"trend_validator: {passed}/{total} trends passed validation")
    return {"validated_trends": validated}
