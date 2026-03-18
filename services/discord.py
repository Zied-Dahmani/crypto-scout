"""Discord webhook notifications.

Setup (30 seconds):
  1. Open your Discord server → any channel → Edit Channel
  2. Integrations → Webhooks → New Webhook → Copy Webhook URL
  3. Add to .env:  DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

Without a webhook URL, notifications are silently skipped.
"""

import requests

import config
from utils.logger import get_logger

logger = get_logger(__name__)

# Embed colours
_COLOR = {"BUY": 0x00C851, "WATCH": 0xFFBB33, "SKIP": 0xFF4444}


def _build_embed(opp: dict) -> dict:
    verdict = opp["verdict"]
    icon = {"BUY": "🟢", "WATCH": "🟡", "SKIP": "🔴"}.get(verdict, "")

    return {
        "title": f"{icon} {verdict} — {opp['symbol']}  ({opp['name']})",
        "color": _COLOR.get(verdict, 0x888888),
        "fields": [
            {"name": "📈 Trend",         "value": opp["trend_keyword"],                      "inline": True},
            {"name": "⚡ Score",          "value": f"{opp['score']:.3f}",                     "inline": True},
            {"name": "💰 Market Cap",     "value": f"${opp['market_cap']:,.0f}",               "inline": True},
            {"name": "📊 Volume 24h",     "value": f"${opp['volume_24h']:,.0f}",               "inline": True},
            {"name": "🕯️ Price Change",   "value": f"{opp['price_change_24h']:+.1f}%",         "inline": True},
            {"name": "💵 Price",          "value": f"${opp['current_price']:.8f}",             "inline": True},
            {
                "name": "🔢 Breakdown",
                "value": (
                    f"trend `{opp['trend_momentum']:.2f}` · "
                    f"market `{opp['market_quality']:.2f}` · "
                    f"smart money `{opp['smart_money_score']:.2f}`"
                ),
                "inline": False,
            },
        ],
        "footer": {"text": "CryptoScout · trend-driven opportunity detection"},
    }


def send_alerts(opportunities: list[dict]) -> None:
    """Send BUY and WATCH opportunities to Discord. Silently skips if no webhook set."""
    if not config.DISCORD_WEBHOOK_URL:
        logger.info("discord: no webhook URL set, skipping notifications")
        return

    actionable = [o for o in opportunities if o["verdict"] in ("BUY", "WATCH")]
    if not actionable:
        logger.info("discord: no BUY/WATCH opportunities to send")
        return

    # Discord allows max 10 embeds per message; split if needed
    chunk_size = 10
    for i in range(0, len(actionable), chunk_size):
        chunk = actionable[i : i + chunk_size]
        payload = {
            "username": "CryptoScout",
            "embeds": [_build_embed(o) for o in chunk],
        }
        try:
            r = requests.post(
                config.DISCORD_WEBHOOK_URL,
                json=payload,
                timeout=10,
            )
            if r.status_code in (200, 204):
                logger.info(f"discord: sent {len(chunk)} alerts")
            else:
                logger.error(f"discord: webhook returned {r.status_code}: {r.text}")
        except requests.RequestException as e:
            logger.error("discord: failed to send alert", error=str(e))
