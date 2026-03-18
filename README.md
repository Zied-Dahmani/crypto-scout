# Crypto Scout

AI-powered bot that detects viral trends on TikTok and finds matching micro-cap tokens before the crowd.

## How It Works

```
TikTok trending  →  Validate (Google Trends + Twitter)  →  Find token on DEXScreener
→  Analyze market data  →  Check smart-money wallets  →  Score & alert on Discord
```

**The edge**: catches a trend going viral on TikTok, finds the matching memecoin on-chain (market cap < $5M), and alerts you before it pumps.

## Pipeline

| Step | Node | What it does |
|------|------|-------------|
| 1 | `trend_detector` | Scrapes TikTok trending page via Playwright |
| 2 | `trend_validator` | Cross-checks with Google Trends + Twitter mentions |
| 3 | `token_finder` | Searches DEXScreener (newest first), falls back to CoinGecko |
| 4 | `market_analyzer` | Fetches liquidity, volume, price from DEXScreener / CoinGecko |
| 5 | `wallet_analyzer` | Checks early buyers on Etherscan (ETH) or Solscan (SOL) |
| 6 | `scorer` | Composite score → BUY / WATCH / SKIP |

**Scoring formula:**
```
score = 0.40 × trend_momentum + 0.35 × market_quality + 0.25 × smart_money
```
- `BUY`   ≥ 0.72
- `WATCH` ≥ 0.52
- `SKIP`  < 0.52

**Filters applied:**
- Market cap ceiling: **$5M** (drop established coins)
- Pair age ceiling: **90 days** (drop old pairs)
- Minimum liquidity: **$5K** (drop ghost pairs)

## Quick Start

### 1. Install

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure

```bash
cp .env.example .env
```

Fill in `.env` — see the table below for what's required vs optional.

### 3. Run

```bash
# Single scan
python main.py

# Scheduled — runs every 30 minutes and sends Discord alerts
python main.py --schedule --interval 30
```

## API Keys

| Key | Where to get | Required? |
|-----|-------------|-----------|
| `DISCORD_WEBHOOK_URL` | Discord → channel settings → Integrations → Webhooks | Yes (for alerts) |
| `ETHERSCAN_API_KEY` | [etherscan.io](https://etherscan.io) → API Keys (free) | Recommended |
| `TIKTOK_MS_TOKEN` | Browser DevTools → tiktok.com cookies → `msToken` | Recommended |
| `COINGECKO_API_KEY` | [coingecko.com](https://coingecko.com) → API (free tier) | Optional |
| `SOLSCAN_API_KEY` | [pro.solscan.io](https://pro.solscan.io) → API Key (free tier) | Optional |
| `TWITTER_SCRAPER_USERNAME` | Any free Twitter account | Optional |
| `TWITTER_SCRAPER_PASSWORD` | Same account | Optional |
| `TWITTER_SCRAPER_EMAIL` | Same account | Optional |

All missing keys fall back to mock data — the pipeline always completes.

## TikTok Token Setup

TikTok requires a session cookie (`msToken`) to serve trending data.

1. Open your browser, go to [tiktok.com](https://tiktok.com) and log in
2. Open DevTools (`F12`) → **Application** → **Cookies** → `https://www.tiktok.com`
3. Copy the value of `msToken`
4. Add to `.env`: `TIKTOK_MS_TOKEN=<value>`

The scraper auto-refreshes the token on every run via Playwright.

## Twitter Setup (Free)

No paid API needed — uses `twscrape` which scrapes via a regular Twitter account.

1. Create a throwaway Twitter account at [twitter.com](https://twitter.com)
2. Add to `.env`:
```
TWITTER_SCRAPER_USERNAME=your_username
TWITTER_SCRAPER_PASSWORD=your_password
TWITTER_SCRAPER_EMAIL=your_email@gmail.com
```

## Project Structure

```
crypto-scout/
├── main.py                        # Entry point (--schedule --interval flags)
├── config.py                      # All env-var config + thresholds
├── pipeline/
│   ├── graph.py                   # LangGraph StateGraph wiring
│   ├── state.py                   # TypedDicts for pipeline state
│   └── nodes/
│       ├── trend_detector.py      # Node 1: TikTok trends
│       ├── trend_validator.py     # Node 2: Google Trends + Twitter
│       ├── token_finder.py        # Node 3: DEXScreener + CoinGecko
│       ├── market_analyzer.py     # Node 4: market data
│       ├── wallet_analyzer.py     # Node 5: on-chain wallets
│       └── scorer.py              # Node 6: scoring + verdict
└── services/
    ├── tiktok.py                  # Playwright scraper + mock fallback
    ├── google_trends.py           # pytrends wrapper
    ├── twitter.py                 # twscrape wrapper + mock fallback
    ├── dexscreener.py             # Free DEX API
    ├── coingecko.py               # CoinGecko API
    ├── etherscan.py               # Ethereum on-chain data
    ├── solscan.py                 # Solana on-chain data
    └── discord.py                 # Webhook alerts
```

## Example Output

```
==============================================================
  CRYPTO OPPORTUNITY DETECTION — RESULTS
==============================================================
  Trends detected  : 10
  Trends validated : 4
  Tokens found     : 12
  Opportunities    : 3

  #1 🟢 [BUY]   NEWMEME — New Meme Token
      Trend      : newmeme
      Score      : 0.741  (trend=0.93, market=0.68, smart=0.52)
      Market cap : $     284,000
      Volume 24h : $     198,000
      Price      : $0.00000284

  #2 🟡 [WATCH] SKBDI — Skibidi Toilet
      Score      : 0.525  (trend=0.45, market=0.75, smart=0.32)
      Market cap : $     366,932
```

## Risk Warning

This software is for educational and research purposes only.

- Memecoins are **extremely speculative** — most go to zero
- Low-cap tokens can lose 100% of value in minutes
- **Never invest more than you can afford to lose**
- Always do your own research (DYOR)
- This is **NOT financial advice**

## License

MIT
