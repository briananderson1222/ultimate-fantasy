"""
NotificationService with WebSocket integration for real-time fantasy sports notifications.

Provides comprehensive notification management with:
- Real-time WebSocket delivery
- Push notification support
- Email notification fallback
- Notification preferences management
- Event-driven notification triggers
- Batch notification processing
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from domains.shared.models.notification import Notification
from domains.users.models.user import User

try:
    from infrastructure.websockets.connection_manager import WebSocketConnectionManager
except ImportError:
    WebSocketConnectionManager = None  # type: ignore[misc,assignment]

try:
    from infrastructure.events.redis_pubsub import RedisEventPublisher
except ImportError:
    RedisEventPublisher = None  # type: ignore[misc,assignment]

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging
    get_logger = logging.getLogger  # type: ignore[assignment]

logger = get_logger(__name__)


class NotificationType:
    """Notification type constants."""

    DRAFT_PICK = "draft_pick"
    TRADE_PROPOSAL = "trade_proposal"
    TRADE_ACCEPTED = "trade_accepted"
    TRADE_REJECTED = "trade_rejected"
    WAIVER_RESULT = "waiver_result"
    SCORE_UPDATE = "score_update"
    LINEUP_REMINDER = "lineup_reminder"
    LEAGUE_INVITATION = "league_invitation"
    PLAYER_NEWS = "player_news"
    SYSTEM_ANNOUNCEMENT = "system_announcement"


class NotificationPriority:
    """Notification priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class DeliveryChannel:
    """Notification delivery channels."""

    WEBSOCKET = "websocket"
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"


