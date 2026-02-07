"""Match result data models."""

from pydantic import BaseModel, Field

from .trend import Trend
from .cryptocurrency import Cryptocurrency


class MatchResult(BaseModel):
    """Result of matching a trend with a cryptocurrency."""
    trend: Trend = Field(..., description="The matched trend")
    crypto: Cryptocurrency = Field(..., description="The matched cryptocurrency")
    match_score: float = Field(..., ge=0, le=1, description="How well the trend matches the crypto")
    match_reasons: list[str] = Field(default_factory=list, description="Reasons for the match")
    keyword_matches: list[str] = Field(default_factory=list, description="Matched keywords")
