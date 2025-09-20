from __future__ import annotations

import uuid as _uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import String, Integer, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class Draft(Base):
    """
    Structured player selection process

    Implements T018 requirements:
    - Draft entity for structured player selection
    - Add current_pick tracking and picks JSON array
    - Include timer and status management
    """
    __tablename__ = "drafts"

    # Primary identification
    draft_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4
    )
    league_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leagues.league_id"),
        nullable=False,
        unique=True  # One draft per league
    )

    # Draft configuration
    draft_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="scheduled")
    pick_timer: Mapped[int] = mapped_column(Integer, nullable=False, default=60)

    # Draft progress tracking
    current_pick: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    current_team_id: Mapped[Optional[_uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.team_id"),
        nullable=True
    )

    # Draft history (JSON array of completed picks)
    picks: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True, default=list)

    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Validation constraints
    __table_args__ = (
        # Draft type validation
        CheckConstraint(
            "draft_type IN ('snake', 'auction', 'linear')",
            name="valid_draft_type"
        ),
        # Status validation
        CheckConstraint(
            "status IN ('scheduled', 'active', 'paused', 'completed')",
            name="valid_draft_status"
        ),
        # Pick timer validation (30-300 seconds)
        CheckConstraint(
            "pick_timer >= 30 AND pick_timer <= 300",
            name="valid_pick_timer"
        ),
        # Current pick must be positive
        CheckConstraint(
            "current_pick > 0",
            name="positive_current_pick"
        ),
        # Common query indexes
        Index('idx_draft_league_id', 'league_id'),
        Index('idx_draft_status', 'status'),
        Index('idx_draft_current_team', 'current_team_id'),
    )

    def __repr__(self) -> str:
        return f"<Draft(league_id='{self.league_id}', type='{self.draft_type}', status='{self.status}')>"