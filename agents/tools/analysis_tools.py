"""
Analysis and recommendation tools for the AI agents.
"""

import json
from datetime import datetime, timezone

from langchain_core.tools import tool

from models.trend import Trend, TrendSource
from models.cryptocurrency import Cryptocurrency
from models.recommendation import Recommendation
from services.matching import MatchingService, RecommendationEngine
from utils.logger import get_logger

logger = get_logger(__name__)

# Initialize services
matching_service = MatchingService()
recommendation_engine = RecommendationEngine(matching_service)


@tool
def analyze_trend_match(
    trend_keyword: str,
    trend_virality: float,
    crypto_name: str,
    crypto_symbol: str,
    crypto_market_cap: float,
    crypto_volume_24h: float = 0,
    crypto_price_change: float = 0
) -> str:
    """
    Analyze how well a cryptocurrency matches a trending topic.
    Returns a detailed match analysis with score and reasoning.

    Args:
        trend_keyword: The trending topic/keyword
        trend_virality: Virality score from 0 to 1 (e.g., 0.75 = 75%)
        crypto_name: Full name of the cryptocurrency
        crypto_symbol: Trading symbol (e.g., PEPE, DOGE)
        crypto_market_cap: Current market cap in USD
        crypto_volume_24h: 24-hour trading volume in USD
        crypto_price_change: 24-hour price change percentage

    Returns:
        Match analysis with score, confidence, and investment assessment
    """
    logger.info(f"Analyzing match: {trend_keyword} <-> {crypto_name}")

    # Create models
    trend = Trend(
        id=f"tool_{trend_keyword}_{datetime.now(timezone.utc).timestamp()}",
        keyword=trend_keyword,
        related_keywords=[trend_keyword.lower()],
        source=TrendSource.CUSTOM,
        virality_score=min(max(trend_virality, 0), 1),
        growth_rate=100,
        volume=1000,
    )

    crypto = Cryptocurrency(
        id=crypto_symbol.lower(),
        symbol=crypto_symbol,
        name=crypto_name,
        current_price_usd=0.0001,
        market_cap_usd=crypto_market_cap,
        volume_24h_usd=crypto_volume_24h,
        price_change_24h_pct=crypto_price_change,
    )

    # Calculate match
    matches = matching_service.match_trends_to_cryptos([trend], [crypto], min_score=0.0)

    if not matches:
        return f"""## Match Analysis Failed

**Trend:** {trend_keyword}
**Crypto:** {crypto_name} ({crypto_symbol})

⚠️ Could not establish a meaningful connection between this trend and cryptocurrency.
The keyword matching and semantic analysis found no significant overlap.

**Recommendation:** SKIP - Look for other opportunities."""

    match = matches[0]

    # Determine match quality
    if match.match_score >= 0.7:
        quality = "🟢 STRONG"
    elif match.match_score >= 0.4:
        quality = "🟡 MODERATE"
    else:
        quality = "🔴 WEAK"

    result = f"""## Match Analysis: {trend_keyword} ↔ {crypto_name}

### Match Quality: {quality}
• **Match Score:** {match.match_score:.0%}
• **Trend Virality:** {trend_virality:.0%}

### Match Factors
"""
    for reason in match.match_reasons:
        result += f"• {reason}\n"

    if match.keyword_matches:
        result += f"\n**Keyword Matches:** {', '.join(match.keyword_matches)}\n"

    # Market assessment
    result += f"""
### Market Metrics
• **Market Cap:** ${crypto_market_cap:,.0f}
• **24h Volume:** ${crypto_volume_24h:,.0f}
• **24h Change:** {crypto_price_change:+.2f}%

### Quick Assessment
"""
    if crypto_market_cap < 100000:
        result += "⚠️ Micro-cap (<$100k) - Extremely high risk, potential for large moves\n"
    elif crypto_market_cap < 500000:
        result += "⚠️ Ultra low-cap (<$500k) - Very high risk, significant volatility expected\n"
    else:
        result += "⚠️ Low-cap (<$1M) - High risk but reasonable liquidity\n"

    return result


