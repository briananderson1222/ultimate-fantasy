from __future__ import annotations

import uuid as _uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import String, DateTime, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class Player(Base):
    """
    Real sports athletes with comprehensive statistics and status

    Implements T014 requirements:
    - Player entity with fields: player_id, external_id, name, position, team_id, sport
    - Add injury_status, season_stats, game_stats, projections JSON fields
    - Include validation rules for position and injury status
    """
    __tablename__ = "players"

    # Primary identification
    player_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4
    )
    external_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    # Basic player info
    position: Mapped[str] = mapped_column(String(20), nullable=False)
    team_id: Mapped[str] = mapped_column(String(10), nullable=True)  # Current team (e.g., "LAA", "NYY")
    sport: Mapped[str] = mapped_column(String(10), nullable=False)

    # Injury and status information
    injury_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="healthy"
    )
    injury_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Statistics and projections (JSON fields)
    season_stats: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    game_stats: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    projections: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Validation constraints
    __table_args__ = (
        # Sport validation
        CheckConstraint(
            "sport IN ('mlb', 'nfl', 'wnba')",
            name="valid_sport"
        ),
        # Injury status validation
        CheckConstraint(
            "injury_status IN ('healthy', 'questionable', 'doubtful', 'out')",
            name="valid_injury_status"
        ),
        # Position validation for MLB
        CheckConstraint(
            """
            CASE
                WHEN sport = 'mlb' THEN position IN ('C', '1B', '2B', '3B', 'SS', 'OF', 'P', 'DH')
                WHEN sport = 'nfl' THEN position IN ('QB', 'RB', 'WR', 'TE', 'K', 'DEF')
                WHEN sport = 'wnba' THEN position IN ('PG', 'SG', 'SF', 'PF', 'C')
                ELSE TRUE
            END
            """,
            name="valid_position_for_sport"
        ),
        # Unique external_id per sport
        Index('idx_external_id_sport', 'external_id', 'sport', unique=True),
        # Index for common queries
        Index('idx_sport_position', 'sport', 'position'),
        Index('idx_team_sport', 'team_id', 'sport'),
        Index('idx_injury_status', 'injury_status'),
    )

    def __repr__(self) -> str:
        return f"<Player(name='{self.name}', sport='{self.sport}', position='{self.position}')>"
