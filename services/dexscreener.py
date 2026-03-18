"""DEXScreener API client — free, no API key required.

Catches tokens BEFORE they appear on CoinGecko.
Provides real DEX liquidity pool data (more accurate than volume/mcap ratio).

Docs: https://docs.dexscreener.com/api/reference
"""

import time
from datetime import datetime, timezone

import certifi
import requests

import config
from utils.logger import get_logger

logger = get_logger(__name__)

_BASE = "https://api.dexscreener.com/latest/dex"
_MIN_INTERVAL = 0.4   # ~2.5 req/sec (conservative)
_MIN_LIQUIDITY = 5_000  # USD — ignore ghost pairs with no real liquidity
_last_request: float = 0.0


def _get(path: str) -> dict | None:
    global _last_request
    elapsed = time.time() - _last_request
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_request = time.time()

    try:
        r = requests.get(f"{_BASE}/{path}", timeout=12, verify=certifi.where())
        if r.status_code == 200:
            return r.json()
        logger.warning(f"dexscreener: HTTP {r.status_code} for {path}")
    except requests.RequestException as e:
        logger.error("dexscreener request failed", error=str(e))
    return None


def search_pairs(keyword: str, limit: int = 5) -> list[dict]:
    """Search DEXScreener for trading pairs matching a keyword.

    Returns normalized pair dicts ready for token_finder and market_analyzer.
    Filters out pairs with liquidity < $5k (ghost/dead pairs).
    Sorted by 24h volume descending.
    """
    data = _get(f"search?q={keyword}")
    if not data:
        return []

    pairs = data.get("pairs") or []
    results = []

    now_ms = datetime.now(timezone.utc).timestamp() * 1000
    max_age_ms = config.MAX_TOKEN_AGE_DAYS * 86_400_000

    for pair in pairs:
        liq = (pair.get("liquidity") or {}).get("usd") or 0
        if liq < _MIN_LIQUIDITY:
            continue

        base = pair.get("baseToken", {})
        symbol = base.get("symbol", "").upper()
        name = base.get("name", "")
        contract = base.get("address", "")
        chain = pair.get("chainId", "")
        pair_address = pair.get("pairAddress", "")
        price = float(pair.get("priceUsd") or 0)
        volume_24h = float((pair.get("volume") or {}).get("h24") or 0)
        market_cap = float(pair.get("marketCap") or pair.get("fdv") or 0)
        price_change_24h = float((pair.get("priceChange") or {}).get("h24") or 0)
        liquidity_usd = float(liq)
        pair_created_at = pair.get("pairCreatedAt") or 0  # ms epoch

        if not symbol or not contract:
            continue

        # Skip established large-cap coins — we want early-stage only
        if market_cap > config.MAX_TOKEN_MARKET_CAP:
            logger.debug(f"dexscreener: skipping {symbol} (mcap=${market_cap:,.0f} > limit)")
            continue

        # Skip pairs older than MAX_TOKEN_AGE_DAYS
        if pair_created_at and (now_ms - pair_created_at) > max_age_ms:
            logger.debug(f"dexscreener: skipping {symbol} (pair too old)")
            continue

        results.append(
            {
                "symbol": symbol,
                "name": name,
                "contract_address": contract,
                "chain_id": chain,
                "pair_address": pair_address,
                "price_usd": price,
                "volume_24h": volume_24h,
                "market_cap": market_cap,
                "price_change_24h": price_change_24h,
                "liquidity_usd": liquidity_usd,
                "pair_created_at": pair_created_at,
            }
        )

    # Sort by newest first — prioritize recently launched tokens
    results.sort(key=lambda x: x["pair_created_at"], reverse=True)
    return results[:limit]


def get_pair(pair_address: str, chain_id: str) -> dict | None:
    """Fetch live data for a specific DEX pair by address."""
    data = _get(f"pairs/{chain_id}/{pair_address}")
    if not data:
        return None
    pairs = data.get("pairs") or []
    return pairs[0] if pairs else None
