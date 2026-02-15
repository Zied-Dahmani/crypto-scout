"""WhatsApp notification service implementation using Twilio."""

import asyncio
from typing import Optional

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from config.settings import config
from models.recommendation import Recommendation
from utils.logger import get_logger
from .base import BaseNotificationService

logger = get_logger(__name__)


class WhatsAppNotificationService(BaseNotificationService):
    """WhatsApp notification service via Twilio API."""

    def __init__(self):
        self.config = config.whatsapp
        self.client: Optional[Client] = None
        self._init_client()

    def _init_client(self) -> None:
        """Initialize the Twilio client."""
        if not self.is_configured():
            logger.warning("Twilio WhatsApp not configured")
            return

        try:
            self.client = Client(
                self.config.account_sid,
                self.config.auth_token
            )
            logger.info("Twilio WhatsApp client initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Twilio client", error=str(e))
            self.client = None

    def is_configured(self) -> bool:
        """Check if Twilio WhatsApp is configured with valid credentials."""
        # Check all required fields exist
        if not all([
            self.config.account_sid,
            self.config.auth_token,
            self.config.from_number,
            self.config.to_number
        ]):
            return False

        # Check for placeholder values
        placeholders = ['your_', 'YOUR_', 'placeholder', 'PLACEHOLDER', 'xxx', 'XXX']
        for field in [self.config.account_sid, self.config.auth_token]:
            if any(p in field for p in placeholders):
                return False

        return True

    async def send_recommendation(self, recommendation: Recommendation) -> bool:
        """Send a recommendation via WhatsApp."""
        if not self.client:
            logger.warning("Twilio client not available")
            return False

        try:
            # WhatsApp messages need to be plain text or use approved templates
            message = self._format_whatsapp_message(recommendation)

            # Run sync Twilio call in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._send_message_sync,
                message
            )

            if result:
                logger.info(
                    "WhatsApp notification sent",
                    recommendation_id=recommendation.id,
                    crypto=recommendation.match.crypto.symbol
                )
            return result

        except Exception as e:
            logger.error("Unexpected error sending WhatsApp message", error=str(e))
            return False

    def _send_message_sync(self, message: str) -> bool:
        """Synchronous message send for Twilio API."""
        try:
            self.client.messages.create(
                body=message,
                from_=f"whatsapp:{self.config.from_number}",
                to=f"whatsapp:{self.config.to_number}"
            )
            return True
        except TwilioRestException as e:
            logger.error("Twilio send failed", error=str(e))
            return False

    def _format_whatsapp_message(self, recommendation: Recommendation) -> str:
        """Format recommendation for WhatsApp (plain text, no markdown)."""
        trend = recommendation.match.trend
        crypto = recommendation.match.crypto

        # WhatsApp doesn't support full markdown, use plain text with emojis
        message = f"""
🚀 CRYPTO SCOUT ALERT

📈 Trending: {trend.keyword}
🔥 Virality: {trend.virality_score:.0%}
📊 Source: {trend.source.value.title()}

💰 Crypto: {crypto.name} ({crypto.symbol.upper()})
💵 Price: ${crypto.current_price_usd:.6f}
📊 Market Cap: ${crypto.market_cap_usd:,.0f}
📈 24h Change: {crypto.price_change_24h_pct:+.2f}%

🎯 Match: {recommendation.match.match_score:.0%}
🔮 Confidence: {recommendation.confidence_score:.0%}
⚠️ Risk: {recommendation.risk_level.upper()}
💡 Action: {recommendation.action.upper()}

📝 {recommendation.reasoning[:200]}...
        """.strip()

        return message

    async def send_batch(self, recommendations: list[Recommendation]) -> int:
        """Send multiple recommendations with rate limiting."""
        if not self.client:
            return 0

        sent_count = 0

        for recommendation in recommendations:
            success = await self.send_recommendation(recommendation)
            if success:
                sent_count += 1

            # Rate limiting: Twilio has strict rate limits
            await asyncio.sleep(1.0)

        logger.info(f"Sent {sent_count}/{len(recommendations)} WhatsApp notifications")
        return sent_count

    async def send_alert(self, message: str) -> bool:
        """Send a generic alert via WhatsApp."""
        if not self.client:
            logger.warning("Twilio client not available")
            return False

        try:
            alert_message = f"⚠️ CRYPTO SCOUT ALERT\n\n{message}"

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self._send_message_sync,
                alert_message
            )

        except Exception as e:
            logger.error("WhatsApp alert failed", error=str(e))
            return False

    async def health_check(self) -> bool:
        """Check Twilio connectivity."""
        if not self.client:
            return False

        try:
            # Try to fetch account info
            loop = asyncio.get_event_loop()
            account = await loop.run_in_executor(
                None,
                lambda: self.client.api.accounts(self.config.account_sid).fetch()
            )
            return account is not None
        except Exception:
            return False
