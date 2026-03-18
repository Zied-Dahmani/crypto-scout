"""Solscan API client — on-chain wallet analysis for Solana SPL tokens.

Free tier: works without API key (public endpoints).
Pro key increases rate limits: pro.solscan.io → API Key (free tier available).
Set SOLSCAN_API_KEY in .env for higher limits.

Strategy (mirrors Etherscan approach):
  1. Get early SPL token transfers (first buyers).
  2. For each buyer address, fetch their transfer history with this token.
  3. Compute win_rate and approximate PnL.
"""

import time

import certifi
import requests

import config
from utils.logger import get_logger

logger = get_logger(__name__)

_PUBLIC_BASE = "https://api.solscan.io/v2"
_PRO_BASE = "https://pro-api.solscan.io/v2.0"
_MIN_INTERVAL = 0.5  # 2 req/sec on free tier
_last_request: float = 0.0

# Known Solana program addresses to exclude (DEX routers, system programs)
_EXCLUDED = {
    "11111111111111111111111111111111",           # System Program
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",  # Token Program
    "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJe8bv",  # Associated Token Program
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4",  # Jupiter Aggregator
    "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin",  # Serum DEX
}


def _base() -> str:
    return _PRO_BASE if config.SOLSCAN_API_KEY else _PUBLIC_BASE


def _headers() -> dict:
    if config.SOLSCAN_API_KEY:
        return {"token": config.SOLSCAN_API_KEY}
    return {}


def _get(path: str, params: dict | None = None) -> dict | None:
    global _last_request
    elapsed = time.time() - _last_request
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_request = time.time()

    url = f"{_base()}{path}"
    try:
        r = requests.get(
            url,
            params=params or {},
            headers=_headers(),
            timeout=12,
            verify=certifi.where(),
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("success", True):
                return data
        logger.debug(f"solscan: HTTP {r.status_code} for {path}")
    except requests.RequestException as e:
        logger.error("solscan request failed", error=str(e))
    return None


def get_early_buyers(token_mint: str, limit: int = 15) -> list[str]:
    """Return addresses of the first N unique buyers of a Solana token.

    Fetches the earliest SPL token transfers sorted ascending by block time.
    Excludes known DEX programs and system addresses.
    """
    data = _get(
        "/token/transfer",
        {
            "address": token_mint,
            "page": 1,
            "page_size": 100,
            "sort_by": "block_time",
            "sort_order": "asc",
        },
    )
    if not data:
        return []

    transfers = data.get("data", {})
    if isinstance(transfers, dict):
        transfers = transfers.get("items", [])

    seen: set[str] = set()
    buyers: list[str] = []

    for tx in transfers:
        # Receiver of the token transfer
        addr = tx.get("to_address", "") or tx.get("dst_owner", "")
        if addr and addr not in _EXCLUDED and addr not in seen:
            seen.add(addr)
            buyers.append(addr)
            if len(buyers) >= limit:
                break

    return buyers


def get_wallet_transfers(token_mint: str, address: str) -> list[dict]:
    """Return SPL token transfer history for a specific wallet + token."""
    data = _get(
        "/account/token/txs",
        {
            "address": address,
            "token_address": token_mint,
            "page": 1,
            "page_size": 100,
        },
    )
    if not data:
        return []

    result = data.get("data", {})
    if isinstance(result, dict):
        return result.get("items", [])
    return result or []


def analyze_wallet(token_mint: str, address: str, current_price: float) -> dict | None:
    """Compute win_rate and approximate PnL for a Solana wallet + token.

    win_rate: fraction of interactions that are outgoing (took profit / sold).
    pnl_usd:  net token balance × current price (approximate current value).
    """
    txs = get_wallet_transfers(token_mint, address)
    if not txs:
        return None

    try:
        received = sum(
            float(t.get("amount", 0))
            for t in txs
            if t.get("to_address") == address or t.get("dst_owner") == address
        )
        sent = sum(
            float(t.get("amount", 0))
            for t in txs
            if t.get("from_address") == address or t.get("src_owner") == address
        )

        net_tokens = received - sent
        pnl = round(net_tokens * current_price, 2)

        n_sells = sum(
            1 for t in txs
            if t.get("from_address") == address or t.get("src_owner") == address
        )
        win_rate = round(n_sells / len(txs), 3) if txs else 0.0

        is_smart = (
            net_tokens > 0
            and win_rate >= 0.3
            and len(txs) >= 3
            and pnl >= 500
        )

        return {
            "address": address,
            "win_rate": win_rate,
            "pnl_usd": pnl,
            "is_smart_money": is_smart,
        }
    except Exception as e:
        logger.warning(f"solscan: failed to analyze {address}: {e}")
        return None
