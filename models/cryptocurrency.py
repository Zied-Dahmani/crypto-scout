"""Cryptocurrency data models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Cryptocurrency(BaseModel):
    """Represents a cryptocurrency with relevant market data."""
    id: str = Field(..., description="Unique identifier (e.g., coingecko ID)")
    symbol: str = Field(..., description="Token symbol (e.g., BTC, ETH)")
    name: str = Field(..., description="Full name of the cryptocurrency")
    current_price_usd: float = Field(..., ge=0, description="Current price in USD")
    market_cap_usd: float = Field(..., ge=0, description="Market capitalization in USD")
    volume_24h_usd: float = Field(default=0, ge=0, description="24h trading volume in USD")
    price_change_24h_pct: float = Field(default=0, description="24h price change percentage")
    price_change_7d_pct: float = Field(default=0, description="7d price change percentage")
    description: str = Field(default="", description="Project description")
    categories: list[str] = Field(default_factory=list, description="Project categories/tags")
    website: Optional[str] = Field(default=None, description="Project website")
    twitter_handle: Optional[str] = Field(default=None, description="Twitter handle")
    telegram_url: Optional[str] = Field(default=None, description="Telegram group URL")
    contract_address: Optional[str] = Field(default=None, description="Token contract address")
    blockchain: Optional[str] = Field(default=None, description="Blockchain network")
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
