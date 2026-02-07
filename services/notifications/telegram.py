"""Telegram notification service implementation."""

import asyncio
from typing import Optional

from telegram import Bot
from telegram.error import TelegramError

from config.settings import config
from models.recommendation import Recommendation
from utils.logger import get_logger
from .base import BaseNotificationService

logger = get_logger(__name__)


class TelegramNotificationService(BaseNotificationService):
    """Telegram bot notification service."""

    def __init__(self):
        self.config = config.telegram
        self.bot: Optional[Bot] = None
        self._init_bot()

    def _init_bot(self) -> None:
        """Initialize the Telegram bot."""
        if not self.is_configured():
            logger.warning("Telegram bot not configured")
            return

        try:
            self.bot = Bot(token=self.config.bot_token)
            logger.info("Telegram bot initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Telegram bot", error=str(e))
            self.bot = None

    def is_configured(self) -> bool:
        """Check if Telegram is configured."""
        return bool(self.config.bot_token and self.config.chat_id)

    async def send_recommendation(self, recommendation: Recommendation) -> bool:
        """Send a recommendation via Telegram."""
        if not self.bot:
            logger.warning("Telegram bot not available")
            return False

        try:
            message = recommendation.to_notification_message()

            await self.bot.send_message(
                chat_id=self.config.chat_id,
                text=message,
                parse_mode="Markdown",
            )

            logger.info(
                "Telegram notification sent",
                recommendation_id=recommendation.id,
                crypto=recommendation.match.crypto.symbol
            )
            return True

        except TelegramError as e:
            logger.error("Telegram send failed", error=str(e))
            return False
        except Exception as e:
            logger.error("Unexpected error sending Telegram message", error=str(e))
            return False

    async def send_batch(self, recommendations: list[Recommendation]) -> int:
        """Send multiple recommendations with rate limiting."""
        if not self.bot:
            return 0

        sent_count = 0

        for recommendation in recommendations:
            success = await self.send_recommendation(recommendation)
            if success:
                sent_count += 1

            # Rate limiting: Telegram allows ~30 messages per second
            await asyncio.sleep(0.5)

        logger.info(f"Sent {sent_count}/{len(recommendations)} Telegram notifications")
        return sent_count

    async def send_alert(self, message: str) -> bool:
        """Send a generic alert via Telegram."""
        if not self.bot:
            logger.warning("Telegram bot not available")
            return False

        try:
            await self.bot.send_message(
                chat_id=self.config.chat_id,
                text=f"⚠️ *CRYPTO SCOUT ALERT*\n\n{message}",
                parse_mode="Markdown",
            )
            return True

        except TelegramError as e:
            logger.error("Telegram alert failed", error=str(e))
            return False

    async def health_check(self) -> bool:
        """Check Telegram bot connectivity."""
        if not self.bot:
            return False

        try:
            await self.bot.get_me()
            return True
        except Exception:
            return False
