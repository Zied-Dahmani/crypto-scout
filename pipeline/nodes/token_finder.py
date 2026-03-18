"""Node 3 — token_finder: Find crypto tokens related to each validated trend.

Search order:
  1. DEXScreener  — catches brand-new tokens before CoinGecko lists them
  2. CoinGecko    — fallback for established tokens not on DEX yet
  3. Mock map     — offline fallback when both APIs fail

Deduplicates by contract address across all sources.
"""

from pipeline.state import PipelineState, TokenMatch
from services import coingecko, dexscreener
from utils.logger import get_logger

logger = get_logger(__name__)

_MIN_DEX_VOLUME = 1_000   # USD — skip ghost pairs

# Offline fallback map: keyword → (symbol, name, coingecko_id)
_MOCK_MAP: dict[str, tuple[str, str, str]] = {
    "moo deng":      ("MOODENG",   "Moo Deng",         "moo-deng"),
    "chill guy":     ("CHILLGUY",  "Chill Guy",         "chill-guy"),
    "skibidi":       ("SKIBIDI",   "Skibidi Toilet",    "skibidi-token"),
    "hawk tuah":     ("HAWKTUAH",  "Hawk Tuah",         "hawk-tuah"),
    "trump":         ("TRUMPMAGA", "Trump MAGA",         "trump-maga"),
    "pepe":          ("MINIPEPE",  "Mini Pepe",         "mini-pepe"),
    "dogwifhat":     ("WIFMINI",   "Dog Wif Mini Hat",  "dogwifhat-mini"),
    "capybara":      ("CAPY",      "Capybara",          "capybara-token"),
    "griddy":        ("GRIDDY",    "Griddy",            "griddy-coin"),
    "pudgy penguin": ("PENGU",     "Pudgy Penguins",    "pudgy-penguins-token"),
}


def _from_dexscreener(keyword: str) -> list[TokenMatch]:
    pairs = dexscreener.search_pairs(keyword, limit=3)
    matches: list[TokenMatch] = []
    for p in pairs:
        if p["volume_24h"] < _MIN_DEX_VOLUME:
            continue
        matches.append(
            {
                "trend_keyword": keyword,
                "symbol": p["symbol"],
                "name": p["name"],
                "coingecko_id": "",
                "dex_pair_address": p["pair_address"],
                "chain_id": p["chain_id"],
                "match_reason": f"DEXScreener match for '{keyword}' on {p['chain_id']}",
                "source": "dexscreener",
            }
        )
    return matches


def _from_coingecko(keyword: str) -> list[TokenMatch]:
    coins = coingecko.search_coins(keyword)
    matches: list[TokenMatch] = []
    for coin in coins[:3]:
        cid = coin.get("id", "")
        if not cid:
            continue
        matches.append(
            {
                "trend_keyword": keyword,
                "symbol": coin.get("symbol", "").upper(),
                "name": coin.get("name", ""),
                "coingecko_id": cid,
                "dex_pair_address": "",
                "chain_id": "",
                "match_reason": f"CoinGecko search match for '{keyword}'",
                "source": "coingecko",
            }
        )
    return matches


def token_finder(state: PipelineState) -> dict:
    """Discover tokens for each validated trend — DEXScreener first, CoinGecko fallback."""
    logger.info("token_finder: discovering tokens")

    all_matches: list[TokenMatch] = []
    seen_contracts: set[str] = set()  # deduplicate by contract address
    seen_cg_ids: set[str] = set()     # deduplicate CoinGecko results

    for trend in state.get("validated_trends", []):
        keyword = trend["keyword"]
        found = False

        # 1️⃣ DEXScreener — catches newest, smallest tokens first
        dex_matches = _from_dexscreener(keyword)
        for m in dex_matches:
            key = m["dex_pair_address"] or m["symbol"]
            if key not in seen_contracts:
                seen_contracts.add(key)
                all_matches.append(m)
                logger.info(f"token_finder [DEX]: {m['symbol']} ({m['chain_id']}) ← '{keyword}'")
                found = True

        # 2️⃣ CoinGecko — only if DEX found nothing (avoids surfacing large established coins)
        if not found:
            cg_matches = _from_coingecko(keyword)
            for m in cg_matches:
                if m["coingecko_id"] not in seen_cg_ids:
                    seen_cg_ids.add(m["coingecko_id"])
                    all_matches.append(m)
                    logger.info(f"token_finder [CG]: {m['symbol']} ← '{keyword}' (no DEX results)")
                    found = True

        if not found:
            logger.warning(f"token_finder: no results for '{keyword}'")

    # 3️⃣ Mock fallback when both APIs failed
    if not all_matches:
        logger.warning("token_finder: both APIs returned nothing, using mock tokens")
        for trend in state.get("validated_trends", []):
            kw = trend["keyword"].lower()
            if kw in _MOCK_MAP:
                sym, name, cid = _MOCK_MAP[kw]
                all_matches.append(
                    {
                        "trend_keyword": trend["keyword"],
                        "symbol": sym,
                        "name": name,
                        "coingecko_id": cid,
                        "dex_pair_address": "",
                        "chain_id": "",
                        "match_reason": f"Mock match for '{kw}'",
                        "source": "mock",
                    }
                )

    logger.info(f"token_finder: {len(all_matches)} tokens identified")
    return {"token_matches": all_matches}
