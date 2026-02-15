# Crypto Scout

AI-powered system for discovering viral trends and matching them to low-cap cryptocurrencies.

## What It Does

Crypto Scout catches investment opportunities from **two angles**:

1. **Mainstream Viral Trends** → Find related memecoins
   - "Moo Deng" (baby hippo) trending → Find $MOODENG coin
   - "Hawk Tuah" meme viral → Find $HAWKTUAH coin
   - "Chill Guy" meme everywhere → Find $CHILLGUY coin

2. **Crypto Twitter Mentions** → Track hyped coins directly
   - "$PEPE is mooning!" → Direct signal
   - "Everyone's buying $PENGU" → Direct signal

**The alpha**: Catch mainstream trends BEFORE crypto Twitter notices them.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CRYPTO SCOUT SUPERVISOR                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
         ┌─────────────────────────────────────────────┐
         │            TREND DISCOVERY                   │
         │  ┌─────────────────┐ ┌───────────────────┐  │
         │  │ General Trends  │ │ Crypto Mentions   │  │
         │  │ (viral topics)  │ │ ($PENGU, $PEPE)   │  │
         │  │                 │ │                   │  │
         │  │ • Moo Deng      │ │ • $MOODENG hype   │  │
         │  │ • Hawk Tuah     │ │ • $PEPE mentions  │  │
         │  │ • Chill Guy     │ │ • $TRUMP trending │  │
         │  │ • Trump news    │ │ • $WIF discussed  │  │
         │  └─────────────────┘ └───────────────────┘  │
         └──────────────────────┬──────────────────────┘
                                │
                                ▼
                  ┌─────────────────────────┐
                  │    CRYPTO ANALYSIS      │
                  │  CoinGecko + LLM Match  │
                  │                         │
                  │  • Find matching coins  │
                  │  • Score opportunities  │
                  │  • Assess risk levels   │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │     NOTIFICATIONS       │
                  │   WhatsApp (Twilio)     │
                  └─────────────────────────┘
```

## Features

- **Dual Detection Strategy**: Both mainstream viral trends AND crypto Twitter mentions
- **AI-Powered Matching**: LLM analyzes thematic connections (penguin trend → penguin coins)
- **Real Crypto Data**: CoinGecko API for actual prices and market caps
- **Low-Cap Focus**: Filters for coins under $1M market cap (maximum upside potential)
- **WhatsApp Alerts**: Instant notifications via Twilio
- **Mock Data Testing**: Test full flow without expensive API costs

## Quick Start

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```bash
# Required: LLM (choose one)
GROQ_API_KEY=gsk_...        # Free & fast (recommended)
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# GOOGLE_API_KEY=...

# Optional: WhatsApp notifications
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_FROM=+14155238886
TWILIO_WHATSAPP_TO=+1234567890
```

### 3. Run

```bash
# Full scan (trends + crypto + notifications)
python main.py scan

# Continuous monitoring (every 5 min)
python main.py continuous --interval 5

# Interactive mode
python main.py interactive

# Trend discovery only
python main.py trends

# Crypto analysis only
python main.py crypto
```

## Example Output

```
============================================================
SCAN RESULTS
============================================================

📊 Found 10 general trends + 10 crypto mentions

### Trends Discovered: 15
• $MOODENG (96%)      ← Direct crypto mention
• moo deng (92%)      ← Mainstream viral trend
• $CHILLGUY (91%)     ← Direct crypto mention
• chill guy (85%)     ← Mainstream viral trend
• $TRUMP (94%)        ← Direct crypto mention

### Recommendations: 5
• Moo Deng (MOODENG) - Score: 96% - BUY
• Chill Guy (CHILLGUY) - Score: 91% - BUY
• Trump MAGA (TRUMP) - Score: 90% - CONSIDER
• Pepe (PEPE) - Score: 85% - WATCH
• Capybara (CAPY) - Score: 75% - WATCH

### Notifications Sent: 3 via WhatsApp
```

## How The Dual Strategy Works

### Approach 1: Mainstream Trends → Find Coins

```
VIRAL TOPIC                    MATCHING CRYPTO
─────────────────────────────────────────────
"Moo Deng" baby hippo    →    $MOODENG token
"Hawk Tuah" meme girl    →    $HAWKTUAH coin
"Chill Guy" cartoon      →    $CHILLGUY token
"Capybara" cute animal   →    $CAPY coin
Trump in the news        →    $TRUMP memecoins
```

**Why this works**: When something goes viral in mainstream culture, degens create memecoins. If you catch the trend early, you can find the coin before everyone else.

### Approach 2: Crypto Mentions → Direct Signal

```
TWITTER CRYPTO DISCUSSION      SIGNAL
─────────────────────────────────────────────
"$PEPE is pumping!"       →    High mention volume
"Aping into $MOODENG"     →    Bullish sentiment
"$WIF community strong"   →    Community activity
```

**Why this works**: When crypto Twitter is actively discussing a coin with bullish sentiment, that's a direct signal of interest.

## WhatsApp Setup (Optional)

1. Create account at [twilio.com](https://www.twilio.com)
2. Go to **Messaging** → **Try it out** → **WhatsApp Sandbox**
3. Follow instructions to join the sandbox (send a WhatsApp message)
4. Copy your credentials to `.env`:
   - Account SID
   - Auth Token
   - Your phone number

## Project Structure

```
crypto-scout/
├── agents/                 # LangGraph AI agents
│   ├── tools/              # Agent tools
│   │   ├── trend_tools.py  # Trend discovery tools
│   │   └── crypto_tools.py # Crypto analysis tools
│   ├── llm.py              # LLM configuration (Groq/OpenAI/Anthropic)
│   ├── trend_agent.py      # Trend discovery agent
│   ├── crypto_agent.py     # Crypto analysis agent
│   └── supervisor.py       # Multi-agent orchestrator
├── services/
│   ├── trend_sources/
│   │   └── twitter.py      # Twitter mock data (both approaches)
│   ├── crypto_sources/
│   │   └── coingecko.py    # CoinGecko API (real data)
│   ├── notifications/
│   │   └── whatsapp.py     # WhatsApp via Twilio
│   └── matching.py         # Trend-crypto matching logic
├── models/                 # Pydantic data models
├── config/                 # Configuration
└── main.py                 # Entry point
```

## Data Sources

| Component | Source | Status |
|-----------|--------|--------|
| General Trends | Twitter | Mock data (realistic) |
| Crypto Mentions | Twitter | Mock data (realistic) |
| Crypto Prices | CoinGecko | Real API |
| Analysis | Groq/OpenAI LLM | Real API |
| Notifications | Twilio WhatsApp | Real API |

**Why mock Twitter?** Twitter API costs $100+/month. Mock data lets you test the full system for free while still being realistic.

## Extending

### Add Real Twitter Data
Replace mock data in `services/trend_sources/twitter.py` with real Twitter API calls.

### Add More Trend Sources
- Google Trends
- Reddit (r/cryptocurrency, r/memecoins)
- TikTok viral sounds
- Discord server activity

### Add More Notification Channels
- Telegram bot
- Discord webhook
- Email alerts

## Risk Warning

This software is for educational and research purposes only.

- Cryptocurrency investments are **extremely speculative**
- Low-cap memecoins can lose **100% of value** in minutes
- **Never invest more than you can afford to lose**
- Always do your own research (DYOR)
- This is **NOT financial advice**

## License

MIT
