"""Node 4 — market_analyzer: Retrieve market data for each discovered token.

Data source priority per token:
  - DEXScreener source → use stored DEX pair data directly
    (real liquidity pool USD, auto contract address, works for brand-new tokens)
  - CoinGecko source   → fetch /markets + /coins/{id} for contract address

DEXScreener liquidity is more accurate: it's the actual pool reserve value,
not a volume/mcap heuristic.
"""

import config
from pipeline.state import PipelineState, TokenMarketData
from services import coingecko, dexscreener
from utils.logger import get_logger

logger = get_logger(__name__)

_PREFERRED_CHAINS = ["ethereum", "binance-smart-chain", "polygon-pos", "arbitrum-one"]


def _estimate_supply_concentration(market_cap: float) -> float:
    if market_cap < 100_000:
        return 0.85
    if market_cap < 500_000:
        return 0.72
    if market_cap < 1_000_000:
        return 0.58
    return 0.45


def _extract_contract(platforms: dict) -> tuple[str, str]:
    for chain in _PREFERRED_CHAINS:
        addr = platforms.get(chain, "")
        if addr:
            return chain, addr
    for chain, addr in platforms.items():
        if addr:
            return chain, addr
    return "", ""


def _from_dex(match: dict) -> TokenMarketData | None:
    """Fetch market data from DEXScreener using the stored pair address."""
    pair = dexscreener.get_pair(match["dex_pair_address"], match["chain_id"])
    if not pair:
        return None

    base = pair.get("baseToken", {})
    market_cap = float(pair.get("marketCap") or pair.get("fdv") or 0)
    volume_24h = float((pair.get("volume") or {}).get("h24") or 0)
    liquidity_usd = float((pair.get("liquidity") or {}).get("usd") or 0)
    # Liquidity ratio: pool size relative to market cap (more meaningful than vol/mcap)
    liquidity_ratio = round(liquidity_usd / market_cap, 4) if market_cap > 0 else 0.0
    price = float(pair.get("priceUsd") or 0)
    price_change = float((pair.get("priceChange") or {}).get("h24") or 0)
    contract = base.get("address", "")
    blockchain = pair.get("chainId", match["chain_id"])

    return {
        "symbol": match["symbol"],
        "name": match["name"],
        "coingecko_id": "",
        "trend_keyword": match["trend_keyword"],
        "market_cap": market_cap,
        "volume_24h": volume_24h,
        "liquidity": liquidity_ratio,
        "supply_concentration": _estimate_supply_concentration(market_cap),
        "price_change_24h": price_change,
        "current_price": price,
        "contract_address": contract,
        "blockchain": blockchain,
        "pair_created_at": int(pair.get("pairCreatedAt") or 0),
    }


def _from_coingecko(match: dict, raw_by_id: dict) -> TokenMarketData | None:
    """Build market data from CoinGecko market + coin details."""
    raw = raw_by_id.get(match["coingecko_id"])
    if not raw:
        return None

    market_cap = float(raw.get("market_cap") or 0)
    volume_24h = float(raw.get("total_volume") or 0)
    liquidity = round(volume_24h / market_cap, 4) if market_cap > 0 else 0.0

    details = coingecko.get_coin_details(match["coingecko_id"])
    platforms = details.get("platforms", {}) if details else {}
    blockchain, contract_address = _extract_contract(platforms)

    return {
        "symbol": match["symbol"],
        "name": match["name"],
        "coingecko_id": match["coingecko_id"],
        "trend_keyword": match["trend_keyword"],
        "market_cap": market_cap,
        "volume_24h": volume_24h,
        "liquidity": liquidity,
        "supply_concentration": _estimate_supply_concentration(market_cap),
        "price_change_24h": float(raw.get("price_change_percentage_24h") or 0),
        "current_price": float(raw.get("current_price") or 0),
        "contract_address": contract_address,
        "blockchain": blockchain,
        "pair_created_at": 0,
    }


def market_analyzer(state: PipelineState) -> dict:
    """Fetch and structure market data for each token match."""
    logger.info("market_analyzer: fetching market data")
    matches = state.get("token_matches", [])
    if not matches:
        return {"market_data": []}

    # Pre-fetch CoinGecko batch for all CG-sourced tokens
    cg_ids = [m["coingecko_id"] for m in matches if m.get("coingecko_id")]
    raw_cg = {c["id"]: c for c in coingecko.get_market_data(cg_ids)} if cg_ids else {}

    if not raw_cg and cg_ids:
        logger.warning("market_analyzer: CoinGecko returned nothing, using mock")
        raw_cg = {c["id"]: c for c in coingecko.get_mock_coins()}

    market_data: list[TokenMarketData] = []

    for match in matches:
        source = match.get("source", "coingecko")

        if source == "dexscreener":
            token = _from_dex(match)
        else:
            token = _from_coingecko(match, raw_cg)

        if not token:
            logger.warning(f"market_analyzer: no data for {match['symbol']}")
            continue

        # Filter out large-cap / established coins — focus on early-stage only
        if token["market_cap"] > config.MAX_TOKEN_MARKET_CAP:
            logger.info(
                f"market_analyzer: dropping {match['symbol']} "
                f"(mcap=${token['market_cap']:,.0f} exceeds ${config.MAX_TOKEN_MARKET_CAP:,.0f} cap)"
            )
            continue

        market_data.append(token)
        logger.info(
            f"market_analyzer [{source}]: {match['symbol']} — "
            f"mcap=${token['market_cap']:,.0f}, "
            f"vol=${token['volume_24h']:,.0f}, "
            f"liq={token['liquidity']:.2f}, "
            f"chain={token['blockchain'] or 'unknown'}"
        )

    return {"market_data": market_data}
