# Crypto Scout

Bot that detects viral trends and finds matching micro-cap tokens before they pump. Runs every hour and sends alerts to Discord.

## How It Works

```
Mock keywords → Validate (Google Trends) → Find token (DEXScreener + CoinGecko)
→ Analyze market → Check smart-money wallets → Score → Alert on Discord
```

**The edge**: takes a list of viral keywords, validates which ones are actually trending on Google right now, finds the matching memecoin on-chain (market cap < $5M), and alerts you before it pumps.

## Pipeline

| Step | Node | Data source | Status |
|------|------|-------------|--------|
| 1 | `trend_detector` | Mock keyword seeds | Mock |
| 2 | `trend_validator` | Google Trends (pytrends) | **Real** |
| 3 | `token_finder` | DEXScreener + CoinGecko | **Real** |
| 4 | `market_analyzer` | DEXScreener + CoinGecko | **Real** |
| 5 | `wallet_analyzer` | Etherscan (ETH) + Solscan (SOL) | **Real** |
| 6 | `scorer` | Composite score → BUY / WATCH / SKIP | — |

> **Note on mock sources**: Trend keywords (step 1) and social mention counts (step 2 Twitter weight) use mock data because TikTok and Twitter block automated scraping from all server/proxy IPs. The pipeline is still effective because Google Trends validation (step 2) filters out dead trends using real data.

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

## Deployment (GitHub Actions — free)

The bot runs automatically every hour via GitHub Actions. No server needed.

### Setup

1. Fork/clone this repo
2. Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Value |
|--------|-------|
| `DISCORD_WEBHOOK_URL` | Your Discord webhook URL |
| `ETHERSCAN_API_KEY` | From etherscan.io (free) |
| `GROQ_API_KEY` | From console.groq.com (free) |

3. Go to **Actions → Crypto Scout → Run workflow** to trigger manually

That's it. Alerts arrive in Discord every hour.

## Run Locally

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
python main.py         # single run
python main.py --schedule --interval 60  # every 60 min
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
│       ├── trend_detector.py      # Node 1: keyword seeds
│       ├── trend_validator.py     # Node 2: Google Trends validation
│       ├── token_finder.py        # Node 3: DEXScreener + CoinGecko
│       ├── market_analyzer.py     # Node 4: market data
│       ├── wallet_analyzer.py     # Node 5: on-chain wallets
│       └── scorer.py              # Node 6: scoring + verdict
└── services/
    ├── tiktok.py                  # Trend keyword seeds (mock)
    ├── google_trends.py           # Google Trends validation (real)
    ├── twitter.py                 # Social mention counts (mock)
    ├── dexscreener.py             # DEX pair data (real)
    ├── coingecko.py               # Market data (real)
    ├── etherscan.py               # Ethereum wallet analysis (real)
    ├── solscan.py                 # Solana wallet analysis (real)
    └── discord.py                 # Webhook alerts
```

## Updating Trend Keywords (TikTok)

The keyword seeds in `services/tiktok.py` are the trends the bot searches for. Update them manually whenever you want the bot to track new viral topics.

Open [services/tiktok.py](services/tiktok.py) and edit the list:

```python
{"keyword": "your new trend", "hashtags": ["#yourtrend"], "views": 500_000_000, "growth_rate": 300.0, "source": "mock"},
```

Then push to `dev`. The bot will start tracking that keyword on the next run.

**Where to find trending topics:**
- [TikTok Trending](https://www.tiktok.com/trending) — browse manually
- [Google Trends](https://trends.google.com/trending) — top trending searches
- Crypto Twitter / Discord — what's being talked about

## Risk Warning

- Memecoins are **extremely speculative** — most go to zero
- Low-cap tokens can lose 100% of value in minutes
- **Never invest more than you can afford to lose**
- This is **NOT financial advice**

## License

MIT
