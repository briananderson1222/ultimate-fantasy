from __future__ import annotations

import uuid as _uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class Team(Base):
    """
    Individual user teams within leagues

    Implements T016 requirements:
    - Team entity linking users to leagues
    - Add wins, losses, points_for, waiver_priority tracking fields
    - Include roster JSON array and budget management
    """
    __tablename__ = "teams"

    # Primary identification
    team_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4
    )
    league_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leagues.league_id"),
        nullable=False
    )
    user_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False
    )

    # Team identification
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Season performance tracking
    wins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    losses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ties: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    points_for: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    points_against: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Waiver and budget management
    waiver_priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    faab_budget: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    # Roster management (JSON array of player_ids)
    roster: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True, default=list)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Validation constraints
    __table_args__ = (
        # Team name must be unique within league
        Index('idx_unique_team_name_per_league', 'league_id', 'name', unique=True),
        # User can only have one team per league
        Index('idx_unique_user_per_league', 'league_id', 'user_id', unique=True),
        # Budget must be non-negative
        CheckConstraint(
            "faab_budget >= 0",
            name="non_negative_budget"
        ),
        # Waiver priority must be positive
        CheckConstraint(
            "waiver_priority > 0",
            name="positive_waiver_priority"
        ),
        # Performance stats validation
        CheckConstraint(
            "wins >= 0 AND losses >= 0 AND ties >= 0",
            name="non_negative_record"
        ),
        CheckConstraint(
            "points_for >= 0 AND points_against >= 0",
            name="non_negative_points"
        ),
        # Common query indexes
        Index('idx_team_league_id', 'league_id'),
        Index('idx_team_user_id', 'user_id'),
        Index('idx_waiver_priority', 'waiver_priority'),
    )

    def __repr__(self) -> str:
        return f"<Team(name='{self.name}', wins={self.wins}, losses={self.losses})>"

    @property
    def win_percentage(self) -> float:
        """Calculate team's win percentage"""
        total_games = self.wins + self.losses + self.ties
        if total_games == 0:
            return 0.0

        # Ties count as half wins for percentage calculation
        effective_wins = self.wins + (self.ties * 0.5)
        return round(effective_wins / total_games, 3)

    @property
    def points_differential(self) -> float:
        """Calculate points differential (points for - points against)"""
        return round(self.points_for - self.points_against, 2)

    def add_player_to_roster(self, player_id: str) -> bool:
        """Add player to team roster if not already present"""
        if self.roster is None:
            self.roster = []

        if player_id not in self.roster:
            self.roster.append(player_id)
            return True
        return False

    def remove_player_from_roster(self, player_id: str) -> bool:
        """Remove player from team roster if present"""
        if self.roster is None:
            self.roster = []

        if player_id in self.roster:
            self.roster.remove(player_id)
            return True
        return False

    def is_roster_full(self, max_roster_size: int = 15) -> bool:
        """Check if roster has reached maximum capacity"""
        if self.roster is None:
            return False
        return len(self.roster) >= max_roster_size

    def get_roster_count_by_position(self, player_positions: Dict[str, str]) -> Dict[str, int]:
        """Get count of players by position on roster"""
        position_counts = {}

        if self.roster is None:
            return position_counts

        for player_id in self.roster:
            position = player_positions.get(player_id, "UNKNOWN")
            position_counts[position] = position_counts.get(position, 0) + 1

        return position_counts

    def can_afford_bid(self, bid_amount: int) -> bool:
        """Check if team can afford a waiver bid"""
        return self.faab_budget >= bid_amount

    def process_waiver_bid(self, bid_amount: int) -> bool:
        """Process a waiver bid, deducting from budget"""
        if self.can_afford_bid(bid_amount):
            self.faab_budget -= bid_amount
            return True
        return False

    def record_game_result(self, points_scored: float, opponent_points: float) -> None:
        """Record the result of a game"""
        self.points_for += points_scored
        self.points_against += opponent_points

        if points_scored > opponent_points:
            self.wins += 1
        elif points_scored < opponent_points:
            self.losses += 1
        else:
            self.ties += 1