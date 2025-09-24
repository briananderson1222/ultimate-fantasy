from __future__ import annotations

import uuid as _uuid
from datetime import datetime
from typing import Any
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression, func

from domains.shared.models.base import Base


class DraftStatus(Enum):
    """Draft status enumeration."""
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class Draft(Base):
    __tablename__ = "drafts"

    draft_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4
    )
    league_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leagues.league_id"), nullable=False, unique=True
    )

    draft_type: Mapped[str] = mapped_column(String(20), nullable=False, default="snake")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="scheduled")
    pick_timer: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    rounds: Mapped[int] = mapped_column(Integer, nullable=False, default=16)
    pick_time_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=120)
    auto_draft_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=expression.true()
    )

    current_pick: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    current_round: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    current_team_id: Mapped[_uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.team_id"), nullable=True
    )

    draft_order: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True, default=list
    )
    picks: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON, nullable=True, default=list
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "draft_type IN ('snake', 'auction', 'linear')", name="valid_draft_type"
        ),
        CheckConstraint(
            "status IN ('scheduled', 'active', 'paused', 'completed')",
            name="valid_draft_status",
        ),
        CheckConstraint("pick_timer BETWEEN 30 AND 300", name="valid_pick_timer"),
        CheckConstraint(
            "pick_time_limit BETWEEN 30 AND 600", name="valid_pick_time_limit"
        ),
        CheckConstraint("current_pick >= 0", name="non_negative_current_pick"),
        CheckConstraint("current_round > 0", name="positive_current_round"),
        Index("idx_draft_league_id", "league_id"),
        Index("idx_draft_status", "status"),
        Index("idx_draft_current_team", "current_team_id"),
    )

    def __repr__(self) -> str:  # pragma: no cover - repr helper
        return f"<Draft(league_id='{self.league_id}', type='{self.draft_type}', status='{self.status}')>"
