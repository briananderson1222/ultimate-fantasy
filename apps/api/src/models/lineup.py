from __future__ import annotations

import uuid as _uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from sqlalchemy import String, Integer, Float, DateTime, Date, Boolean, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class Lineup(Base):
    """
    Daily/weekly player selections for scoring

    Implements T017 requirements:
    - Lineup entity for daily/weekly player selections
    - Add players JSON array with position validation
    - Include optimistic locking with version field
    """
    __tablename__ = "lineups"

    # Primary identification
    lineup_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4
    )
    team_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.team_id"),
        nullable=False
    )

    # Scoring period identification
    week: Mapped[int] = mapped_column(Integer, nullable=False)
    game_day: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Player selections (JSON array of {player_id, position})
    players: Mapped[Optional[List[Dict[str, str]]]] = mapped_column(JSON, nullable=True, default=list)

    # Scoring and status
    points_scored: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Optimistic locking
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Validation constraints
    __table_args__ = (
        # Unique lineup per team per week/day
        Index('idx_unique_lineup_per_team_week', 'team_id', 'week', 'game_day', unique=True),
        # Week must be positive
        CheckConstraint(
            "week > 0",
            name="positive_week"
        ),
        # Points must be non-negative
        CheckConstraint(
            "points_scored >= 0",
            name="non_negative_points"
        ),
        # Version must be positive
        CheckConstraint(
            "version > 0",
            name="positive_version"
        ),
        # Common query indexes
        Index('idx_lineup_team_id', 'team_id'),
        Index('idx_lineup_week', 'week'),
        Index('idx_lineup_game_day', 'game_day'),
        Index('idx_lineup_locked', 'is_locked'),
    )

    def __repr__(self) -> str:
        return f"<Lineup(team_id='{self.team_id}', week={self.week}, points={self.points_scored})>"