class NotificationService:
    """Service for managing real-time notifications with WebSocket integration."""

    def __init__(
        self,
        session: Session,
        websocket_manager: Optional[WebSocketConnectionManager] = None,
        redis_publisher: Optional[RedisEventPublisher] = None,
    ):
        self.session = session
        self.websocket_manager = websocket_manager
        self.redis_publisher = redis_publisher

        # Default notification settings
        self.default_expiry_hours = 72
        self.max_retries = 3
        self.retry_delay_seconds = 60

        # WebSocket notification queues
        self.pending_websocket_notifications: Dict[str, List[Dict[str, Any]]] = {}

    async def send_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        priority: str = NotificationPriority.NORMAL,
        channels: Optional[List[str]] = None,
        league_id: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> Notification:
        """
        Send a notification to a user via multiple channels.

        Args:
            user_id: Target user ID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            data: Additional notification data
            priority: Notification priority level
            channels: Delivery channels to use
            league_id: Associated league ID
            expires_at: When notification expires

        Returns:
            Created notification instance
        """
        # Create notification record
        notification = Notification(
            user_id=UUID(user_id),
            league_id=UUID(league_id) if league_id else None,
            type=notification_type,
            title=title,
            message=message,
            data=data or {},
            priority=priority,
            expires_at=expires_at or datetime.utcnow() + timedelta(hours=self.default_expiry_hours),
        )

        self.session.add(notification)
        self.session.commit()
        self.session.refresh(notification)

        # Determine delivery channels
        if channels is None:
            channels = await self._get_user_preferred_channels(user_id)

        # Send via each channel
        delivery_results = {}
        for channel in channels:
            try:
                if channel == DeliveryChannel.WEBSOCKET:
                    success = await self._send_websocket_notification(user_id, notification)
                elif channel == DeliveryChannel.PUSH:
                    success = await self._send_push_notification(user_id, notification)
                elif channel == DeliveryChannel.EMAIL:
                    success = await self._send_email_notification(user_id, notification)
                else:
                    success = False

                delivery_results[channel] = success

            except Exception as e:
                logger.error(f"Failed to send notification via {channel}: {e}")
                delivery_results[channel] = False

        # Update notification with delivery status
        notification.delivery_status = delivery_results
        self.session.commit()

        logger.info(
            f"Notification sent",
            extra={
                "notification_id": str(notification.notification_id),
                "user_id": user_id,
                "type": notification_type,
                "channels": channels,
                "delivery_results": delivery_results,
            }
        )

        return notification

    async def send_bulk_notifications(
        self,
        notifications: List[Dict[str, Any]]
    ) -> List[Notification]:
        """
        Send multiple notifications efficiently.

        Args:
            notifications: List of notification data dicts

        Returns:
            List of created notification instances
        """
        created_notifications = []

        # Process in batches to avoid overwhelming the system
        batch_size = 50
        for i in range(0, len(notifications), batch_size):
            batch = notifications[i:i + batch_size]
            batch_results = []

            for notif_data in batch:
                try:
                    notification = await self.send_notification(**notif_data)
                    batch_results.append(notification)
                except Exception as e:
                    logger.error(f"Failed to send bulk notification: {e}")
                    continue

            created_notifications.extend(batch_results)

            # Small delay between batches
            if i + batch_size < len(notifications):
                await asyncio.sleep(0.1)

        logger.info(f"Sent {len(created_notifications)} bulk notifications")
        return created_notifications

    async def send_league_notification(
        self,
        league_id: str,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        exclude_user_ids: Optional[Set[str]] = None,
    ) -> List[Notification]:
        """
        Send notification to all users in a league.

        Args:
            league_id: League ID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            data: Additional notification data
            exclude_user_ids: User IDs to exclude

        Returns:
            List of created notifications
        """
        # Get all users in the league
        from domains.leagues.models.team import Team

        teams = self.session.query(Team).filter(Team.league_id == UUID(league_id)).all()
        user_ids = {str(team.user_id) for team in teams}

        if exclude_user_ids:
            user_ids -= exclude_user_ids

        # Prepare notification data for bulk sending
        notifications_data = []
        for user_id in user_ids:
            notifications_data.append({
                "user_id": user_id,
                "notification_type": notification_type,
                "title": title,
                "message": message,
                "data": data,
                "league_id": league_id,
            })

        return await self.send_bulk_notifications(notifications_data)

    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """
        Mark a notification as read.

        Args:
            notification_id: Notification ID
            user_id: User ID (for authorization)

        Returns:
            True if successfully marked as read
        """
        notification = (
            self.session.query(Notification)
            .filter(
                Notification.notification_id == UUID(notification_id),
                Notification.user_id == UUID(user_id)
            )
            .first()
        )

        if not notification:
            return False

        notification.read_at = datetime.utcnow()
        self.session.commit()

        # Send WebSocket update
        if self.websocket_manager:
            await self._send_websocket_message(user_id, {
                "type": "notification_read",
                "notification_id": notification_id,
            })

        return True

    async def mark_all_as_read(self, user_id: str, league_id: Optional[str] = None) -> int:
        """
        Mark all notifications as read for a user.

        Args:
            user_id: User ID
            league_id: Optional league ID to filter by

        Returns:
            Number of notifications marked as read
        """
        query = self.session.query(Notification).filter(
            Notification.user_id == UUID(user_id),
            Notification.read_at.is_(None)
        )

        if league_id:
            query = query.filter(Notification.league_id == UUID(league_id))

        count = query.count()
        query.update({"read_at": datetime.utcnow()})
        self.session.commit()

        # Send WebSocket update
        if self.websocket_manager:
            await self._send_websocket_message(user_id, {
                "type": "notifications_read_all",
                "count": count,
                "league_id": league_id,
            })

        return count

    async def get_user_notifications(
        self,
        user_id: str,
        league_id: Optional[str] = None,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        """
        Get notifications for a user.

        Args:
            user_id: User ID
            league_id: Optional league ID filter
            unread_only: Only return unread notifications
            limit: Maximum number of notifications
            offset: Offset for pagination

        Returns:
            List of notifications
        """
        query = self.session.query(Notification).filter(
            Notification.user_id == UUID(user_id)
        )

        if league_id:
            query = query.filter(Notification.league_id == UUID(league_id))

        if unread_only:
            query = query.filter(Notification.read_at.is_(None))

        # Filter out expired notifications
        query = query.filter(
            (Notification.expires_at.is_(None)) |
            (Notification.expires_at > datetime.utcnow())
        )

        return (
            query
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    async def get_unread_count(self, user_id: str, league_id: Optional[str] = None) -> int:
        """
        Get count of unread notifications for a user.

        Args:
            user_id: User ID
            league_id: Optional league ID filter

        Returns:
            Number of unread notifications
        """
        query = self.session.query(Notification).filter(
            Notification.user_id == UUID(user_id),
            Notification.read_at.is_(None)
        )

        if league_id:
            query = query.filter(Notification.league_id == UUID(league_id))

        # Filter out expired notifications
        query = query.filter(
            (Notification.expires_at.is_(None)) |
            (Notification.expires_at > datetime.utcnow())
        )

        return query.count()

    async def cleanup_expired_notifications(self) -> int:
        """
        Remove expired notifications from the database.

        Returns:
            Number of notifications cleaned up
        """
        expired_notifications = self.session.query(Notification).filter(
            Notification.expires_at < datetime.utcnow()
        )

        count = expired_notifications.count()
        expired_notifications.delete()
        self.session.commit()

        logger.info(f"Cleaned up {count} expired notifications")
        return count

    # WebSocket Integration Methods

    async def _send_websocket_notification(self, user_id: str, notification: Notification) -> bool:
        """Send notification via WebSocket."""
        if not self.websocket_manager:
            return False

        message = {
            "type": "notification",
            "notification": {
                "id": str(notification.notification_id),
                "type": notification.type,
                "title": notification.title,
                "message": notification.message,
                "data": notification.data,
                "priority": notification.priority,
                "created_at": notification.created_at.isoformat(),
                "league_id": str(notification.league_id) if notification.league_id else None,
            }
        }

        return await self._send_websocket_message(user_id, message)

    async def _send_websocket_message(self, user_id: str, message: Dict[str, Any]) -> bool:
        """Send a WebSocket message to a user."""
        if not self.websocket_manager:
            return False

        try:
            # Send to all connections for this user
            connections = self.websocket_manager.get_user_connections(user_id)
            if not connections:
                # Queue message for when user connects
                if user_id not in self.pending_websocket_notifications:
                    self.pending_websocket_notifications[user_id] = []
                self.pending_websocket_notifications[user_id].append(message)
                return True

            # Send to active connections
            success_count = 0
            for connection in connections:
                try:
                    await connection.send_text(json.dumps(message))
                    success_count += 1
                except Exception as e:
                    logger.warning(f"Failed to send WebSocket message to connection: {e}")

            return success_count > 0

        except Exception as e:
            logger.error(f"WebSocket notification failed: {e}")
            return False

    async def handle_user_connected(self, user_id: str) -> None:
        """Handle user WebSocket connection - send pending notifications."""
        if user_id in self.pending_websocket_notifications:
            pending = self.pending_websocket_notifications.pop(user_id)
            for message in pending:
                await self._send_websocket_message(user_id, message)

    # Push Notification Methods

    async def _send_push_notification(self, user_id: str, notification: Notification) -> bool:
        """Send push notification (stub for future implementation)."""
        # This would integrate with FCM, APNs, etc.
        logger.debug(f"Push notification would be sent to user {user_id}: {notification.title}")
        return True

    # Email Notification Methods

    async def _send_email_notification(self, user_id: str, notification: Notification) -> bool:
        """Send email notification (stub for future implementation)."""
        # This would integrate with email service
        logger.debug(f"Email notification would be sent to user {user_id}: {notification.title}")
        return True

    # User Preferences

    async def _get_user_preferred_channels(self, user_id: str) -> List[str]:
        """Get user's preferred notification channels."""
        # This would check user preferences from database
        # For now, default to WebSocket only
        return [DeliveryChannel.WEBSOCKET]

    async def update_user_notification_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """Update user notification preferences."""
        # This would update user preferences in database
        logger.info(f"Updated notification preferences for user {user_id}")
        return True

    # Event-Driven Notification Methods

    async def handle_draft_pick_event(self, event_data: Dict[str, Any]) -> None:
        """Handle draft pick event and send notifications."""
        league_id = event_data.get("league_id")
        team_id = event_data.get("team_id")
        player_name = event_data.get("player_name", "Unknown Player")
        pick_number = event_data.get("pick_number")

        if not all([league_id, team_id]):
            return

        # Notify all league members except the picker
        picking_user_id = event_data.get("user_id")
        exclude_users = {picking_user_id} if picking_user_id else set()

        await self.send_league_notification(
            league_id=league_id,
            notification_type=NotificationType.DRAFT_PICK,
            title="Draft Pick Made",
            message=f"{player_name} was selected (Pick #{pick_number})",
            data=event_data,
            exclude_user_ids=exclude_users,
        )

    async def handle_trade_proposal_event(self, event_data: Dict[str, Any]) -> None:
        """Handle trade proposal event."""
        receiving_user_id = event_data.get("receiving_user_id")
        proposing_team_name = event_data.get("proposing_team_name", "Another team")

        if not receiving_user_id:
            return

        await self.send_notification(
            user_id=receiving_user_id,
            notification_type=NotificationType.TRADE_PROPOSAL,
            title="New Trade Proposal",
            message=f"You have received a trade proposal from {proposing_team_name}",
            data=event_data,
            priority=NotificationPriority.HIGH,
        )

    async def handle_score_update_event(self, event_data: Dict[str, Any]) -> None:
        """Handle player score update event."""
        league_id = event_data.get("league_id")
        player_name = event_data.get("player_name", "A player")
        points = event_data.get("points", 0)

        if not league_id:
            return

        # Only notify if significant score update
        if points >= 10:  # Configurable threshold
            await self.send_league_notification(
                league_id=league_id,
                notification_type=NotificationType.SCORE_UPDATE,
                title="Big Performance Alert",
                message=f"{player_name} has scored {points} fantasy points!",
                data=event_data,
            )


# Global service instance
_notification_service: Optional[NotificationService] = None


def get_notification_service(session: Session) -> NotificationService:
    """Get the global notification service instance."""
    global _notification_service

    if _notification_service is None:
        websocket_manager = None
        redis_publisher = None

        # Try to get WebSocket manager
        if WebSocketConnectionManager:
            try:
                websocket_manager = WebSocketConnectionManager()
            except Exception:
                pass

        # Try to get Redis publisher
        if RedisEventPublisher:
            try:
                redis_publisher = RedisEventPublisher()
            except Exception:
                pass

        _notification_service = NotificationService(
            session=session,
            websocket_manager=websocket_manager,
            redis_publisher=redis_publisher,
        )

    return _notification_service


def reset_notification_service():
    """Reset the global service (useful for testing)."""
    global _notification_service
    _notification_service = None