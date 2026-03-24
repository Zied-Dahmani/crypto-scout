"""Node 6 — scorer: Score and rank crypto opportunities.

Composite score = 0.40 * trend_momentum
               + 0.35 * market_quality
               + 0.25 * smart_money_score

Verdict thresholds:
  >= 0.72  → BUY
  >= 0.52  → WATCH
  <  0.52  → SKIP
"""

import config
from pipeline.state import Opportunity, PipelineState
from utils.logger import get_logger

logger = get_logger(__name__)


def _market_quality(token: dict) -> float:
    """Score market quality 0-1 from liquidity, volume activity, and price momentum.

    Volume is scored relative to market cap (turnover ratio) so micro-cap tokens
    aren't penalised for having lower absolute volume than large-caps.
    A 20%+ daily turnover ratio scores 1.0 — strong for an early-stage token.
    """
    liquidity = min(token["liquidity"], 1.0)
    mcap = token["market_cap"]
    if mcap > 0:
        # Relative volume: 20% daily turnover = full score
        volume_score = min(token["volume_24h"] / mcap / 0.20, 1.0)
    else:
        volume_score = min(token["volume_24h"] / 500_000, 1.0)
    momentum_score = min(max(token["price_change_24h"], 0) / 200, 1.0)
    return round(0.40 * liquidity + 0.35 * volume_score + 0.25 * momentum_score, 4)


def _smart_money_score(wallet: dict) -> float:
    """Score smart money presence 0-1 from count and avg win rate."""
    count_score = min(wallet["smart_money_count"] / 5, 1.0)  # 5+ wallets = max
    return round(0.60 * count_score + 0.40 * wallet["avg_win_rate"], 4)


def _verdict(score: float) -> str:
    if score >= 0.72:
        return "BUY"
    if score >= 0.52:
        return "WATCH"
    return "SKIP"


def scorer(state: PipelineState) -> dict:
    """Score each token opportunity and return a ranked list."""
    logger.info("scorer: scoring opportunities")

    validated_by_kw = {t["keyword"]: t for t in state.get("validated_trends", [])}
    wallet_by_sym = {w["symbol"]: w for w in state.get("wallet_analyses", [])}

    opportunities: list[Opportunity] = []

    for token in state.get("market_data", []):
        symbol = token["symbol"]
        keyword = token["trend_keyword"]
        trend = validated_by_kw.get(keyword)
        wallets = wallet_by_sym.get(symbol)

        if not trend or not wallets:
            logger.warning(f"scorer: missing data for {symbol}, skipping")
            continue

        trend_momentum = trend["momentum"]
        mq = _market_quality(token)
        sm = _smart_money_score(wallets)
        score = round(0.40 * trend_momentum + 0.35 * mq + 0.25 * sm, 4)

        opportunities.append(
            {
                "symbol": symbol,
                "name": token["name"],
                "trend_keyword": keyword,
                "score": score,
                "trend_momentum": trend_momentum,
                "market_quality": mq,
                "smart_money_score": sm,
                "verdict": _verdict(score),
                "market_cap": token["market_cap"],
                "volume_24h": token["volume_24h"],
                "price_change_24h": token["price_change_24h"],
                "current_price": token["current_price"],
                "contract_address": token.get("contract_address", ""),
                "blockchain": token.get("blockchain", ""),
                "pair_created_at": token.get("pair_created_at", 0),
            }
        )

    opportunities.sort(key=lambda x: x["score"], reverse=True)
    opportunities = [o for o in opportunities if o["score"] >= config.MIN_OPPORTUNITY_SCORE]
    opportunities = opportunities[: config.TOP_N_OPPORTUNITIES]

    for opp in opportunities:
        logger.info(
            f"scorer: [{opp['verdict']}] {opp['symbol']} score={opp['score']} "
            f"(trend={opp['trend_momentum']}, mkt={opp['market_quality']}, sm={opp['smart_money_score']})"
        )

    return {"opportunities": opportunities}
