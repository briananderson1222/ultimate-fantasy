from __future__ import annotations

import uuid as _uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from domains.shared.models.base import Base


class Team(Base):
    __tablename__ = "teams"

    team_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4
    )
    league_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leagues.league_id"), nullable=False
    )
    user_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )

    team_name: Mapped[str] = mapped_column(String(120), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    wins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    losses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ties: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    points_for: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    points_against: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    waiver_priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    faab_budget: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    roster: Mapped[list[str] | None] = mapped_column(JSON, nullable=True, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_unique_team_name_per_league", "league_id", "team_name", unique=True),
        Index("idx_unique_user_per_league", "league_id", "user_id", unique=True),
        CheckConstraint("faab_budget >= 0", name="non_negative_budget"),
        CheckConstraint("waiver_priority > 0", name="positive_waiver_priority"),
        CheckConstraint(
            "wins >= 0 AND losses >= 0 AND ties >= 0", name="non_negative_record"
        ),
        CheckConstraint(
            "points_for >= 0 AND points_against >= 0", name="non_negative_points"
        ),
        Index("idx_team_league_id", "league_id"),
        Index("idx_team_user_id", "user_id"),
        Index("idx_waiver_priority", "waiver_priority"),
    )

    def __repr__(self) -> str:  # pragma: no cover - repr helper
        return f"<Team(team_name='{self.team_name}', wins={self.wins}, losses={self.losses})>"

    @property
    def win_percentage(self) -> float:
        total_games = self.wins + self.losses + self.ties
        if total_games == 0:
            return 0.0
        effective_wins = self.wins + (self.ties * 0.5)
        return round(effective_wins / total_games, 3)

    @property
    def points_differential(self) -> float:
        return round(self.points_for - self.points_against, 2)

    def add_player_to_roster(self, player_id: str) -> bool:
        if self.roster is None:
            self.roster = []
        if player_id not in self.roster:
            self.roster.append(player_id)
            return True
        return False

    def remove_player_from_roster(self, player_id: str) -> bool:
        if self.roster is None:
            self.roster = []
        if player_id in self.roster:
            self.roster.remove(player_id)
            return True
        return False

    def is_roster_full(self, max_roster_size: int = 15) -> bool:
        return bool(self.roster) and len(self.roster) >= max_roster_size

    def get_roster_count_by_position(
        self, player_positions: dict[str, str]
    ) -> dict[str, int]:
        counts: dict[str, int] = {}
        for player_id in self.roster or []:
            position = player_positions.get(player_id, "UNKNOWN")
            counts[position] = counts.get(position, 0) + 1
        return counts

    def can_afford_bid(self, bid_amount: int) -> bool:
        return self.faab_budget >= bid_amount

    def process_waiver_bid(self, bid_amount: int) -> bool:
        if self.can_afford_bid(bid_amount):
            self.faab_budget -= bid_amount
            return True
        return False

    def record_game_result(self, points_scored: float, opponent_points: float) -> None:
        self.points_for += points_scored
        self.points_against += opponent_points
        if points_scored > opponent_points:
            self.wins += 1
        elif points_scored < opponent_points:
            self.losses += 1
        else:
            self.ties += 1
