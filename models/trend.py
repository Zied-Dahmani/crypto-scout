"""Trend data models."""

from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class TrendSource(str, Enum):
    """Source of the trending topic."""
    TWITTER = "twitter"
    DISCORD = "discord"
    CUSTOM = "custom"


class Trend(BaseModel):
    """Represents a viral trend detected from social media."""
    id: str = Field(..., description="Unique identifier for the trend")
    keyword: str = Field(..., description="Main keyword/topic of the trend")
    related_keywords: list[str] = Field(default_factory=list, description="Related keywords and hashtags")
    source: TrendSource = Field(..., description="Where the trend was detected")
    virality_score: float = Field(..., ge=0, le=1, description="Score indicating how viral the trend is (0-1)")
    growth_rate: float = Field(..., ge=0, description="Rate of growth in mentions/engagement")
    volume: int = Field(..., ge=0, description="Total mentions/posts/engagement count")
    sentiment_score: float = Field(default=0.5, ge=0, le=1, description="Sentiment score (0=negative, 1=positive)")
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    raw_data: dict[str, Any] = Field(default_factory=dict, description="Raw data from source")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
