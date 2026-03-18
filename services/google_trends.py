"""Google Trends validation — real pytrends implementation.

No API key required. Rate-limited by Google (~1 req/sec).
Results are cached in-process to avoid duplicate calls within a run.
"""

import time

from utils.logger import get_logger

logger = get_logger(__name__)

_cache: dict[str, dict] = {}


def _build_pytrends():
    from pytrends.request import TrendReq
    return TrendReq(hl="en-US", tz=360, timeout=(10, 25), retries=2, backoff_factor=0.5)


def get_trend_score(keyword: str) -> dict:
    """Return Google Trends interest score for a keyword over the last 7 days.

    Returns:
        dict with keys:
          - score (int): 0-100 interest level (100 = peak popularity)
          - is_increasing (bool): True if second half of week > first half
    """
    if keyword in _cache:
        return _cache[keyword]

    try:
        pt = _build_pytrends()
        pt.build_payload([keyword], timeframe="now 7-d", geo="")
        iot = pt.interest_over_time()
        time.sleep(1.2)  # respect Google's rate limit

        if iot.empty or keyword not in iot.columns:
            result = {"score": 0, "is_increasing": False}
        else:
            scores = iot[keyword].dropna().tolist()
            if not scores:
                result = {"score": 0, "is_increasing": False}
            else:
                score = int(scores[-1])
                mid = len(scores) // 2
                avg_first = sum(scores[:mid]) / max(mid, 1)
                is_increasing = bool(scores[-1] > avg_first)
                result = {"score": score, "is_increasing": is_increasing}

        logger.info(f"google_trends: {keyword} → score={result['score']}, increasing={result['is_increasing']}")

    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "too many" in err_str.lower() or "ResponseError" in err_str:
            # Rate-limited — treat as unknown, not zero (so Twitter + growth can still pass)
            logger.warning(f"google_trends: rate-limited for '{keyword}', using neutral score")
            result = {"score": 50, "is_increasing": True}
        else:
            logger.warning(f"google_trends: failed for '{keyword}' ({e}), score=0")
            result = {"score": 0, "is_increasing": False}

    _cache[keyword] = result
    return result
