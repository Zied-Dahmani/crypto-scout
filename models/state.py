"""Agent state data models."""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field

from .trend import Trend
from .cryptocurrency import Cryptocurrency
from .match import MatchResult
from .recommendation import Recommendation


class AgentState(BaseModel):
    """State shared between agents in the LangGraph workflow."""
    trends: list[Trend] = Field(default_factory=list, description="Detected trends")
    cryptocurrencies: list[Cryptocurrency] = Field(default_factory=list, description="Filtered cryptocurrencies")
    matches: list[MatchResult] = Field(default_factory=list, description="Trend-crypto matches")
    recommendations: list[Recommendation] = Field(default_factory=list, description="Final recommendations")
    errors: list[str] = Field(default_factory=list, description="Any errors encountered")
    messages: list[Any] = Field(default_factory=list, description="LangGraph messages")
    last_scan_time: Optional[datetime] = Field(default=None, description="Last scan timestamp")
    iteration_count: int = Field(default=0, description="Number of iterations completed")
