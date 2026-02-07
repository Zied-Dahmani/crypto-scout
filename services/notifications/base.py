"""Base class for notification services."""

from abc import ABC, abstractmethod

from models.recommendation import Recommendation


class BaseNotificationService(ABC):
    """Abstract base class for notification services."""

    @abstractmethod
    async def send_recommendation(self, recommendation: Recommendation) -> bool:
        """
        Send a single recommendation notification.

        Args:
            recommendation: The recommendation to send

        Returns:
            True if sent successfully, False otherwise
        """
        pass

    @abstractmethod
    async def send_batch(self, recommendations: list[Recommendation]) -> int:
        """
        Send multiple recommendations.

        Args:
            recommendations: List of recommendations to send

        Returns:
            Number of successfully sent notifications
        """
        pass

    @abstractmethod
    async def send_alert(self, message: str) -> bool:
        """
        Send a generic alert message.

        Args:
            message: Alert message text

        Returns:
            True if sent successfully, False otherwise
        """
        pass

    def is_configured(self) -> bool:
        """Check if the notification service is properly configured."""
        return True

    async def health_check(self) -> bool:
        """Check if the notification service is operational."""
        return True
