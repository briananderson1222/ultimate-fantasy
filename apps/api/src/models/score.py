from __future__ import annotations

import uuid as _uuid
from datetime import datetime, date
from typing import Optional, Dict, Any

from sqlalchemy import String, Integer, Float, DateTime, Date, Boolean, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class Score(Base):
    """
    Individual player scoring events and aggregated totals

    Implements T021 requirements:
    - Score entity for player performance tracking
    - Add stat_values JSON, fantasy_points calculation
    - Include real-time scoring updates and aggregation
    """
    __tablename__ = "scores"

    # Primary identification
    score_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4
    )
    player_id: Mapped[str] = mapped_column(String(64), nullable=False)  # External player ID
    league_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leagues.league_id"),
        nullable=False
    )

    # Scoring period identification
    game_date: Mapped[date] = mapped_column(Date, nullable=False)
    week: Mapped[int] = mapped_column(Integer, nullable=False)
    season: Mapped[str] = mapped_column(String(16), nullable=False)

    # Game context
    opponent_team: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    game_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_home_game: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Statistical performance (JSON object with stat categories)
    stat_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, default=dict)

    # Fantasy scoring
    fantasy_points: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    bonus_points: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Scoring metadata
    scoring_type: Mapped[str] = mapped_column(String(20), nullable=False, default="game")
    is_projected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_final: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Update tracking
    last_updated_from_source: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Validation constraints
    __table_args__ = (
        # Scoring type validation
        CheckConstraint(
            "scoring_type IN ('game', 'weekly', 'season')",
            name="valid_scoring_type"
        ),
        # Week must be positive
        CheckConstraint(
            "week > 0",
            name="positive_week"
        ),
        # Fantasy points must be finite
        CheckConstraint(
            "fantasy_points IS NOT NULL AND fantasy_points = fantasy_points",  # Check for NaN
            name="valid_fantasy_points"
        ),
        # Bonus points must be non-negative
        CheckConstraint(
            "bonus_points >= 0",
            name="non_negative_bonus_points"
        ),
        # Unique score per player per game/period
        Index('idx_unique_score_per_player_game', 'player_id', 'league_id', 'game_date', 'scoring_type', unique=True),
        # Common query indexes
        Index('idx_score_player_id', 'player_id'),
        Index('idx_score_league_id', 'league_id'),
        Index('idx_score_game_date', 'game_date'),
        Index('idx_score_week_season', 'week', 'season'),
        Index('idx_score_fantasy_points', 'fantasy_points'),
        Index('idx_score_is_final', 'is_final'),
        Index('idx_score_is_projected', 'is_projected'),
    )

    def __repr__(self) -> str:
        return f"<Score(player_id='{self.player_id}', points={self.fantasy_points}, date='{self.game_date}')>"

    def calculate_total_points(self) -> float:
        """Calculate total fantasy points including bonuses"""
        return round(self.fantasy_points + self.bonus_points, 2)

    def get_stat_value(self, stat_name: str, default: float = 0.0) -> float:
        """Get specific stat value with default fallback"""
        if not self.stat_values:
            return default
        return float(self.stat_values.get(stat_name, default))

    def set_stat_value(self, stat_name: str, value: float) -> None:
        """Set specific stat value"""
        if self.stat_values is None:
            self.stat_values = {}
        self.stat_values[stat_name] = value

    def update_stat_values(self, new_stats: Dict[str, Any]) -> None:
        """Update multiple stat values at once"""
        if self.stat_values is None:
            self.stat_values = {}
        self.stat_values.update(new_stats)

    def calculate_fantasy_points(self, scoring_rules: Dict[str, float]) -> float:
        """
        Calculate fantasy points based on league scoring rules

        Args:
            scoring_rules: Dictionary mapping stat names to point values

        Returns:
            Calculated fantasy points
        """
        if not self.stat_values or not scoring_rules:
            return 0.0

        total_points = 0.0
        for stat_name, point_value in scoring_rules.items():
            stat_value = self.get_stat_value(stat_name, 0.0)
            total_points += stat_value * point_value

        return round(total_points, 2)

    def apply_scoring_rules(self, scoring_rules: Dict[str, float]) -> None:
        """Apply league scoring rules and update fantasy_points"""
        self.fantasy_points = self.calculate_fantasy_points(scoring_rules)

    def mark_as_final(self) -> None:
        """Mark score as final (game completed)"""
        self.is_final = True
        self.is_projected = False

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of player performance"""
        return {
            "player_id": self.player_id,
            "game_date": self.game_date.isoformat(),
            "fantasy_points": self.calculate_total_points(),
            "is_final": self.is_final,
            "is_projected": self.is_projected,
            "key_stats": self._get_key_stats(),
            "opponent": self.opponent_team
        }

    def _get_key_stats(self) -> Dict[str, Any]:
        """Get key statistics for display"""
        if not self.stat_values:
            return {}

        # Common key stats across sports
        key_stats = {}

        # Points scored (universal)
        if "points" in self.stat_values:
            key_stats["points"] = self.stat_values["points"]

        # Sport-specific key stats
        sport_key_stats = {
            "mlb": ["hits", "home_runs", "rbis", "runs", "wins", "saves", "innings_pitched"],
            "nfl": ["passing_yards", "passing_touchdowns", "rushing_yards", "rushing_touchdowns", "receiving_yards", "receptions"],
            "wnba": ["points", "rebounds", "assists", "steals", "blocks"]
        }

        # Try to determine sport from available stats and include relevant ones
        for stat in self.stat_values:
            if stat in ["hits", "home_runs", "rbis"]:  # MLB indicators
                for mlb_stat in sport_key_stats["mlb"]:
                    if mlb_stat in self.stat_values:
                        key_stats[mlb_stat] = self.stat_values[mlb_stat]
                break
            elif stat in ["passing_yards", "rushing_yards"]:  # NFL indicators
                for nfl_stat in sport_key_stats["nfl"]:
                    if nfl_stat in self.stat_values:
                        key_stats[nfl_stat] = self.stat_values[nfl_stat]
                break
            elif stat in ["rebounds", "assists"]:  # WNBA indicators
                for wnba_stat in sport_key_stats["wnba"]:
                    if wnba_stat in self.stat_values:
                        key_stats[wnba_stat] = self.stat_values[wnba_stat]
                break

        return key_stats