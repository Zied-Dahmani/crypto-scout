"""Recommendation data models."""

from datetime import datetime
from pydantic import BaseModel, Field

from .match import MatchResult


class Recommendation(BaseModel):
    """Investment recommendation combining trend and crypto analysis."""
    id: str = Field(..., description="Unique recommendation ID")
    match: MatchResult = Field(..., description="The trend-crypto match")
    confidence_score: float = Field(..., ge=0, le=1, description="Overall confidence in recommendation")
    risk_level: str = Field(..., description="Risk level: low, medium, high, extreme")
    potential_upside: str = Field(default="unknown", description="Estimated potential upside")
    reasoning: str = Field(..., description="Detailed reasoning for the recommendation")
    action: str = Field(..., description="Suggested action: watch, consider, buy")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_notification_message(self) -> str:
        """Format recommendation as a notification message."""
        trend = self.match.trend
        crypto = self.match.crypto

        message = f"""
🚀 *CRYPTO SCOUT ALERT*

📈 *Trending Topic:* {trend.keyword}
🔥 *Virality Score:* {trend.virality_score:.2%}
📊 *Source:* {trend.source.value.title()}

💰 *Matched Crypto:* {crypto.name} ({crypto.symbol.upper()})
💵 *Price:* ${crypto.current_price_usd:.6f}
📊 *Market Cap:* ${crypto.market_cap_usd:,.0f}
📈 *24h Change:* {crypto.price_change_24h_pct:+.2f}%

🎯 *Match Score:* {self.match.match_score:.2%}
🔮 *Confidence:* {self.confidence_score:.2%}
⚠️ *Risk Level:* {self.risk_level.upper()}
💡 *Action:* {self.action.upper()}

📝 *Reasoning:*
{self.reasoning[:300]}{'...' if len(self.reasoning) > 300 else ''}

⏰ Generated: {self.created_at.strftime('%Y-%m-%d %H:%M UTC')}
        """.strip()

        return message

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
