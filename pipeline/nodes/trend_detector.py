"""Node 1 — trend_detector: Fetch viral topics from Google Trends RSS."""

from pipeline.state import PipelineState
from services.trends_rss import fetch_tiktok_trends
from utils.logger import get_logger

logger = get_logger(__name__)


def trend_detector(state: PipelineState) -> dict:
    """Fetch raw trending topics from TikTok and populate raw_trends."""
    logger.info("trend_detector: fetching TikTok trends")
    try:
        trends = fetch_tiktok_trends()
        logger.info(f"trend_detector: found {len(trends)} trends")
        return {"raw_trends": trends}
    except Exception as e:
        logger.error("trend_detector failed", error=str(e))
        return {"raw_trends": [], "errors": state.get("errors", []) + [f"trend_detector: {e}"]}
