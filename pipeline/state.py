"""Shared state schema for the LangGraph pipeline.

Each node reads from and writes to this TypedDict.
Fields are appended/replaced as the pipeline progresses.
"""

from typing import TypedDict


class TrendSignal(TypedDict):
    keyword: str
    hashtags: list[str]
    views: int
    growth_rate: float   # % growth in last 24 hours
    source: str          # e.g. "tiktok"


class ValidatedTrend(TypedDict):
    keyword: str
    hashtags: list[str]
    google_score: int        # 0-100 Google Trends interest
    twitter_mentions: int    # 24-hour mention count
    momentum: float          # composite score 0-1
    is_increasing: bool


class TokenMatch(TypedDict):
    trend_keyword: str
    symbol: str
    name: str
    coingecko_id: str        # empty if source is dexscreener
    dex_pair_address: str    # empty if source is coingecko
    chain_id: str            # "ethereum", "solana", "bsc", etc.
    match_reason: str
    source: str              # "dexscreener" | "coingecko" | "mock"


class TokenMarketData(TypedDict):
    symbol: str
    name: str
    coingecko_id: str
    trend_keyword: str
    market_cap: float
    volume_24h: float
    liquidity: float            # volume / market_cap ratio
    supply_concentration: float # estimated % held by top 10 wallets
    price_change_24h: float
    current_price: float
    contract_address: str       # ERC-20 / BEP-20 contract (empty if unknown)
    blockchain: str             # e.g. "ethereum", "solana", "" if unknown


class WalletInfo(TypedDict):
    address: str
    win_rate: float   # 0-1
    pnl_usd: float
    is_smart_money: bool


class WalletAnalysis(TypedDict):
    symbol: str
    trend_keyword: str
    early_wallets: list[WalletInfo]
    smart_money_count: int
    avg_win_rate: float


class Opportunity(TypedDict):
    symbol: str
    name: str
    trend_keyword: str
    score: float            # composite 0-1
    trend_momentum: float
    market_quality: float
    smart_money_score: float
    verdict: str            # "BUY" | "WATCH" | "SKIP"
    market_cap: float
    volume_24h: float
    price_change_24h: float
    current_price: float


class PipelineState(TypedDict):
    raw_trends: list[TrendSignal]
    validated_trends: list[ValidatedTrend]
    token_matches: list[TokenMatch]
    market_data: list[TokenMarketData]
    wallet_analyses: list[WalletAnalysis]
    opportunities: list[Opportunity]
    errors: list[str]
