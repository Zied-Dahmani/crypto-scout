# Crypto Scout

AI-powered system for discovering viral trends and matching them to low-cap cryptocurrencies.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CRYPTO SCOUT SUPERVISOR                   │
│                   (LangGraph Orchestrator)                   │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   │                   ▼
┌─────────────────┐           │         ┌─────────────────┐
│  TREND AGENT    │           │         │  CRYPTO AGENT   │
│  (LLM + Tools)  │           │         │  (LLM + Tools)  │
├─────────────────┤           │         ├─────────────────┤
│ • Twitter Mock  │           │         │ • CoinGecko API │
│ • Trend Scoring │           │         │ • Matching Svc  │
└─────────────────┘           │         └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  NOTIFICATIONS  │
                    │    WhatsApp     │
                    └─────────────────┘
```

## Features

- **Multi-Agent Architecture**: LangGraph-powered supervisor orchestrating specialized agents
- **Trend Discovery**: Twitter trend simulation with mock data (cost-optimized)
- **Crypto Matching**: Semantic and keyword matching between trends and cryptocurrencies
- **Low-Cap Focus**: Filters for coins under $1M market cap for maximum upside
- **AI-Powered Analysis**: LLM agents reason about matches and generate recommendations
- **WhatsApp Notifications**: Alerts via WhatsApp (Twilio) for high-confidence opportunities

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run

```bash
# Single scan
python main.py scan

# Continuous monitoring (every 5 min)
python main.py continuous --interval 5

# Interactive mode
python main.py interactive

# Trend discovery only
python main.py trends

# Crypto analysis only
python main.py crypto --keywords penguin pepe
```

## Project Structure

```
crypto-scout/
├── agents/                 # LangGraph AI agents
│   ├── tools/              # Agent tools
│   │   ├── trend_tools.py  # Twitter discovery (mock)
│   │   ├── crypto_tools.py # CoinGecko integration
│   │   └── analysis_tools.py # Matching & scoring
│   ├── llm.py              # LLM configuration
│   ├── trend_agent.py      # Trend discovery agent
│   ├── crypto_agent.py     # Crypto analysis agent
│   └── supervisor.py       # Multi-agent orchestrator
├── services/               # Backend services
│   ├── trend_sources/      # Social media integrations
│   │   ├── base.py         # Abstract base class
│   │   └── twitter.py      # Twitter mock data source
│   ├── crypto_sources/     # Crypto data integrations
│   │   ├── base.py         # Abstract base class
│   │   └── coingecko.py    # CoinGecko API
│   ├── notifications/      # Notification services
│   │   ├── base.py         # Abstract base class
│   │   └── whatsapp.py     # WhatsApp via Twilio
│   └── matching.py         # Trend-crypto matching
├── models/                 # Pydantic data models
├── config/                 # Configuration
├── utils/                  # Logging utilities
└── main.py                 # Entry point
```

## How It Works

### 1. Trend Discovery Agent

The trend agent uses an LLM with tools to:
- Fetch simulated Twitter trends (mock data for cost optimization)
- Score trends by virality (engagement rate, growth speed)
- Filter for potentially crypto-relevant trends

### 2. Crypto Analysis Agent

The crypto agent uses an LLM with tools to:
- Fetch low-cap cryptocurrencies from CoinGecko
- Search for coins matching trend keywords
- Analyze trend-crypto matches using semantic similarity
- Calculate investment scores based on match quality + market metrics
- Generate structured recommendations

### 3. Supervisor

The supervisor orchestrates the workflow:
1. Initializes the scan
2. Runs trend discovery agent
3. Passes trends to crypto analysis agent
4. Evaluates recommendations
5. Sends WhatsApp notifications for high-confidence opportunities
6. Generates summary report

## Configuration

### Required: LLM API Key

```bash
# OpenAI (recommended)
OPENAI_API_KEY=sk-...
LLM_PROVIDER=openai

# OR Anthropic
ANTHROPIC_API_KEY=sk-ant-...
LLM_PROVIDER=anthropic
```

### Optional: CoinGecko API

For higher rate limits on crypto data:
```bash
COINGECKO_API_KEY=CG-...
```

### Optional: WhatsApp Notifications

WhatsApp notifications are sent via Twilio:

1. Sign up at [twilio.com](https://www.twilio.com)
2. Enable WhatsApp sandbox
3. Set Twilio credentials:

```bash
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_FROM=+14155238886
TWILIO_WHATSAPP_TO=+1234567890
```

## Example Output

```
🚀 CRYPTO SCOUT ALERT

📈 Trending Topic: penguin
🔥 Virality Score: 85%
📊 Source: Twitter

💰 Matched Crypto: Pudgy Penguins (PENGU)
💵 Price: $0.000025
📊 Market Cap: $850,000
📈 24h Change: +45.5%

🎯 Match Score: 78%
🔮 Confidence: 72%
⚠️ Risk Level: HIGH
💡 Action: CONSIDER

📝 Reasoning: Strong keyword match between trending "penguin"
topic and Pudgy Penguins crypto. High virality trend with
positive price momentum. Low market cap suggests upside potential.

⚠️ DYOR - Not financial advice
```

## Extending

### Add New Trend Source

1. Create `services/trend_sources/discord.py`
2. Extend `BaseTrendSource`
3. Add to trend agent tools

### Add New Crypto Source

1. Create `services/crypto_sources/dexscreener.py`
2. Extend `BaseCryptoSource`
3. Add to crypto agent tools

### Add New Notification Channel

1. Create `services/notifications/discord.py`
2. Extend `BaseNotificationService`
3. Update config and supervisor

## Disclaimer

This software is for educational and research purposes only.

- Cryptocurrency investments are highly speculative
- Low-cap coins can lose 100% of value
- Never invest more than you can afford to lose
- Always do your own research (DYOR)
- This is NOT financial advice

## License

MIT
