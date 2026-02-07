"""
Cryptocurrency data tools for the AI agents.
"""

from langchain_core.tools import tool

from services.crypto_sources import CoinGeckoSource
from utils.logger import get_logger

logger = get_logger(__name__)

# Initialize source
crypto_source = CoinGeckoSource()


@tool
async def fetch_low_cap_cryptos(max_market_cap: int = 1000000, limit: int = 30) -> str:
    """
    Fetch cryptocurrencies with market cap below the threshold.
    These are potential gems with high upside but also high risk.

    Args:
        max_market_cap: Maximum market cap in USD (default $1 million)
        limit: Maximum number of coins to return (default 30)

    Returns:
        List of low-cap cryptocurrencies with price and volume data
    """
    logger.info(f"Fetching low-cap cryptos (max MC: ${max_market_cap:,})")

    cryptos = await crypto_source.fetch_low_cap_coins(
        max_market_cap=float(max_market_cap),
        limit=limit
    )

    if not cryptos:
        return "No low-cap cryptocurrencies found. Try increasing market cap threshold."

    result = f"💰 **Low-Cap Cryptocurrencies** (MC < ${max_market_cap:,}):\n\n"
    for c in cryptos[:limit]:
        emoji = "🟢" if c.price_change_24h_pct > 0 else "🔴"
        result += f"{emoji} **{c.name}** (${c.symbol.upper()})\n"
        result += f"   Price: ${c.current_price_usd:.8f}\n"
        result += f"   Market Cap: ${c.market_cap_usd:,.0f}\n"
        result += f"   24h Volume: ${c.volume_24h_usd:,.0f}\n"
        result += f"   24h Change: {c.price_change_24h_pct:+.2f}%\n\n"

    return result


@tool
async def search_crypto(query: str) -> str:
    """
    Search for cryptocurrencies by name, symbol, or keyword.
    Use this to find coins that might be related to a trending topic.

    Args:
        query: Search term (e.g., "penguin", "pepe", "dog", "meme")

    Returns:
        List of matching cryptocurrencies with basic metrics
    """
    logger.info(f"Searching crypto: {query}")

    cryptos = await crypto_source.search_coins(query)

    if not cryptos:
        return f"No cryptocurrencies found matching '{query}'. Try different keywords."

    result = f"🔍 **Crypto Search: '{query}'** (Found {len(cryptos)}):\n\n"
    for c in cryptos[:10]:
        result += f"• **{c.name}** (${c.symbol.upper()})\n"
        result += f"  ID: `{c.id}` (use this for detailed lookup)\n"
        result += f"  Price: ${c.current_price_usd:.8f} | "
        result += f"MC: ${c.market_cap_usd:,.0f}\n\n"

    return result


@tool
async def get_crypto_details(coin_id: str) -> str:
    """
    Get comprehensive details about a specific cryptocurrency.
    Use the coin_id from search results (e.g., 'bitcoin', 'ethereum').

    Args:
        coin_id: The CoinGecko ID of the cryptocurrency

    Returns:
        Detailed information including description, social links, and full metrics
    """
    logger.info(f"Getting details for coin: {coin_id}")

    crypto = await crypto_source.get_coin_details(coin_id)

    if not crypto:
        return f"Could not find cryptocurrency with ID '{coin_id}'. Check the ID is correct."

    result = f"## 📊 {crypto.name} (${crypto.symbol.upper()})\n\n"

    # Price metrics
    result += "### Price & Market Data\n"
    result += f"• **Current Price:** ${crypto.current_price_usd:.8f}\n"
    result += f"• **Market Cap:** ${crypto.market_cap_usd:,.0f}\n"
    result += f"• **24h Volume:** ${crypto.volume_24h_usd:,.0f}\n"
    result += f"• **24h Change:** {crypto.price_change_24h_pct:+.2f}%\n"
    result += f"• **7d Change:** {crypto.price_change_7d_pct:+.2f}%\n\n"

    # Risk assessment
    if crypto.market_cap_usd < 100000:
        risk = "🔴 EXTREME"
    elif crypto.market_cap_usd < 500000:
        risk = "🟠 HIGH"
    elif crypto.market_cap_usd < 1000000:
        risk = "🟡 MEDIUM-HIGH"
    else:
        risk = "🟢 MEDIUM"
    result += f"### Risk Level: {risk}\n\n"

    # Description
    if crypto.description:
        result += "### Description\n"
        result += f"{crypto.description[:600]}...\n\n"

    # Categories
    if crypto.categories:
        result += f"### Categories\n{', '.join(crypto.categories)}\n\n"

    # Links
    result += "### Links\n"
    if crypto.website:
        result += f"• Website: {crypto.website}\n"
    if crypto.twitter_handle:
        result += f"• Twitter: @{crypto.twitter_handle}\n"
    if crypto.telegram_url:
        result += f"• Telegram: {crypto.telegram_url}\n"

    # Contract
    if crypto.contract_address:
        result += f"\n### Contract\n"
        result += f"• Address: `{crypto.contract_address}`\n"
        if crypto.blockchain:
            result += f"• Blockchain: {crypto.blockchain}\n"

    return result


# Export all crypto tools
CRYPTO_TOOLS = [
    fetch_low_cap_cryptos,
    search_crypto,
    get_crypto_details,
]
