from __future__ import annotations

import uuid as _uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import String, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class Trade(Base):
    """
    Player trading between teams

    Implements T019 requirements:
    - Trade entity for player exchanges between teams
    - Add offered_players, requested_players JSON arrays
    - Include trade evaluation and approval workflow
    """
    __tablename__ = "trades"

    # Primary identification
    trade_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4
    )
    league_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leagues.league_id"),
        nullable=False
    )

    # Trading teams
    offering_team_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.team_id"),
        nullable=False
    )
    receiving_team_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.team_id"),
        nullable=False
    )

    # Trade details (JSON arrays of player_ids)
    offered_players: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True, default=list)
    requested_players: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True, default=list)

    # Trade workflow
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    trade_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Evaluation and approval
    commissioner_notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    vetoed_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Trade deadlines
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Validation constraints
    __table_args__ = (
        # Status validation
        CheckConstraint(
            "status IN ('pending', 'accepted', 'rejected', 'expired', 'vetoed', 'completed')",
            name="valid_trade_status"
        ),
        # Teams cannot trade with themselves
        CheckConstraint(
            "offering_team_id != receiving_team_id",
            name="different_trade_teams"
        ),
        # Common query indexes
        Index('idx_trade_league_id', 'league_id'),
        Index('idx_trade_offering_team', 'offering_team_id'),
        Index('idx_trade_receiving_team', 'receiving_team_id'),
        Index('idx_trade_status', 'status'),
        Index('idx_trade_expires_at', 'expires_at'),
    )

    def __repr__(self) -> str:
        return f"<Trade(offering_team='{self.offering_team_id}', receiving_team='{self.receiving_team_id}', status='{self.status}')>"

    def can_transition_to(self, new_status: str) -> bool:
        """
        Validate trade status transitions:
        pending → accepted/rejected/expired
        accepted → vetoed/completed
        """
        valid_transitions = {
            "pending": ["accepted", "rejected", "expired"],
            "accepted": ["vetoed", "completed"],
            "rejected": [],  # Terminal state
            "expired": [],   # Terminal state
            "vetoed": [],    # Terminal state
            "completed": []  # Terminal state
        }

        return new_status in valid_transitions.get(self.status, [])

    def is_expired(self) -> bool:
        """Check if trade has expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def get_trade_value_summary(self) -> Dict[str, Any]:
        """Get summary of trade value for evaluation"""
        return {
            "offered_count": len(self.offered_players) if self.offered_players else 0,
            "requested_count": len(self.requested_players) if self.requested_players else 0,
            "is_balanced": self._is_player_count_balanced(),
            "status": self.status
        }

    def _is_player_count_balanced(self) -> bool:
        """Check if trade has equal number of players on each side"""
        offered_count = len(self.offered_players) if self.offered_players else 0
        requested_count = len(self.requested_players) if self.requested_players else 0
        return offered_count == requested_count

    def add_offered_player(self, player_id: str) -> bool:
        """Add player to offered side of trade"""
        if self.offered_players is None:
            self.offered_players = []

        if player_id not in self.offered_players:
            self.offered_players.append(player_id)
            return True
        return False

    def add_requested_player(self, player_id: str) -> bool:
        """Add player to requested side of trade"""
        if self.requested_players is None:
            self.requested_players = []

        if player_id not in self.requested_players:
            self.requested_players.append(player_id)
            return True
        return False

    def remove_offered_player(self, player_id: str) -> bool:
        """Remove player from offered side of trade"""
        if self.offered_players and player_id in self.offered_players:
            self.offered_players.remove(player_id)
            return True
        return False

    def remove_requested_player(self, player_id: str) -> bool:
        """Remove player from requested side of trade"""
        if self.requested_players and player_id in self.requested_players:
            self.requested_players.remove(player_id)
            return True
        return False