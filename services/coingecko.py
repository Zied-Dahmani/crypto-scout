"""CoinGecko API client — synchronous, rate-limited."""

import time

import certifi
import requests

import config
from utils.logger import get_logger

logger = get_logger(__name__)

_BASE_URL = config.COINGECKO_PRO_URL if config.COINGECKO_API_KEY else config.COINGECKO_BASE_URL
_HEADERS = {"x-cg-pro-api-key": config.COINGECKO_API_KEY} if config.COINGECKO_API_KEY else {}
_MIN_INTERVAL = 1.5  # seconds between requests on free tier
_last_request: float = 0.0


def _get(endpoint: str, params: dict | None = None) -> dict | list | None:
    """Rate-limited GET to CoinGecko. Returns parsed JSON or None on error."""
    global _last_request
    elapsed = time.time() - _last_request
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_request = time.time()

    url = f"{_BASE_URL}/{endpoint}"
    try:
        resp = requests.get(
            url,
            params=params or {},
            headers=_HEADERS,
            timeout=15,
            verify=certifi.where(),
        )
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 429:
            logger.warning("CoinGecko rate limit — sleeping 60s")
            time.sleep(60)
        else:
            logger.error("CoinGecko error", status=resp.status_code, endpoint=endpoint)
    except requests.RequestException as e:
        logger.error("CoinGecko request failed", error=str(e))
    return None


def search_coins(keyword: str) -> list[dict]:
    """Search CoinGecko for coins matching a keyword. Returns up to 5 raw results."""
    data = _get("search", {"query": keyword})
    if not data:
        return []
    return data.get("coins", [])[:5]


def get_market_data(coin_ids: list[str]) -> list[dict]:
    """Fetch market data for a list of coin IDs. Returns raw CoinGecko market entries."""
    if not coin_ids:
        return []
    data = _get(
        "coins/markets",
        {
            "vs_currency": "usd",
            "ids": ",".join(coin_ids),
            "order": "market_cap_desc",
            "price_change_percentage": "24h",
        },
    )
    return data or []


def get_coin_details(coin_id: str) -> dict | None:
    """Fetch full coin details including contract addresses and blockchain platforms.

    Returns a dict with keys: id, symbol, name, platforms (dict of chain→address).
    Used by market_analyzer to extract the contract address for on-chain queries.
    """
    data = _get(
        f"coins/{coin_id}",
        {
            "localization": "false",
            "tickers": "false",
            "market_data": "false",
            "community_data": "false",
            "developer_data": "false",
        },
    )
    if not data:
        return None
    return {
        "id": data.get("id", ""),
        "symbol": data.get("symbol", ""),
        "name": data.get("name", ""),
        "platforms": data.get("platforms", {}),  # {"ethereum": "0x...", "solana": "..."}
    }


def get_mock_coins() -> list[dict]:
    """Return mock market data for development / offline testing."""
    return [
        {"id": "moo-deng",          "symbol": "moodeng",   "name": "Moo Deng",          "market_cap": 750_000,  "total_volume": 280_000, "current_price": 0.00045,    "price_change_percentage_24h": 156.5},
        {"id": "hawk-tuah",         "symbol": "hawktuah",  "name": "Hawk Tuah",          "market_cap": 320_000,  "total_volume": 145_000, "current_price": 0.000082,   "price_change_percentage_24h": 234.2},
        {"id": "chill-guy",         "symbol": "chillguy",  "name": "Chill Guy",          "market_cap": 580_000,  "total_volume": 195_000, "current_price": 0.00028,    "price_change_percentage_24h": 89.3},
        {"id": "skibidi-token",     "symbol": "skibidi",   "name": "Skibidi Toilet",     "market_cap": 180_000,  "total_volume": 72_000,  "current_price": 0.000015,   "price_change_percentage_24h": 67.8},
        {"id": "capybara-token",    "symbol": "capy",      "name": "Capybara",           "market_cap": 290_000,  "total_volume": 88_000,  "current_price": 0.00012,    "price_change_percentage_24h": 42.1},
        {"id": "pudgy-penguins-token", "symbol": "pengu",  "name": "Pudgy Penguins",     "market_cap": 850_000,  "total_volume": 125_000, "current_price": 0.000025,   "price_change_percentage_24h": 45.5},
        {"id": "mini-pepe",         "symbol": "minipepe",  "name": "Mini Pepe",          "market_cap": 180_000,  "total_volume": 45_000,  "current_price": 0.0000008,  "price_change_percentage_24h": 112.5},
        {"id": "trump-maga",        "symbol": "trumpmaga", "name": "Trump MAGA",         "market_cap": 920_000,  "total_volume": 310_000, "current_price": 0.00035,    "price_change_percentage_24h": 55.2},
        {"id": "griddy-coin",       "symbol": "griddy",    "name": "Griddy",             "market_cap": 95_000,   "total_volume": 35_000,  "current_price": 0.000008,   "price_change_percentage_24h": 128.5},
        {"id": "dogwifhat-mini",    "symbol": "wifmini",   "name": "Dog Wif Mini Hat",   "market_cap": 410_000,  "total_volume": 98_000,  "current_price": 0.00019,    "price_change_percentage_24h": 78.4},
    ]
