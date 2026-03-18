"""Etherscan API client — real on-chain wallet analysis for ERC-20 tokens.

Free tier: 5 calls/sec, 100k calls/day.
Set ETHERSCAN_API_KEY in .env (free at etherscan.io).

Strategy:
  1. Fetch the first 100 token transfers for a contract (early buyers).
  2. For each unique buyer address, fetch their transfer history.
  3. Compute win_rate and PnL from net token balance * current price.

Limitations:
  - Only works for Ethereum ERC-20 tokens.
  - PnL is approximate (net holdings × current price, not actual cost basis).
  - Solana / BSC tokens need Solscan / BscScan respectively.
"""

import time

import certifi
import requests

import config
from utils.logger import get_logger

logger = get_logger(__name__)

_BASE = "https://api.etherscan.io/api"
_RATE_DELAY = 0.25  # 4 calls/sec (safely under the 5/sec free limit)

# Well-known contracts to exclude (DEX routers, bridges, burn addresses)
_EXCLUDED = {
    "0x0000000000000000000000000000000000000000",  # burn
    "0x000000000000000000000000000000000000dead",  # burn
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",  # Uniswap v2 router
    "0xe592427a0aece92de3edee1f18e0157c05861564",  # Uniswap v3 router
    "0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f",  # Sushiswap router
}


def _get(params: dict) -> dict | None:
    params["apikey"] = config.ETHERSCAN_API_KEY
    time.sleep(_RATE_DELAY)
    try:
        r = requests.get(_BASE, params=params, timeout=12, verify=certifi.where())
        data = r.json()
        if data.get("status") == "1":
            return data
        msg = data.get("message", "")
        if "No transactions found" not in msg:
            logger.debug(f"etherscan: {msg}")
    except Exception as e:
        logger.error("etherscan request failed", error=str(e))
    return None


def get_early_buyers(contract_address: str, limit: int = 15) -> list[str]:
    """Return addresses of the first N unique buyers of a token.

    Queries the first 100 token transfers sorted ascending by block.
    Excludes known DEX routers and zero-addresses.
    """
    data = _get(
        {
            "module": "account",
            "action": "tokentx",
            "contractaddress": contract_address,
            "sort": "asc",
            "page": 1,
            "offset": 100,
        }
    )
    if not data:
        return []

    seen: set[str] = set()
    buyers: list[str] = []
    for tx in data.get("result", []):
        addr = tx.get("to", "").lower()
        if addr and addr not in _EXCLUDED and addr not in seen:
            seen.add(addr)
            buyers.append(addr)
            if len(buyers) >= limit:
                break

    return buyers


def get_wallet_transfers(contract_address: str, address: str) -> list[dict]:
    """Return all token transfers for a specific wallet + contract."""
    data = _get(
        {
            "module": "account",
            "action": "tokentx",
            "contractaddress": contract_address,
            "address": address,
            "sort": "asc",
            "page": 1,
            "offset": 100,
        }
    )
    return data.get("result", []) if data else []


def analyze_wallet(
    contract_address: str, address: str, current_price: float
) -> dict | None:
    """Compute win_rate and PnL for a wallet relative to a token.

    win_rate: fraction of interactions that are sells (took profit).
    pnl_usd:  net token balance × current price (approximate).
    """
    txs = get_wallet_transfers(contract_address, address)
    if not txs:
        return None

    try:
        decimals = int(txs[0].get("tokenDecimal", 18))
        scale = 10**decimals
        addr_lower = address.lower()

        received = sum(int(t["value"]) for t in txs if t["to"].lower() == addr_lower)
        sent = sum(int(t["value"]) for t in txs if t["from"].lower() == addr_lower)

        net_tokens = (received - sent) / scale
        pnl = round(net_tokens * current_price, 2)

        n_sells = sum(1 for t in txs if t["from"].lower() == addr_lower)
        win_rate = round(n_sells / len(txs), 3) if txs else 0.0

        is_smart = (
            net_tokens > 0          # still holding
            and win_rate >= 0.3     # has taken some profit
            and len(txs) >= 3       # experienced (not a one-off)
            and pnl >= 500          # meaningful position
        )

        return {
            "address": address,
            "win_rate": win_rate,
            "pnl_usd": pnl,
            "is_smart_money": is_smart,
        }
    except Exception as e:
        logger.warning(f"etherscan: failed to analyze {address}: {e}")
        return None
