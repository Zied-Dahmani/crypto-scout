"""Discord webhook notifications."""

import time

import requests

import config
from utils.logger import get_logger

logger = get_logger(__name__)

_COLOR = {"BUY": 0x00C851, "WATCH": 0xFFBB33, "SKIP": 0xFF4444}


def _truncate_address(addr: str) -> str:
    if not addr or len(addr) < 12:
        return addr or "unknown"
    return f"{addr[:6]}...{addr[-4:]}"


def _age_label(pair_created_at: int) -> str:
    """Return human-readable age string from ms epoch timestamp."""
    if not pair_created_at:
        return "unknown"
    elapsed_s = time.time() - pair_created_at / 1000
    if elapsed_s < 3600:
        return f"{int(elapsed_s // 60)}m"
    if elapsed_s < 86400:
        return f"{int(elapsed_s // 3600)}h"
    return f"{int(elapsed_s // 86400)}d"


def _age_emoji(pair_created_at: int) -> str:
    if not pair_created_at:
        return "⚪"
    elapsed_s = time.time() - pair_created_at / 1000
    if elapsed_s < 3600:
        return "🟢"
    if elapsed_s < 86400:
        return "🟡"
    return "⚪"


def _dexscreener_url(opp: dict) -> str:
    contract = opp.get("contract_address", "")
    chain = opp.get("blockchain", "")
    if not contract:
        return "https://dexscreener.com"
    if chain == "solana":
        return f"https://dexscreener.com/solana/{contract}"
    return f"https://dexscreener.com/{chain}/{contract}"


def _build_embed(opp: dict) -> dict:
    verdict = opp["verdict"]
    icon = {"BUY": "🟢", "WATCH": "🟡", "SKIP": "🔴"}.get(verdict, "")

    contract = opp.get("contract_address", "")
    age = _age_label(opp.get("pair_created_at", 0))
    age_emoji = _age_emoji(opp.get("pair_created_at", 0))
    chart_url = _dexscreener_url(opp)

    # Contract address line (truncated, copyable in description)
    desc_parts = []
    if contract:
        desc_parts.append(f"`{_truncate_address(contract)}`")
        desc_parts.append(f"[📋 Copy]({chart_url}) · [📊 Chart]({chart_url})")
    description = "  ".join(desc_parts) if desc_parts else ""

    return {
        "title": f"{icon} {verdict} — {opp['symbol']}  ({opp['name']})",
        "description": description,
        "color": _COLOR.get(verdict, 0x888888),
        "fields": [
            {
                "name": "📈 Trend",
                "value": opp["trend_keyword"],
                "inline": True,
            },
            {
                "name": "⚡ Score",
                "value": f"{opp['score']:.3f}",
                "inline": True,
            },
            {
                "name": f"{age_emoji} Age",
                "value": age,
                "inline": True,
            },
            {
                "name": "💰 Market Cap",
                "value": f"[${opp['market_cap']:,.0f}]({chart_url})",
                "inline": True,
            },
            {
                "name": "📊 Volume 24h",
                "value": f"${opp['volume_24h']:,.0f}",
                "inline": True,
            },
            {
                "name": "🕯️ Price Change",
                "value": f"{opp['price_change_24h']:+.1f}%",
                "inline": True,
            },
            {
                "name": "💵 Price",
                "value": f"${opp['current_price']:.8f}",
                "inline": True,
            },
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
    """Send BUY and WATCH opportunities to Discord."""
    if not config.DISCORD_WEBHOOK_URL:
        logger.info("discord: no webhook URL set, skipping notifications")
        return

    actionable = [o for o in opportunities if o["verdict"] in ("BUY", "WATCH")]
    if not actionable:
        logger.info("discord: no BUY/WATCH opportunities to send")
        return

    for i in range(0, len(actionable), 10):
        chunk = actionable[i: i + 10]
        payload = {
            "username": "CryptoScout",
            "embeds": [_build_embed(o) for o in chunk],
        }
        try:
            r = requests.post(config.DISCORD_WEBHOOK_URL, json=payload, timeout=10)
            if r.status_code in (200, 204):
                logger.info(f"discord: sent {len(chunk)} alerts")
            else:
                logger.error(f"discord: webhook returned {r.status_code}: {r.text}")
        except requests.RequestException as e:
            logger.error("discord: failed to send alert", error=str(e))
