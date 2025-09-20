from __future__ import annotations

import uuid as _uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class WaiverBid(Base):
    """
    Waiver wire bidding system for free agent acquisitions

    Implements T020 requirements:
    - WaiverBid entity for free agent player claims
    - Add bid_amount, waiver_priority, processing workflow
    - Include claim evaluation and award logic
    """
    __tablename__ = "waiver_bids"

    # Primary identification
    bid_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4
    )
    league_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leagues.league_id"),
        nullable=False
    )
    team_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.team_id"),
        nullable=False
    )

    # Player and transaction details
    player_id: Mapped[str] = mapped_column(String(64), nullable=False)  # External player ID
    dropped_player_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # Player being dropped

    # Bidding details
    bid_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    waiver_priority: Mapped[int] = mapped_column(Integer, nullable=False)

    # Bid workflow
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    processing_order: Mapped[int] = mapped_column(Integer, nullable=False)

    # Processing details
    award_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Processing timestamps
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    waiver_period_ends: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

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
            "status IN ('pending', 'awarded', 'rejected', 'expired')",
            name="valid_bid_status"
        ),
        # Bid amount must be non-negative
        CheckConstraint(
            "bid_amount >= 0",
            name="non_negative_bid_amount"
        ),
        # Waiver priority must be positive
        CheckConstraint(
            "waiver_priority > 0",
            name="positive_waiver_priority"
        ),
        # Processing order must be positive
        CheckConstraint(
            "processing_order > 0",
            name="positive_processing_order"
        ),
        # Unique bid per team per player per waiver period
        Index('idx_unique_bid_per_team_player', 'team_id', 'player_id', 'waiver_period_ends', unique=True),
        # Common query indexes
        Index('idx_waiver_league_id', 'league_id'),
        Index('idx_waiver_team_id', 'team_id'),
        Index('idx_waiver_player_id', 'player_id'),
        Index('idx_waiver_status', 'status'),
        Index('idx_waiver_processing_order', 'processing_order'),
        Index('idx_waiver_period_ends', 'waiver_period_ends'),
        Index('idx_waiver_priority_bid', 'waiver_priority', 'bid_amount'),
    )

    def __repr__(self) -> str:
        return f"<WaiverBid(team_id='{self.team_id}', player_id='{self.player_id}', bid=${self.bid_amount}, status='{self.status}')>"

    def can_transition_to(self, new_status: str) -> bool:
        """
        Validate waiver bid status transitions:
        pending → awarded/rejected/expired
        """
        valid_transitions = {
            "pending": ["awarded", "rejected", "expired"],
            "awarded": [],   # Terminal state
            "rejected": [],  # Terminal state
            "expired": []    # Terminal state
        }

        return new_status in valid_transitions.get(self.status, [])

    def is_expired(self) -> bool:
        """Check if waiver period has ended"""
        return datetime.utcnow() > self.waiver_period_ends

    def get_priority_score(self) -> tuple:
        """
        Get priority score for bid evaluation.
        Returns tuple for sorting: (waiver_priority, -bid_amount, processing_order)
        Lower waiver priority number = higher priority
        Higher bid amount = higher priority (hence negative)
        Lower processing order = higher priority (tie-breaker)
        """
        return (self.waiver_priority, -self.bid_amount, self.processing_order)

    def calculate_net_budget_impact(self, current_budget: int) -> int:
        """Calculate the net budget impact if this bid is awarded"""
        return current_budget - self.bid_amount

    def has_valid_drop_player(self) -> bool:
        """Check if a valid drop player is specified when required"""
        # If no drop player specified, assume roster has space
        return self.dropped_player_id is not None

    def get_transaction_summary(self) -> dict:
        """Get summary of the waiver transaction"""
        return {
            "action": "waiver_claim",
            "player_added": self.player_id,
            "player_dropped": self.dropped_player_id,
            "bid_amount": self.bid_amount,
            "status": self.status,
            "priority": self.waiver_priority
        }

    def award_bid(self, reason: str = "Highest priority bid") -> None:
        """Award the waiver bid"""
        self.status = "awarded"
        self.award_reason = reason
        self.processed_at = datetime.utcnow()

    def reject_bid(self, reason: str) -> None:
        """Reject the waiver bid"""
        self.status = "rejected"
        self.rejection_reason = reason
        self.processed_at = datetime.utcnow()

    def expire_bid(self) -> None:
        """Mark bid as expired"""
        self.status = "expired"
        self.rejection_reason = "Waiver period expired"
        self.processed_at = datetime.utcnow()