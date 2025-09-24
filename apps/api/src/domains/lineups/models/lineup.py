from __future__ import annotations

import uuid as _uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from domains.shared.models.base import Base


class Lineup(Base):
    __tablename__ = "lineups"

    lineup_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4
    )
    team_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.team_id"), nullable=False
    )

    week: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    game_day: Mapped[date | None] = mapped_column(Date, nullable=True)

    players: Mapped[list[dict[str, str]] | None] = mapped_column(
        JSON, nullable=True, default=list
    )
    points_scored: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index(
            "idx_unique_lineup_per_team_week",
            "team_id",
            "week",
            "game_day",
            unique=True,
        ),
        CheckConstraint("week > 0", name="positive_week"),
        CheckConstraint("points_scored >= 0", name="non_negative_points"),
        CheckConstraint("version > 0", name="positive_version"),
        Index("idx_lineup_team_id", "team_id"),
        Index("idx_lineup_week", "week"),
        Index("idx_lineup_game_day", "game_day"),
        Index("idx_lineup_locked", "is_locked"),
    )
