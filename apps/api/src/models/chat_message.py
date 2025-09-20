from __future__ import annotations

import uuid as _uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class ChatMessage(Base):
    """
    League chat and communication system

    Implements T023 requirements:
    - ChatMessage entity for league communication
    - Add message_data JSON for rich content and attachments
    - Include moderation and thread support
    """
    __tablename__ = "chat_messages"

    # Primary identification
    message_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4
    )
    league_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leagues.league_id"),
        nullable=False
    )
    user_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False
    )

    # Message content
    message_text: Mapped[str] = mapped_column(String(2000), nullable=False)
    message_type: Mapped[str] = mapped_column(String(20), nullable=False, default="text")

    # Rich content and attachments (JSON object)
    message_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, default=dict)

    # Threading and conversation
    parent_message_id: Mapped[Optional[_uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_messages.message_id"),
        nullable=True
    )
    thread_depth: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Message status and moderation
    is_edited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_system_message: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Moderation
    is_flagged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    flag_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    moderated_by: Mapped[Optional[_uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=True
    )

    # Timestamps
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Validation constraints
    __table_args__ = (
        # Message type validation
        CheckConstraint(
            "message_type IN ('text', 'trade_proposal', 'draft_pick', 'system_alert', 'image', 'link')",
            name="valid_message_type"
        ),
        # Thread depth must be non-negative and reasonable
        CheckConstraint(
            "thread_depth >= 0 AND thread_depth <= 10",
            name="valid_thread_depth"
        ),
        # System messages should not have parent messages
        CheckConstraint(
            "NOT (is_system_message = true AND parent_message_id IS NOT NULL)",
            name="system_message_no_parent"
        ),
        # Common query indexes
        Index('idx_chat_league_id', 'league_id'),
        Index('idx_chat_user_id', 'user_id'),
        Index('idx_chat_parent_message', 'parent_message_id'),
        Index('idx_chat_created_at', 'created_at'),
        Index('idx_chat_is_deleted', 'is_deleted'),
        Index('idx_chat_is_pinned', 'is_pinned'),
        Index('idx_chat_is_flagged', 'is_flagged'),
        Index('idx_chat_message_type', 'message_type'),
        # Composite index for league chat feed
        Index('idx_league_chat_feed', 'league_id', 'is_deleted', 'created_at'),
        # Index for threaded conversations
        Index('idx_thread_conversation', 'parent_message_id', 'thread_depth', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<ChatMessage(league_id='{self.league_id}', user_id='{self.user_id}', type='{self.message_type}')>"

    def mark_as_edited(self) -> None:
        """Mark message as edited"""
        self.is_edited = True
        self.edited_at = datetime.utcnow()

    def soft_delete(self) -> None:
        """Soft delete the message"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def flag_message(self, reason: str, moderated_by_user_id: _uuid.UUID) -> None:
        """Flag message for moderation"""
        self.is_flagged = True
        self.flag_reason = reason
        self.moderated_by = moderated_by_user_id

    def unflag_message(self) -> None:
        """Remove flag from message"""
        self.is_flagged = False
        self.flag_reason = None
        self.moderated_by = None

    def pin_message(self) -> None:
        """Pin message to top of chat"""
        self.is_pinned = True

    def unpin_message(self) -> None:
        """Unpin message"""
        self.is_pinned = False

    def get_data_value(self, key: str, default: Any = None) -> Any:
        """Get specific data value from message_data"""
        if not self.message_data:
            return default
        return self.message_data.get(key, default)

    def set_data_value(self, key: str, value: Any) -> None:
        """Set specific data value in message_data"""
        if self.message_data is None:
            self.message_data = {}
        self.message_data[key] = value

    def update_data(self, new_data: Dict[str, Any]) -> None:
        """Update multiple data values at once"""
        if self.message_data is None:
            self.message_data = {}
        self.message_data.update(new_data)

    def is_reply(self) -> bool:
        """Check if message is a reply to another message"""
        return self.parent_message_id is not None

    def is_thread_starter(self) -> bool:
        """Check if message is the start of a thread"""
        return self.parent_message_id is None and self.thread_depth == 0

    def can_be_edited(self, user_id: _uuid.UUID, time_limit_minutes: int = 15) -> bool:
        """Check if message can be edited by user within time limit"""
        if self.user_id != user_id:
            return False
        if self.is_deleted or self.is_system_message:
            return False

        # Check time limit
        time_since_created = datetime.utcnow() - self.created_at.replace(tzinfo=None)
        return time_since_created.total_seconds() < (time_limit_minutes * 60)

    def get_display_data(self, include_deleted: bool = False) -> Dict[str, Any]:
        """Get message data for display"""
        if self.is_deleted and not include_deleted:
            return {
                "id": str(self.message_id),
                "is_deleted": True,
                "message_text": "[Message deleted]",
                "created_at": self.created_at.isoformat(),
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None
            }

        return {
            "id": str(self.message_id),
            "league_id": str(self.league_id),
            "user_id": str(self.user_id),
            "message_text": self.message_text,
            "message_type": self.message_type,
            "message_data": self.message_data,
            "parent_message_id": str(self.parent_message_id) if self.parent_message_id else None,
            "thread_depth": self.thread_depth,
            "is_edited": self.is_edited,
            "is_pinned": self.is_pinned,
            "is_system_message": self.is_system_message,
            "is_flagged": self.is_flagged,
            "created_at": self.created_at.isoformat(),
            "edited_at": self.edited_at.isoformat() if self.edited_at else None
        }

    @classmethod
    def create_system_message(
        cls,
        league_id: _uuid.UUID,
        message_text: str,
        message_type: str = "system_alert",
        message_data: Optional[Dict[str, Any]] = None
    ) -> "ChatMessage":
        """Factory method for system messages"""
        return cls(
            league_id=league_id,
            user_id=_uuid.uuid4(),  # System user ID placeholder
            message_text=message_text,
            message_type=message_type,
            message_data=message_data or {},
            is_system_message=True
        )

    @classmethod
    def create_trade_announcement(
        cls,
        league_id: _uuid.UUID,
        trade_summary: str,
        trade_data: Dict[str, Any]
    ) -> "ChatMessage":
        """Factory method for trade announcements"""
        return cls.create_system_message(
            league_id=league_id,
            message_text=trade_summary,
            message_type="trade_proposal",
            message_data=trade_data
        )

    @classmethod
    def create_draft_pick_announcement(
        cls,
        league_id: _uuid.UUID,
        pick_summary: str,
        pick_data: Dict[str, Any]
    ) -> "ChatMessage":
        """Factory method for draft pick announcements"""
        return cls.create_system_message(
            league_id=league_id,
            message_text=pick_summary,
            message_type="draft_pick",
            message_data=pick_data
        )