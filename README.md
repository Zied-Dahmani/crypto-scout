# Crypto Scout

Bot that detects what's going viral right now, finds the matching micro-cap memecoin on-chain, and alerts you on Discord before it pumps. Runs every 6 hours automatically via GitHub Actions.

## How It Works

```
Google Trends RSS (what's viral now)
  → Validate: Google Trends + TikTok viral videos (Apify)
  → Find token: DEXScreener (newest first) + CoinGecko fallback
  → Analyze: live price, volume, liquidity, market cap
  → Check wallets: smart-money early buyers (Etherscan / Solscan)
  → Score → Discord alert
```

**The edge:** a person/meme/animal goes viral on Google → someone launches a memecoin → bot finds it at $50k–$5M market cap before the crowd.

## Pipeline

| Step | Node | Data source | Status |
|------|------|-------------|--------|
| 1 | `trend_detector` | Google Trends RSS (US, CA, GB, FR, DE, JP, KR, AU, CN) | **Real** |
| 2 | `trend_validator` | Google Trends interest + Apify TikTok viral count | **Real** |
| 3 | `token_finder` | DEXScreener + CoinGecko | **Real** |
| 4 | `market_analyzer` | DEXScreener + CoinGecko | **Real** |
| 5 | `wallet_analyzer` | Etherscan (ETH) + Solscan (SOL) | **Real** |
| 6 | `scorer` | Composite score → BUY / WATCH / SKIP | — |

**Scoring formula:**
```
score = 0.40 × trend_momentum + 0.35 × market_quality + 0.25 × smart_money
```
- `BUY`   ≥ 0.72
- `WATCH` ≥ 0.52
- `SKIP`  < 0.52

**Token filters:**
- Market cap ≤ $5M
- Pair age ≤ 90 days
- Liquidity ≥ $5K

**Expected alerts per run:** 0–3 cards. Quiet days = 0–1. Viral meme/person days = 2–5.

**Sports filtering:** Routine fixtures (e.g. "Watford vs Leicester") are automatically filtered. Extraordinary sports moments with 500k+ searches (Super Bowl, Champions League final upset) are kept — they spawn coins too.

## Deployment (GitHub Actions — free)

Runs automatically every 6 hours. No server needed.

### Setup

1. Fork/clone this repo
2. Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Where to get | Required |
|--------|-------------|---------|
| `DISCORD_WEBHOOK_URL` | Discord → channel settings → Integrations → Webhooks | Yes |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) (free) | Yes |
| `ETHERSCAN_API_KEY` | [etherscan.io](https://etherscan.io/apis) (free) | Recommended |
| `APIFY_API_KEY` | [apify.com](https://apify.com) → Settings → Integrations (free tier) | Recommended |
| `COINGECKO_API_KEY` | [coingecko.com](https://coingecko.com/en/api) (free tier) | Optional |

3. Go to **Actions → Crypto Scout → Run workflow** to trigger manually

Alerts arrive in Discord at 00:00, 06:00, 12:00, 18:00 UTC.

## Run Locally

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
python main.py                        # single run
python main.py --schedule --interval 360  # every 6 hours
```

## Project Structure

```
crypto-scout/
├── main.py                        # Entry point
├── config.py                      # Env-var config + thresholds
├── pipeline/
│   ├── graph.py                   # LangGraph StateGraph wiring
│   ├── state.py                   # TypedDicts for pipeline state
│   └── nodes/
│       ├── trend_detector.py      # Node 1: Google Trends RSS
│       ├── trend_validator.py     # Node 2: Google Trends + TikTok viral
│       ├── token_finder.py        # Node 3: DEXScreener + CoinGecko
│       ├── market_analyzer.py     # Node 4: market data
│       ├── wallet_analyzer.py     # Node 5: on-chain wallets
│       └── scorer.py              # Node 6: scoring + verdict
└── services/
    ├── tiktok.py                  # Google Trends RSS (trend discovery)
    ├── twitter.py                 # Apify TikTok viral count (social signal)
    ├── google_trends.py           # Google Trends interest validation
    ├── dexscreener.py             # DEX pair data
    ├── coingecko.py               # Market data
    ├── etherscan.py               # Ethereum wallet analysis
    ├── solscan.py                 # Solana wallet analysis
    └── discord.py                 # Webhook alerts
```

## Updating Trend Keywords Manually

If the bot misses a viral trend you spotted, edit `services/tiktok.py` mock list and push to `dev`. The mock list is the fallback used when Google Trends RSS is unavailable.

## Risk Warning

- Memecoins are **extremely speculative** — most go to zero
- Low-cap tokens can lose 100% of value in minutes
- **Never invest more than you can afford to lose**
- This is **NOT financial advice**

## License

MIT
