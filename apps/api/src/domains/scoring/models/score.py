from __future__ import annotations

import uuid as _uuid
from datetime import date, datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from domains.shared.models.base import Base


class Score(Base):
    __tablename__ = "scores"

    score_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4
    )
    player_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.player_id"), nullable=False
    )
    league_id: Mapped[Optional[_uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leagues.league_id"), nullable=True
    )
    team_id: Mapped[Optional[_uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.team_id"), nullable=True
    )

    game_day: Mapped[date] = mapped_column(Date, nullable=False)
    week: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    season: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    opponent_team: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    game_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_home_game: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    stat_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default=dict
    )
    fantasy_points: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    bonus_points: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    scoring_type: Mapped[str] = mapped_column(String(20), nullable=False, default="game")
    is_projected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_final: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    last_updated_from_source: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint("week > 0", name="positive_score_week"),
        Index("idx_score_player", "player_id"),
        Index("idx_score_league", "league_id"),
        Index("idx_score_game_day", "game_day"),
        Index("idx_score_team", "team_id"),
        Index("idx_score_scoring_type", "scoring_type"),
    )
