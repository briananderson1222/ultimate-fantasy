from __future__ import annotations

import uuid as _uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from domains.shared.models.base import Base


class Trade(Base):
    __tablename__ = "trades"

    trade_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4
    )
    league_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leagues.league_id"), nullable=False
    )
    offering_team_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.team_id"), nullable=False
    )
    receiving_team_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.team_id"), nullable=False
    )

    offered_players: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True, default=list
    )
    requested_players: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True, default=list
    )

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    trade_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    commissioner_notes: Mapped[str | None] = mapped_column(
        String(1000), nullable=True
    )
    vetoed_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'accepted', 'rejected', 'expired', 'vetoed', 'completed')",
            name="valid_trade_status",
        ),
        CheckConstraint(
            "offering_team_id != receiving_team_id", name="different_trade_teams"
        ),
        Index("idx_trade_league_id", "league_id"),
        Index("idx_trade_offering_team", "offering_team_id"),
        Index("idx_trade_receiving_team", "receiving_team_id"),
        Index("idx_trade_status", "status"),
        Index("idx_trade_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover - repr helper
        return (
            f"<Trade(offering_team='{self.offering_team_id}', "
            f"receiving_team='{self.receiving_team_id}', status='{self.status}')>"
        )

    def can_transition_to(self, new_status: str) -> bool:
        transitions = {
            "pending": ["accepted", "rejected", "expired"],
            "accepted": ["vetoed", "completed"],
            "rejected": [],
            "expired": [],
            "vetoed": [],
            "completed": [],
        }
        return new_status in transitions.get(self.status, [])

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def get_trade_value_summary(self) -> dict[str, Any]:
        return {
            "offered_count": len(self.offered_players or []),
            "requested_count": len(self.requested_players or []),
            "is_balanced": self._is_player_count_balanced(),
            "status": self.status,
        }

    def _is_player_count_balanced(self) -> bool:
        offered_count = len(self.offered_players or [])
        requested_count = len(self.requested_players or [])
        return offered_count == requested_count

    def add_offered_player(self, player_id: str) -> bool:
        if self.offered_players is None:
            self.offered_players = []
        if player_id not in self.offered_players:
            self.offered_players.append(player_id)
            return True
        return False

    def add_requested_player(self, player_id: str) -> bool:
        if self.requested_players is None:
            self.requested_players = []
        if player_id not in self.requested_players:
            self.requested_players.append(player_id)
            return True
        return False

    def remove_offered_player(self, player_id: str) -> bool:
        if self.offered_players and player_id in self.offered_players:
            self.offered_players.remove(player_id)
            return True
        return False

    def remove_requested_player(self, player_id: str) -> bool:
        if self.requested_players and player_id in self.requested_players:
            self.requested_players.remove(player_id)
            return True
        return False
