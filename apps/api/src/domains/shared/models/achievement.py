from __future__ import annotations

import uuid as _uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from domains.shared.models.base import Base


class Achievement(Base):
    """User achievements and milestone tracking system."""

    __tablename__ = "achievements"

    achievement_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4
    )
    user_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    league_id: Mapped[_uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leagues.league_id"), nullable=True
    )
    team_id: Mapped[_uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.team_id"), nullable=True
    )

    achievement_type: Mapped[str] = mapped_column(String(50), nullable=False)
    achievement_name: Mapped[str] = mapped_column(String(100), nullable=False)
    achievement_description: Mapped[str] = mapped_column(String(500), nullable=False)
    achievement_icon: Mapped[str | None] = mapped_column(String(200), nullable=True)

    rarity: Mapped[str] = mapped_column(String(15), nullable=False, default="common")
    points_value: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    category: Mapped[str] = mapped_column(String(30), nullable=False)

    is_unlocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    progress_current: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progress_target: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    achievement_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, default=dict
    )
    unlock_conditions: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, default=dict
    )

    is_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    unlocked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    season: Mapped[str | None] = mapped_column(String(16), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            """
            achievement_type IN (
                'first_login', 'first_league', 'first_trade', 'first_championship',
                'win_streak', 'perfect_lineup', 'draft_master', 'trade_baron',
                'waiver_warrior', 'injury_survivor', 'comeback_kid', 'dynasty_builder',
                'points_milestone', 'games_played', 'seasons_completed'
            )
            """,
            name="valid_achievement_type",
        ),
        CheckConstraint(
            "rarity IN ('common', 'uncommon', 'rare', 'epic', 'legendary')",
            name="valid_rarity",
        ),
        CheckConstraint(
            """
            category IN (
                'getting_started', 'league_management', 'trading', 'drafting',
                'scoring', 'longevity', 'competition', 'special_events'
            )
            """,
            name="valid_category",
        ),
        CheckConstraint("progress_current >= 0", name="non_negative_progress_current"),
        CheckConstraint("progress_target > 0", name="positive_progress_target"),
        CheckConstraint(
            "progress_current <= progress_target", name="progress_within_target"
        ),
        CheckConstraint("points_value > 0", name="positive_points_value"),
        CheckConstraint("display_order >= 0", name="non_negative_display_order"),
        CheckConstraint(
            "NOT (is_unlocked = true AND unlocked_at IS NULL)",
            name="unlocked_has_timestamp",
        ),
        Index("idx_achievement_user_id", "user_id"),
        Index("idx_achievement_league_id", "league_id"),
        Index("idx_achievement_team_id", "team_id"),
        Index("idx_achievement_type", "achievement_type"),
        Index("idx_achievement_category", "category"),
        Index("idx_achievement_rarity", "rarity"),
        Index("idx_achievement_is_unlocked", "is_unlocked"),
        Index("idx_achievement_is_visible", "is_visible"),
        Index("idx_achievement_is_featured", "is_featured"),
        Index("idx_achievement_unlocked_at", "unlocked_at"),
        Index("idx_achievement_season", "season"),
        Index(
            "idx_user_unlocked_achievements",
            "user_id",
            "is_unlocked",
            "unlocked_at",
        ),
        Index(
            "idx_user_progress_achievements",
            "user_id",
            "is_unlocked",
            "progress_current",
        ),
        Index(
            "idx_featured_achievements",
            "is_featured",
            "is_visible",
            "display_order",
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover - repr helper
        return (
            f"<Achievement(user_id='{self.user_id}', type='{self.achievement_type}', "
            f"unlocked={self.is_unlocked})>"
        )

    def calculate_progress_percentage(self) -> float:
        if self.progress_target == 0:
            return 100.0
        return min(100.0, (self.progress_current / self.progress_target) * 100.0)

    def update_progress(self, new_progress: int) -> bool:
        old_progress = self.progress_current
        self.progress_current = min(new_progress, self.progress_target)
        if not self.is_unlocked and self.progress_current >= self.progress_target:
            self.unlock()
            return True
        return old_progress != self.progress_current

    def increment_progress(self, amount: int = 1) -> bool:
        return self.update_progress(self.progress_current + amount)

    def unlock(self) -> None:
        if not self.is_unlocked:
            self.is_unlocked = True
            self.unlocked_at = datetime.utcnow()
            self.progress_current = self.progress_target

    def reset_progress(self) -> None:
        self.progress_current = 0
        self.is_unlocked = False
        self.unlocked_at = None

    def is_completed(self) -> bool:
        return self.is_unlocked and self.progress_current >= self.progress_target

    def get_data_value(self, key: str, default: Any = None) -> Any:
        if not self.achievement_data:
            return default
        return self.achievement_data.get(key, default)

    def set_data_value(self, key: str, value: Any) -> None:
        if self.achievement_data is None:
            self.achievement_data = {}
        self.achievement_data[key] = value

    def update_data(self, new_data: dict[str, Any]) -> None:
        if self.achievement_data is None:
            self.achievement_data = {}
        self.achievement_data.update(new_data)

    def get_condition_value(self, key: str, default: Any = None) -> Any:
        if not self.unlock_conditions:
            return default
        return self.unlock_conditions.get(key, default)

    def set_condition_value(self, key: str, value: Any) -> None:
        if self.unlock_conditions is None:
            self.unlock_conditions = {}
        self.unlock_conditions[key] = value

    def get_rarity_multiplier(self) -> float:
        multipliers = {
            "common": 1.0,
            "uncommon": 1.5,
            "rare": 2.0,
            "epic": 3.0,
            "legendary": 5.0,
        }
        return multipliers.get(self.rarity, 1.0)

    def get_total_points(self) -> int:
        return int(self.points_value * self.get_rarity_multiplier())

    def get_display_data(self) -> dict[str, Any]:
        return {
            "id": str(self.achievement_id),
            "user_id": str(self.user_id),
            "achievement_type": self.achievement_type,
            "name": self.achievement_name,
            "description": self.achievement_description,
            "icon": self.achievement_icon,
            "category": self.category,
            "rarity": self.rarity,
            "points_value": self.points_value,
            "total_points": self.get_total_points(),
            "is_unlocked": self.is_unlocked,
            "progress_current": self.progress_current,
            "progress_target": self.progress_target,
            "progress_percentage": self.calculate_progress_percentage(),
            "is_visible": self.is_visible,
            "is_featured": self.is_featured,
            "unlocked_at": self.unlocked_at.isoformat() if self.unlocked_at else None,
            "season": self.season,
            "league_id": str(self.league_id) if self.league_id else None,
            "team_id": str(self.team_id) if self.team_id else None,
        }

    @classmethod
    def create_first_login_achievement(cls, user_id: _uuid.UUID) -> Achievement:
        return cls(
            user_id=user_id,
            achievement_type="first_login",
            achievement_name="Welcome to Fantasy Sports!",
            achievement_description="Complete your first login to the platform",
            category="getting_started",
            rarity="common",
            points_value=10,
            progress_target=1,
        )

    @classmethod
    def create_first_league_achievement(
        cls, user_id: _uuid.UUID, league_id: _uuid.UUID
    ) -> Achievement:
        return cls(
            user_id=user_id,
            league_id=league_id,
            achievement_type="first_league",
            achievement_name="League Pioneer",
            achievement_description="Join your first fantasy league",
            category="getting_started",
            rarity="common",
            points_value=25,
            progress_target=1,
        )

    @classmethod
    def create_championship_achievement(
        cls,
        user_id: _uuid.UUID,
        league_id: _uuid.UUID,
        team_id: _uuid.UUID,
        season: str,
    ) -> Achievement:
        return cls(
            user_id=user_id,
            league_id=league_id,
            team_id=team_id,
            achievement_type="first_championship",
            achievement_name="Champion!",
            achievement_description="Win your first league championship",
            category="competition",
            rarity="epic",
            points_value=100,
            progress_target=1,
            season=season,
            is_featured=True,
        )
