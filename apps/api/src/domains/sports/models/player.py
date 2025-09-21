from __future__ import annotations

import uuid as _uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import CheckConstraint, DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from domains.shared.models.base import Base


class Player(Base):
    """Real sports athletes with comprehensive statistics and status."""

    __tablename__ = "players"

    player_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4
    )
    external_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    position: Mapped[str] = mapped_column(String(20), nullable=False)
    team_id: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    sport: Mapped[str] = mapped_column(String(10), nullable=False)

    injury_status: Mapped[str] = mapped_column(String(20), nullable=False, default="healthy")
    injury_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    season_stats: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    game_stats: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    projections: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("sport IN ('mlb', 'nfl', 'wnba')", name="valid_sport"),
        CheckConstraint(
            "injury_status IN ('healthy', 'questionable', 'doubtful', 'out')",
            name="valid_injury_status",
        ),
        CheckConstraint(
            """
            CASE
                WHEN sport = 'mlb' THEN position IN ('C', '1B', '2B', '3B', 'SS', 'OF', 'P', 'DH')
                WHEN sport = 'nfl' THEN position IN ('QB', 'RB', 'WR', 'TE', 'K', 'DEF')
                WHEN sport = 'wnba' THEN position IN ('PG', 'SG', 'SF', 'PF', 'C')
                ELSE TRUE
            END
            """,
            name="valid_position_for_sport",
        ),
        Index("idx_external_id_sport", "external_id", "sport", unique=True),
        Index("idx_sport_position", "sport", "position"),
        Index("idx_team_sport", "team_id", "sport"),
        Index("idx_injury_status", "injury_status"),
    )

    def __repr__(self) -> str:  # pragma: no cover - repr helper
        return (
            f"<Player(name='{self.name}', sport='{self.sport}', position='{self.position}')>"
        )
