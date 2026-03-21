"""Application configuration loaded from environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()

# --- LLM ---
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

# --- CoinGecko ---
COINGECKO_API_KEY: str = os.getenv("COINGECKO_API_KEY", "")
COINGECKO_BASE_URL: str = "https://api.coingecko.com/api/v3"
COINGECKO_PRO_URL: str = "https://pro-api.coingecko.com/api/v3"

# --- On-chain data ---
ETHERSCAN_API_KEY: str = os.getenv("ETHERSCAN_API_KEY", "")
SOLSCAN_API_KEY: str = os.getenv("SOLSCAN_API_KEY", "")

# --- Apify (TikTok viral validation) ---
APIFY_API_KEY: str = os.getenv("APIFY_API_KEY", "")

# --- Discord webhook ---
DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL", "")

# --- Pipeline thresholds ---
MIN_TREND_MOMENTUM: float = 0.4
MIN_OPPORTUNITY_SCORE: float = 0.4
TOP_N_OPPORTUNITIES: int = 10

# --- Token discovery filters ---
MAX_TOKEN_MARKET_CAP: float = 5_000_000   # $5M — skip established coins
MAX_TOKEN_AGE_DAYS: int = 90              # Skip pairs older than 90 days
