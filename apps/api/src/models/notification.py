from __future__ import annotations

import uuid as _uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import String, DateTime, Boolean, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class Notification(Base):
    """
    User notifications for league events and system updates

    Implements T022 requirements:
    - Notification entity for user alerts and messages
    - Add notification_data JSON with event context
    - Include delivery tracking and user preferences
    """
    __tablename__ = "notifications"

    # Primary identification
    notification_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4
    )
    user_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False
    )

    # Notification context
    league_id: Mapped[Optional[_uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leagues.league_id"),
        nullable=True
    )
    team_id: Mapped[Optional[_uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.team_id"),
        nullable=True
    )

    # Notification content
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    action_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Event data and context (JSON object)
    notification_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, default=dict)

    # Delivery and status
    priority: Mapped[str] = mapped_column(String(10), nullable=False, default="normal")
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_delivered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    delivery_method: Mapped[str] = mapped_column(String(20), nullable=False, default="in_app")

    # Delivery tracking
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Validation constraints
    __table_args__ = (
        # Notification type validation
        CheckConstraint(
            """notification_type IN (
                'trade_proposal', 'trade_accepted', 'trade_rejected', 'trade_vetoed',
                'waiver_claim_awarded', 'waiver_claim_rejected',
                'draft_pick_turn', 'draft_completed',
                'lineup_reminder', 'injury_alert',
                'league_invite', 'league_update',
                'system_announcement', 'maintenance_notice'
            )""",
            name="valid_notification_type"
        ),
        # Priority validation
        CheckConstraint(
            "priority IN ('low', 'normal', 'high', 'urgent')",
            name="valid_priority"
        ),
        # Delivery method validation
        CheckConstraint(
            "delivery_method IN ('in_app', 'email', 'push', 'sms')",
            name="valid_delivery_method"
        ),
        # Common query indexes
        Index('idx_notification_user_id', 'user_id'),
        Index('idx_notification_league_id', 'league_id'),
        Index('idx_notification_team_id', 'team_id'),
        Index('idx_notification_type', 'notification_type'),
        Index('idx_notification_priority', 'priority'),
        Index('idx_notification_is_read', 'is_read'),
        Index('idx_notification_is_delivered', 'is_delivered'),
        Index('idx_notification_created_at', 'created_at'),
        Index('idx_notification_expires_at', 'expires_at'),
        # Composite index for user's unread notifications
        Index('idx_user_unread_notifications', 'user_id', 'is_read', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<Notification(user_id='{self.user_id}', type='{self.notification_type}', title='{self.title[:30]}...')>"

    def mark_as_read(self) -> None:
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()

    def mark_as_delivered(self) -> None:
        """Mark notification as delivered"""
        if not self.is_delivered:
            self.is_delivered = True
            self.delivered_at = datetime.utcnow()

    def is_expired(self) -> bool:
        """Check if notification has expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def get_data_value(self, key: str, default: Any = None) -> Any:
        """Get specific data value from notification_data"""
        if not self.notification_data:
            return default
        return self.notification_data.get(key, default)

    def set_data_value(self, key: str, value: Any) -> None:
        """Set specific data value in notification_data"""
        if self.notification_data is None:
            self.notification_data = {}
        self.notification_data[key] = value

    def update_data(self, new_data: Dict[str, Any]) -> None:
        """Update multiple data values at once"""
        if self.notification_data is None:
            self.notification_data = {}
        self.notification_data.update(new_data)

    def get_priority_weight(self) -> int:
        """Get numeric weight for priority sorting"""
        priority_weights = {
            "low": 1,
            "normal": 2,
            "high": 3,
            "urgent": 4
        }
        return priority_weights.get(self.priority, 2)

    def should_send_push(self) -> bool:
        """Determine if notification should be sent as push notification"""
        high_priority_types = {
            "draft_pick_turn",
            "trade_proposal",
            "waiver_claim_awarded",
            "injury_alert",
            "system_announcement"
        }
        return (
            self.priority in ["high", "urgent"] or
            self.notification_type in high_priority_types
        )

    def get_display_summary(self) -> Dict[str, Any]:
        """Get notification summary for display"""
        return {
            "id": str(self.notification_id),
            "type": self.notification_type,
            "title": self.title,
            "message": self.message,
            "priority": self.priority,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
            "action_url": self.action_url,
            "league_id": str(self.league_id) if self.league_id else None,
            "team_id": str(self.team_id) if self.team_id else None
        }

    @classmethod
    def create_trade_notification(
        cls,
        user_id: str,
        league_id: str,
        team_id: str,
        trade_id: str,
        notification_type: str,
        other_team_name: str
    ) -> "Notification":
        """Factory method for trade-related notifications"""
        type_messages = {
            "trade_proposal": f"New trade proposal from {other_team_name}",
            "trade_accepted": f"Your trade with {other_team_name} was accepted",
            "trade_rejected": f"Your trade with {other_team_name} was rejected",
            "trade_vetoed": f"Your trade with {other_team_name} was vetoed by commissioner"
        }

        return cls(
            user_id=user_id,
            league_id=league_id,
            team_id=team_id,
            notification_type=notification_type,
            title="Trade Update",
            message=type_messages.get(notification_type, "Trade status updated"),
            action_url=f"/leagues/{league_id}/trades/{trade_id}",
            notification_data={"trade_id": trade_id, "other_team": other_team_name},
            priority="high" if notification_type == "trade_proposal" else "normal"
        )

    @classmethod
    def create_draft_notification(
        cls,
        user_id: str,
        league_id: str,
        team_id: str,
        pick_number: int,
        time_remaining: int
    ) -> "Notification":
        """Factory method for draft pick notifications"""
        return cls(
            user_id=user_id,
            league_id=league_id,
            team_id=team_id,
            notification_type="draft_pick_turn",
            title="Your Draft Pick",
            message=f"It's your turn to draft! Pick #{pick_number} - {time_remaining}s remaining",
            action_url=f"/leagues/{league_id}/draft",
            notification_data={"pick_number": pick_number, "time_remaining": time_remaining},
            priority="urgent"
        )
