"""Node 5 — wallet_analyzer: Detect early smart-money wallets for each token.

Routing:
  blockchain == "ethereum"  →  Etherscan  (needs ETHERSCAN_API_KEY)
  blockchain == "solana"    →  Solscan    (works without key, key = higher limits)
  anything else / no key    →  mock fallback

Smart money criteria (same for both chains):
  - Still holding (net balance > 0)
  - Has taken some profit (win_rate ≥ 30%)
  - Experienced trader (≥ 3 transactions)
  - Meaningful position (pnl ≥ $500)
"""

import hashlib
import random

import config
from pipeline.state import PipelineState, WalletAnalysis, WalletInfo
from services import etherscan, solscan
from utils.logger import get_logger

logger = get_logger(__name__)


# ── Etherscan (Ethereum) ──────────────────────────────────────────────────────

def _analyze_via_etherscan(token: dict) -> WalletAnalysis:
    contract = token["contract_address"]
    symbol = token["symbol"]
    price = token["current_price"]

    logger.info(f"wallet_analyzer [ETH]: querying Etherscan for {symbol}")
    buyers = etherscan.get_early_buyers(contract, limit=15)

    wallets: list[WalletInfo] = []
    for addr in buyers:
        result = etherscan.analyze_wallet(contract, addr, price)
        if result:
            wallets.append(result)

    if not wallets:
        logger.warning(f"wallet_analyzer [ETH]: no data for {symbol}, using mock")
        return _analyze_via_mock(token)

    return _build_analysis(symbol, token["trend_keyword"], wallets)


# ── Solscan (Solana) ──────────────────────────────────────────────────────────

def _analyze_via_solscan(token: dict) -> WalletAnalysis:
    mint = token["contract_address"]
    symbol = token["symbol"]
    price = token["current_price"]

    logger.info(f"wallet_analyzer [SOL]: querying Solscan for {symbol}")
    buyers = solscan.get_early_buyers(mint, limit=15)

    wallets: list[WalletInfo] = []
    for addr in buyers:
        result = solscan.analyze_wallet(mint, addr, price)
        if result:
            wallets.append(result)

    if not wallets:
        logger.warning(f"wallet_analyzer [SOL]: no data for {symbol}, using mock")
        return _analyze_via_mock(token)

    return _build_analysis(symbol, token["trend_keyword"], wallets)


# ── Mock fallback ─────────────────────────────────────────────────────────────

def _generate_mock_wallets(symbol: str) -> list[WalletInfo]:
    seed = int(hashlib.md5(symbol.encode()).hexdigest(), 16) % (2**31)
    rng = random.Random(seed)
    wallets: list[WalletInfo] = []
    for i in range(rng.randint(3, 8)):
        addr_seed = f"{symbol}-wallet-{i}"
        address = "0x" + hashlib.sha256(addr_seed.encode()).hexdigest()[:40]
        win_rate = round(rng.uniform(0.3, 0.9), 3)
        pnl = round(rng.uniform(-5_000, 150_000), 2)
        is_smart = win_rate >= 0.65 and pnl >= 10_000
        wallets.append({"address": address, "win_rate": win_rate, "pnl_usd": pnl, "is_smart_money": is_smart})
    return wallets


def _analyze_via_mock(token: dict) -> WalletAnalysis:
    wallets = _generate_mock_wallets(token["symbol"])
    return _build_analysis(token["symbol"], token["trend_keyword"], wallets)


# ── Shared ────────────────────────────────────────────────────────────────────

def _build_analysis(symbol: str, trend_keyword: str, wallets: list[WalletInfo]) -> WalletAnalysis:
    smart = [w for w in wallets if w["is_smart_money"]]
    avg_win = round(sum(w["win_rate"] for w in wallets) / len(wallets), 3) if wallets else 0.0
    return {
        "symbol": symbol,
        "trend_keyword": trend_keyword,
        "early_wallets": wallets,
        "smart_money_count": len(smart),
        "avg_win_rate": avg_win,
    }


# ── Node entry point ──────────────────────────────────────────────────────────

def wallet_analyzer(state: PipelineState) -> dict:
    """Route each token to the correct on-chain analyzer based on its blockchain."""
    logger.info("wallet_analyzer: analyzing wallets")
    analyses: list[WalletAnalysis] = []

    for token in state.get("market_data", []):
        symbol = token["symbol"]
        chain = token.get("blockchain", "")
        contract = token.get("contract_address", "")

        if chain == "ethereum" and contract and config.ETHERSCAN_API_KEY:
            analysis = _analyze_via_etherscan(token)

        elif chain == "solana" and contract:
            # Solscan works without a key (key just increases rate limits)
            analysis = _analyze_via_solscan(token)

        else:
            if not contract:
                reason = "no contract address"
            elif chain not in ("ethereum", "solana"):
                reason = f"chain={chain or 'unknown'} not supported yet"
            else:
                reason = "no ETHERSCAN_API_KEY"
            logger.info(f"wallet_analyzer: {symbol} → mock ({reason})")
            analysis = _analyze_via_mock(token)

        analyses.append(analysis)
        logger.info(
            f"wallet_analyzer: {symbol} [{chain or '?'}] — "
            f"{analysis['smart_money_count']} smart-money wallets, "
            f"avg win rate={analysis['avg_win_rate']:.1%}"
        )

    return {"wallet_analyses": analyses}