@tool
def calculate_investment_score(
    match_score: float,
    trend_virality: float,
    market_cap: float,
    volume_24h: float,
    price_change_24h: float
) -> str:
    """
    Calculate an overall investment opportunity score.
    Combines trend strength, match quality, and market metrics.

    Args:
        match_score: Match score from 0 to 1
        trend_virality: Trend virality from 0 to 1
        market_cap: Market cap in USD
        volume_24h: 24h trading volume in USD
        price_change_24h: 24h price change percentage

    Returns:
        Investment score with breakdown and risk assessment
    """
    # Normalize inputs
    match_score = min(max(match_score, 0), 1)
    trend_virality = min(max(trend_virality, 0), 1)

    # Calculate component scores

    # Trend score (30% weight)
    trend_score = trend_virality * 0.3

    # Match score (25% weight)
    match_component = match_score * 0.25

    # Volume score (20% weight) - higher volume is better for liquidity
    if volume_24h > 100000:
        volume_score = 1.0
    elif volume_24h > 50000:
        volume_score = 0.8
    elif volume_24h > 10000:
        volume_score = 0.5
    else:
        volume_score = 0.2
    volume_component = volume_score * 0.2

    # Momentum score (15% weight)
    if price_change_24h > 50:
        momentum_score = 1.0
    elif price_change_24h > 20:
        momentum_score = 0.8
    elif price_change_24h > 0:
        momentum_score = 0.5
    elif price_change_24h > -10:
        momentum_score = 0.3
    else:
        momentum_score = 0.1
    momentum_component = momentum_score * 0.15

    # Market cap score (10% weight) - lower cap = more upside potential
    if market_cap < 100000:
        cap_score = 1.0
    elif market_cap < 500000:
        cap_score = 0.8
    elif market_cap < 1000000:
        cap_score = 0.6
    else:
        cap_score = 0.3
    cap_component = cap_score * 0.1

    # Total score
    total_score = trend_score + match_component + volume_component + momentum_component + cap_component

    # Determine rating
    if total_score >= 0.75:
        rating = "⭐⭐⭐⭐⭐ EXCELLENT"
        action = "STRONG BUY SIGNAL"
    elif total_score >= 0.6:
        rating = "⭐⭐⭐⭐ GOOD"
        action = "CONSIDER BUYING"
    elif total_score >= 0.45:
        rating = "⭐⭐⭐ MODERATE"
        action = "ADD TO WATCHLIST"
    elif total_score >= 0.3:
        rating = "⭐⭐ WEAK"
        action = "MONITOR ONLY"
    else:
        rating = "⭐ POOR"
        action = "SKIP"

    return f"""## Investment Score Analysis

### Overall Score: {total_score:.0%}
### Rating: {rating}
### Suggested Action: {action}

---

### Score Breakdown

| Component | Score | Weight | Contribution |
|-----------|-------|--------|--------------|
| Trend Virality | {trend_virality:.0%} | 30% | {trend_score:.2f} |
| Match Quality | {match_score:.0%} | 25% | {match_component:.2f} |
| Volume/Liquidity | {volume_score:.0%} | 20% | {volume_component:.2f} |
| Price Momentum | {momentum_score:.0%} | 15% | {momentum_component:.2f} |
| Upside Potential | {cap_score:.0%} | 10% | {cap_component:.2f} |
| **TOTAL** | | **100%** | **{total_score:.2f}** |

---

### Risk Warning
⚠️ Low-cap cryptocurrencies are extremely volatile and speculative.
Never invest more than you can afford to lose completely.
This is not financial advice - always DYOR (Do Your Own Research)."""


@tool
def generate_recommendation(
    trend_keyword: str,
    crypto_name: str,
    crypto_symbol: str,
    investment_score: float,
    market_cap: float,
    key_reasons: str
) -> str:
    """
    Generate a final structured recommendation for a crypto opportunity.
    Use this after analyzing a trend-crypto match.

    Args:
        trend_keyword: The trending topic
        crypto_name: Cryptocurrency name
        crypto_symbol: Cryptocurrency symbol
        investment_score: Overall score from 0 to 1
        market_cap: Market cap in USD
        key_reasons: Comma-separated list of key reasons for the match

    Returns:
        Structured recommendation in JSON format for notifications
    """
    # Determine action and risk
    if investment_score >= 0.7:
        action = "BUY"
        confidence = "HIGH"
    elif investment_score >= 0.5:
        action = "CONSIDER"
        confidence = "MEDIUM"
    elif investment_score >= 0.3:
        action = "WATCH"
        confidence = "LOW"
    else:
        action = "SKIP"
        confidence = "VERY LOW"

    if market_cap < 100000:
        risk = "EXTREME"
        potential = "100x+"
    elif market_cap < 500000:
        risk = "VERY HIGH"
        potential = "20x-50x"
    elif market_cap < 1000000:
        risk = "HIGH"
        potential = "5x-20x"
    else:
        risk = "MEDIUM"
        potential = "2x-5x"

    recommendation = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trend": trend_keyword,
        "crypto": {
            "name": crypto_name,
            "symbol": crypto_symbol.upper(),
            "market_cap_usd": market_cap,
        },
        "analysis": {
            "investment_score": round(investment_score, 2),
            "confidence": confidence,
            "risk_level": risk,
            "potential_upside": potential,
            "action": action,
        },
        "reasons": [r.strip() for r in key_reasons.split(",")],
        "disclaimer": "This is not financial advice. Always DYOR.",
    }

    # Format for display
    result = f"""## 📋 RECOMMENDATION GENERATED

```json
{json.dumps(recommendation, indent=2)}
```

---

### Summary

🎯 **{action}** - {crypto_name} (${crypto_symbol.upper()})

| Metric | Value |
|--------|-------|
| Trend | {trend_keyword} |
| Score | {investment_score:.0%} |
| Confidence | {confidence} |
| Risk | {risk} |
| Potential | {potential} |

### Key Reasons
"""
    for reason in recommendation["reasons"]:
        result += f"• {reason}\n"

    result += "\n⚠️ *Always verify independently before making any investment decisions.*"

    return result


# Export all analysis tools
ANALYSIS_TOOLS = [
    analyze_trend_match,
    calculate_investment_score,
    generate_recommendation,
]
