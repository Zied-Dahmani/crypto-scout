"""Application configuration loaded from environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()

# --- LLM API keys (first available is used) ---
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# --- CoinGecko ---
COINGECKO_API_KEY: str = os.getenv("COINGECKO_API_KEY", "")
COINGECKO_BASE_URL: str = "https://api.coingecko.com/api/v3"
COINGECKO_PRO_URL: str = "https://pro-api.coingecko.com/api/v3"

# --- Twitter / X (scraper account — free, no paid API needed) ---
TWITTER_BEARER_TOKEN: str = os.getenv("TWITTER_BEARER_TOKEN", "")
TWITTER_SCRAPER_USERNAME: str = os.getenv("TWITTER_SCRAPER_USERNAME", "")
TWITTER_SCRAPER_PASSWORD: str = os.getenv("TWITTER_SCRAPER_PASSWORD", "")
TWITTER_SCRAPER_EMAIL: str = os.getenv("TWITTER_SCRAPER_EMAIL", "")

# --- Etherscan (Ethereum on-chain data) ---
ETHERSCAN_API_KEY: str = os.getenv("ETHERSCAN_API_KEY", "")

# --- Solscan (Solana on-chain data) ---
SOLSCAN_API_KEY: str = os.getenv("SOLSCAN_API_KEY", "")

# --- TikTok scraper ---
TIKTOK_MS_TOKEN: str = os.getenv("TIKTOK_MS_TOKEN", "")
TIKTOK_USERNAME: str = os.getenv("TIKTOK_USERNAME", "")
TIKTOK_PASSWORD: str = os.getenv("TIKTOK_PASSWORD", "")

# --- Discord webhook ---
DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL", "")

# --- Pipeline thresholds ---
MIN_TREND_MOMENTUM: float = 0.4    # Drop trends scoring below this
MIN_OPPORTUNITY_SCORE: float = 0.4  # Drop opportunities scoring below this
TOP_N_OPPORTUNITIES: int = 10       # Return at most this many results

# --- Token discovery filters (early-stage focus) ---
MAX_TOKEN_MARKET_CAP: float = 5_000_000   # $5M — skip established coins
MAX_TOKEN_AGE_DAYS: int = 90              # Skip pairs older than 90 days
