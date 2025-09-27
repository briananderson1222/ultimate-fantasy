from __future__ import annotations

import uuid as _uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from domains.shared.models.base import Base


class League(Base):
    """Domain league model with full configuration and state."""

    __tablename__ = "leagues"

    league_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sport: Mapped[str] = mapped_column(String(10), nullable=False)
    league_type: Mapped[str] = mapped_column(String(20), nullable=False)
    season: Mapped[str] = mapped_column(String(16), nullable=False)

    commissioner_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    max_teams: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="setup")
    invite_code: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)

    scoring_rules: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    roster_settings: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    draft_settings: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    waiver_settings: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    trade_settings: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    playoff_settings: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "sport IN ('mlb', 'nfl', 'wnba', 'basketball')",
            name="valid_league_sport",
        ),
        CheckConstraint(
            "league_type IN ('head_to_head', 'rotisserie')", name="valid_league_type"
        ),
        CheckConstraint(
            "status IN ('setup', 'drafting', 'active', 'completed')",
            name="valid_league_status",
        ),
        CheckConstraint("max_teams >= 2 AND max_teams <= 20", name="valid_max_teams"),
        Index("idx_commissioner_id", "commissioner_id"),
        Index("idx_sport_season", "sport", "season"),
        Index("idx_status", "status"),
        Index("idx_invite_code", "invite_code", unique=True),
    )

    def can_transition_to(self, new_status: str) -> bool:
        transitions = {
            "setup": ["drafting"],
            "drafting": ["active", "setup"],
            "active": ["completed"],
            "completed": [],
        }
        return new_status in transitions.get(self.status, [])

    def is_full(self, current_team_count: int) -> bool:
        return current_team_count >= self.max_teams

    def get_default_scoring_rules(self) -> dict[str, Any]:
        defaults = {
            "mlb": {
                "hits": 1,
                "doubles": 2,
                "triples": 3,
                "home_runs": 4,
                "rbis": 1,
                "runs": 1,
                "stolen_bases": 2,
                "walks": 1,
                "strikeouts": -1,
                "wins": 5,
                "saves": 5,
                "innings_pitched": 1,
                "earned_runs": -1,
                "whip": -1,
            },
            "nfl": {
                "passing_yards": 0.04,
                "passing_touchdowns": 4,
                "interceptions": -2,
                "rushing_yards": 0.1,
                "rushing_touchdowns": 6,
                "receiving_yards": 0.1,
                "receiving_touchdowns": 6,
                "receptions": 1,
                "field_goals": 3,
                "extra_points": 1,
                "defense_touchdowns": 6,
                "sacks": 1,
                "interceptions_defense": 2,
            },
            "wnba": {
                "points": 1,
                "rebounds": 1.2,
                "assists": 1.5,
                "steals": 2,
                "blocks": 2,
                "turnovers": -1,
                "field_goal_made": 1,
                "field_goal_missed": -0.5,
                "free_throw_made": 1,
                "free_throw_missed": -0.5,
                "three_pointers": 1,
            },
        }
        return defaults.get(self.sport, {})

    def get_default_roster_settings(self) -> dict[str, Any]:
        defaults = {
            "mlb": {
                "starting_positions": [
                    "C",
                    "1B",
                    "2B",
                    "3B",
                    "SS",
                    "OF",
                    "OF",
                    "OF",
                    "P",
                    "P",
                ],
                "bench_spots": 5,
                "ir_spots": 2,
            },
            "nfl": {
                "starting_positions": [
                    "QB",
                    "RB",
                    "RB",
                    "WR",
                    "WR",
                    "TE",
                    "FLEX",
                    "K",
                    "DEF",
                ],
                "bench_spots": 6,
                "ir_spots": 1,
            },
            "wnba": {
                "starting_positions": [
                    "PG",
                    "SG",
                    "SF",
                    "PF",
                    "C",
                    "FLEX",
                    "FLEX",
                ],
                "bench_spots": 5,
                "ir_spots": 1,
            },
        }
        return defaults.get(self.sport, {})

    def get_default_draft_settings(self) -> dict[str, Any]:
        return {"type": "snake", "timer_seconds": 90}

    def get_default_trade_settings(self) -> dict[str, Any]:
        return {"review_period_hours": 48, "veto_threshold": 0.5}
