"""
Configuration settings for Crypto Scout.
All API keys and secrets should be set via environment variables.
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class TwitterConfig:
    """Twitter/X API configuration."""
    api_key: str = field(default_factory=lambda: os.getenv("TWITTER_API_KEY", ""))
    api_secret: str = field(default_factory=lambda: os.getenv("TWITTER_API_SECRET", ""))
    access_token: str = field(default_factory=lambda: os.getenv("TWITTER_ACCESS_TOKEN", ""))
    access_token_secret: str = field(default_factory=lambda: os.getenv("TWITTER_ACCESS_TOKEN_SECRET", ""))
    bearer_token: str = field(default_factory=lambda: os.getenv("TWITTER_BEARER_TOKEN", ""))


@dataclass
class CoinGeckoConfig:
    """CoinGecko API configuration."""
    api_key: str = field(default_factory=lambda: os.getenv("COINGECKO_API_KEY", ""))
    base_url: str = "https://api.coingecko.com/api/v3"
    pro_base_url: str = "https://pro-api.coingecko.com/api/v3"
    # Market cap threshold in USD
    max_market_cap: float = 1_000_000  # $1 million


@dataclass
class WhatsAppConfig:
    """WhatsApp (Twilio) configuration."""
    account_sid: str = field(default_factory=lambda: os.getenv("TWILIO_ACCOUNT_SID", ""))
    auth_token: str = field(default_factory=lambda: os.getenv("TWILIO_AUTH_TOKEN", ""))
    from_number: str = field(default_factory=lambda: os.getenv("TWILIO_WHATSAPP_FROM", ""))
    to_number: str = field(default_factory=lambda: os.getenv("TWILIO_WHATSAPP_TO", ""))


@dataclass
class LLMConfig:
    """LLM configuration for agents."""
    provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "openai"))  # openai or anthropic
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    model_name: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4-turbo-preview"))


@dataclass
class AppConfig:
    """Main application configuration."""
    twitter: TwitterConfig = field(default_factory=TwitterConfig)
    coingecko: CoinGeckoConfig = field(default_factory=CoinGeckoConfig)
    whatsapp: WhatsAppConfig = field(default_factory=WhatsAppConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)

    # Trend detection settings
    trend_refresh_interval: int = 300  # 5 minutes
    min_virality_score: float = 0.5

    # Crypto scanning settings
    crypto_refresh_interval: int = 60  # 1 minute
    min_confidence_score: float = 0.6

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment variables."""
        return cls()


# Global config instance
config = AppConfig.from_env()
