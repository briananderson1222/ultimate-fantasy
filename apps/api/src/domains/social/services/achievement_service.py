"""
Achievement tracking system service.

Provides comprehensive achievement and gamification features including:
- Dynamic achievement definitions and tracking
- Progress monitoring and milestone rewards
- Leaderboards and competitive rankings
- Badge collections and trophy systems
- Social sharing and celebration features
"""

import contextlib
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

try:
    from infrastructure.cache.redis_pool import get_redis_pool
except ImportError:
    get_redis_pool = None

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging

    get_logger = logging.getLogger

try:
    from models.achievement import Achievement, UserAchievement
    from models.league import League
    from models.user import User
except ImportError:
    # Mock classes for when models aren't available
    class Achievement:
        pass

    class UserAchievement:
        pass

    class User:
        pass

    class League:
        pass


logger = get_logger(__name__)


class AchievementType(Enum):
    """Achievement category types."""

    DRAFT = "draft"
    TRADING = "trading"
    LINEUP = "lineup"
    SCORING = "scoring"
    SOCIAL = "social"
    LEAGUE = "league"
    SEASONAL = "seasonal"
    MILESTONE = "milestone"


class AchievementRarity(Enum):
    """Achievement rarity levels."""

    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class ProgressType(Enum):
    """Progress tracking types."""

    COUNTER = "counter"  # Count occurrences
    PERCENTAGE = "percentage"  # Track percentage completion
    STREAK = "streak"  # Track consecutive events
    THRESHOLD = "threshold"  # Reach specific value
    BOOLEAN = "boolean"  # One-time achievement


@dataclass
class AchievementDefinition:
    """Achievement definition and requirements."""

    achievement_id: str
    name: str
    description: str
    category: AchievementType
    rarity: AchievementRarity
    progress_type: ProgressType
    target_value: int | None = None
    conditions: dict[str, Any] = field(default_factory=dict)
    rewards: dict[str, Any] = field(default_factory=dict)
    prerequisites: list[str] = field(default_factory=list)
    icon_url: str | None = None
    is_hidden: bool = False
    is_repeatable: bool = False
    season_specific: bool = False
    points_value: int = 10


@dataclass
class UserProgress:
    """User progress on an achievement."""

    user_id: str
    achievement_id: str
    current_value: int = 0
    target_value: int = 1
    progress_percentage: float = 0.0
    is_completed: bool = False
    completed_at: datetime | None = None
    last_updated: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AchievementReward:
    """Achievement reward details."""

    reward_id: str
    achievement_id: str
    reward_type: str  # points, badge, title, unlock
    value: Any
    display_name: str
    description: str | None = None


@dataclass
class LeaderboardEntry:
    """Leaderboard entry."""

    user_id: str
    username: str
    score: int
    rank: int
    achievements_count: int
    rare_achievements: int
    total_points: int
    avatar_url: str | None = None


class AchievementService:
    """
    Comprehensive achievement tracking and gamification service.

    Features:
    - Dynamic achievement definitions and criteria
    - Real-time progress tracking and updates
    - Automated unlock notifications
    - Leaderboards and competitive rankings
    - Reward distribution and badge management
    """

    def __init__(self, db_session: AsyncSession, redis_pool=None):
        self.db_session = db_session
        self.redis_pool = redis_pool

        # Achievement definitions
        self.achievements: dict[str, AchievementDefinition] = {}

        # Progress tracking
        self.user_progress: dict[str, dict[str, UserProgress]] = {}

        # Event listeners for achievement triggers
        self.event_listeners: dict[str, list[Callable]] = {}

        self._initialized = False

    async def initialize(self):
        """Initialize achievement service."""
        if self._initialized:
            return

        # Load achievement definitions
        await self._load_achievement_definitions()

        # Setup event listeners
        await self._setup_event_listeners()

        # Load user progress cache
        await self._load_user_progress_cache()

        self._initialized = True
        logger.info("Achievement service initialized")

    async def track_event(
        self, event_name: str, user_id: str, event_data: dict[str, Any]
    ):
        """
        Track an event that may trigger achievement progress.

        Args:
            event_name: Name of the event (e.g., 'draft_pick', 'trade_completed')
            user_id: User who triggered the event
            event_data: Additional event context and data
        """
        await self.initialize()

        # Get relevant achievements for this event
        relevant_achievements = await self._get_achievements_for_event(event_name)

        for achievement in relevant_achievements:
            # Check if user is eligible for this achievement
            if await self._is_user_eligible(user_id, achievement):
                # Update progress
                await self._update_achievement_progress(
                    user_id, achievement, event_name, event_data
                )

        # Update leaderboards
        await self._update_leaderboards(user_id)

    async def get_user_achievements(
        self,
        user_id: str,
        category: AchievementType | None = None,
        completed_only: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Get user's achievements and progress.

        Args:
            user_id: User identifier
            category: Optional category filter
            completed_only: Whether to return only completed achievements

        Returns:
            List of achievement data with progress
        """
        await self.initialize()

        achievements = []

        for achievement_id, definition in self.achievements.items():
            # Apply category filter
            if category and definition.category != category:
                continue

            # Get user progress
            progress = await self._get_user_progress(user_id, achievement_id)

            # Apply completion filter
            if completed_only and not progress.is_completed:
                continue

            # Skip hidden achievements if not completed
            if definition.is_hidden and not progress.is_completed:
                continue

            achievement_data = {
                "achievement_id": achievement_id,
                "name": definition.name,
                "description": definition.description,
                "category": definition.category.value,
                "rarity": definition.rarity.value,
                "icon_url": definition.icon_url,
                "points_value": definition.points_value,
                "is_completed": progress.is_completed,
                "progress": {
                    "current_value": progress.current_value,
                    "target_value": progress.target_value,
                    "percentage": progress.progress_percentage,
                    "completed_at": (
                        progress.completed_at.isoformat()
                        if progress.completed_at
                        else None
                    ),
                },
                "rewards": definition.rewards,
            }

            achievements.append(achievement_data)

        return achievements

    async def get_achievement_leaderboard(
        self,
        category: AchievementType | None = None,
        limit: int = 50,
        league_id: str | None = None,
    ) -> list[LeaderboardEntry]:
        """
        Get achievement leaderboard.

        Args:
            category: Optional category filter
            limit: Maximum entries to return
            league_id: Optional league filter

        Returns:
            List of leaderboard entries
        """
        await self.initialize()

        # Build leaderboard query
        if self.redis_pool:
            return await self._get_redis_leaderboard(category, limit, league_id)
        else:
            return await self._get_db_leaderboard(category, limit, league_id)

    async def unlock_achievement(
        self, user_id: str, achievement_id: str, force: bool = False
    ) -> bool:
        """
        Manually unlock an achievement for a user.

        Args:
            user_id: User identifier
            achievement_id: Achievement to unlock
            force: Whether to force unlock regardless of progress

        Returns:
            True if achievement was unlocked
        """
        await self.initialize()

        if achievement_id not in self.achievements:
            return False

        progress = await self._get_user_progress(user_id, achievement_id)

        if progress.is_completed and not force:
            return False

        # Mark as completed
        progress.is_completed = True
        progress.completed_at = datetime.utcnow()
        progress.current_value = progress.target_value
        progress.progress_percentage = 100.0

        # Save progress
        await self._save_user_progress(user_id, progress)

        # Distribute rewards
        await self._distribute_rewards(user_id, achievement_id)

        # Send notification
        await self._send_achievement_notification(user_id, achievement_id)

        # Update leaderboards
        await self._update_leaderboards(user_id)

        logger.info(f"Achievement {achievement_id} unlocked for user {user_id}")
        return True

    async def get_user_stats(self, user_id: str) -> dict[str, Any]:
        """
        Get comprehensive user achievement statistics.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with user achievement stats
        """
        await self.initialize()

        total_achievements = len(self.achievements)
        completed_count = 0
        total_points = 0
        rarity_counts = {rarity.value: 0 for rarity in AchievementRarity}

        for achievement_id, definition in self.achievements.items():
            progress = await self._get_user_progress(user_id, achievement_id)

            if progress.is_completed:
                completed_count += 1
                total_points += definition.points_value
                rarity_counts[definition.rarity.value] += 1

        completion_rate = (
            (completed_count / total_achievements) * 100
            if total_achievements > 0
            else 0
        )

        return {
            "user_id": user_id,
            "total_achievements": total_achievements,
            "completed_achievements": completed_count,
            "completion_rate": completion_rate,
            "total_points": total_points,
            "rarity_breakdown": rarity_counts,
            "rank": await self._get_user_rank(user_id),
        }

    async def create_achievement(self, definition: AchievementDefinition) -> bool:
        """
        Create a new achievement definition.

        Args:
            definition: Achievement definition

        Returns:
            True if achievement was created successfully
        """
        await self.initialize()

        if definition.achievement_id in self.achievements:
            return False

        # Validate definition
        if not self._validate_achievement_definition(definition):
            return False

        # Store in database
        await self._store_achievement_definition(definition)

        # Add to cache
        self.achievements[definition.achievement_id] = definition

        logger.info(f"Achievement {definition.achievement_id} created")
        return True

    async def _get_achievements_for_event(
        self, event_name: str
    ) -> list[AchievementDefinition]:
        """Get achievements that can be triggered by an event."""
        relevant_achievements = []

        for achievement in self.achievements.values():
            # Check if achievement can be triggered by this event
            trigger_events = achievement.conditions.get("trigger_events", [])
            if event_name in trigger_events:
                relevant_achievements.append(achievement)

        return relevant_achievements

    async def _is_user_eligible(
        self, user_id: str, achievement: AchievementDefinition
    ) -> bool:
        """Check if user is eligible for an achievement."""
        # Check prerequisites
        for prereq_id in achievement.prerequisites:
            prereq_progress = await self._get_user_progress(user_id, prereq_id)
            if not prereq_progress.is_completed:
                return False

        # Check if already completed and not repeatable
        progress = await self._get_user_progress(user_id, achievement.achievement_id)
        if progress.is_completed and not achievement.is_repeatable:
            return False

        # Check season-specific achievements
        if achievement.season_specific:
            # Would check current season eligibility
            pass

        return True

    async def _update_achievement_progress(
        self,
        user_id: str,
        achievement: AchievementDefinition,
        event_name: str,
        event_data: dict[str, Any],
    ):
        """Update progress for a specific achievement."""
        progress = await self._get_user_progress(user_id, achievement.achievement_id)

        if progress.is_completed and not achievement.is_repeatable:
            return

        # Calculate progress update based on achievement type and event
        progress_delta = await self._calculate_progress_delta(
            achievement, event_name, event_data, progress
        )

        if progress_delta == 0:
            return

        # Update progress
        if achievement.progress_type == ProgressType.COUNTER:
            progress.current_value += progress_delta
        elif achievement.progress_type == ProgressType.STREAK:
            # Handle streak logic
            if event_data.get("maintains_streak", True):
                progress.current_value += progress_delta
            else:
                progress.current_value = 1  # Reset streak
        elif achievement.progress_type == ProgressType.THRESHOLD:
            progress.current_value = max(
                progress.current_value, event_data.get("value", 0)
            )
        elif achievement.progress_type == ProgressType.BOOLEAN:
            progress.current_value = 1

        # Update percentage
        if achievement.target_value:
            progress.progress_percentage = min(
                100.0, (progress.current_value / achievement.target_value) * 100
            )

        # Check if completed
        if not progress.is_completed and (
            achievement.target_value
            and progress.current_value >= achievement.target_value
        ):
            progress.is_completed = True
            progress.completed_at = datetime.utcnow()

            # Distribute rewards
            await self._distribute_rewards(user_id, achievement.achievement_id)

            # Send notification
            await self._send_achievement_notification(
                user_id, achievement.achievement_id
            )

        progress.last_updated = datetime.utcnow()

        # Save progress
        await self._save_user_progress(user_id, progress)

    async def _calculate_progress_delta(
        self,
        achievement: AchievementDefinition,
        event_name: str,
        event_data: dict[str, Any],
        current_progress: UserProgress,
    ) -> int:
        """Calculate how much progress should be added for an event."""
        # Get event rules from achievement conditions
        event_rules = achievement.conditions.get("event_rules", {})
        rule = event_rules.get(event_name, {})

        # Default delta
        delta = rule.get("delta", 1)

        # Apply conditions
        conditions = rule.get("conditions", {})
        for condition_key, condition_value in conditions.items():
            if condition_key in event_data:
                if event_data[condition_key] != condition_value:
                    return 0  # Condition not met

        # Apply multipliers
        multiplier = rule.get("multiplier", 1)
        if "multiplier_field" in rule and rule["multiplier_field"] in event_data:
            multiplier = event_data[rule["multiplier_field"]]

        return int(delta * multiplier)

    async def _get_user_progress(
        self, user_id: str, achievement_id: str
    ) -> UserProgress:
        """Get user progress for an achievement."""
        # Check cache first
        if (
            user_id in self.user_progress
            and achievement_id in self.user_progress[user_id]
        ):
            return self.user_progress[user_id][achievement_id]

        # Load from database
        progress = await self._load_user_progress_from_db(user_id, achievement_id)

        if not progress:
            # Create new progress
            achievement = self.achievements[achievement_id]
            progress = UserProgress(
                user_id=user_id,
                achievement_id=achievement_id,
                target_value=achievement.target_value or 1,
            )

        # Cache progress
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {}
        self.user_progress[user_id][achievement_id] = progress

        return progress

    async def _save_user_progress(self, user_id: str, progress: UserProgress):
        """Save user progress to database and cache."""
        # Update cache
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {}
        self.user_progress[user_id][progress.achievement_id] = progress

        # Save to database
        await self._save_user_progress_to_db(progress)

        # Update Redis cache
        if self.redis_pool:
            progress_key = f"achievements:progress:{user_id}:{progress.achievement_id}"
            progress_data = {
                "current_value": progress.current_value,
                "progress_percentage": progress.progress_percentage,
                "is_completed": progress.is_completed,
                "completed_at": (
                    progress.completed_at.isoformat() if progress.completed_at else None
                ),
                "last_updated": progress.last_updated.isoformat(),
            }
            await self.redis_pool.redis_client.hset(progress_key, mapping=progress_data)
            await self.redis_pool.redis_client.expire(progress_key, 86400)  # 24 hours

    async def _distribute_rewards(self, user_id: str, achievement_id: str):
        """Distribute rewards for completed achievement."""
        achievement = self.achievements.get(achievement_id)
        if not achievement or not achievement.rewards:
            return

        for reward_type, reward_value in achievement.rewards.items():
            await self._apply_reward(user_id, reward_type, reward_value, achievement_id)

    async def _apply_reward(
        self, user_id: str, reward_type: str, reward_value: Any, achievement_id: str
    ):
        """Apply a specific reward to a user."""
        if reward_type == "points":
            # Add points to user's total
            await self._add_user_points(user_id, reward_value)
        elif reward_type == "badge":
            # Grant badge to user
            await self._grant_badge(user_id, reward_value)
        elif reward_type == "title":
            # Grant title to user
            await self._grant_title(user_id, reward_value)
        elif reward_type == "unlock":
            # Unlock feature or content
            await self._unlock_feature(user_id, reward_value)

        logger.info(f"Reward applied: {reward_type}={reward_value} to user {user_id}")

    async def _send_achievement_notification(self, user_id: str, achievement_id: str):
        """Send notification for completed achievement."""
        achievement = self.achievements.get(achievement_id)
        if not achievement:
            return

        # This would integrate with the notification service

        logger.info(
            f"Achievement notification sent for {achievement_id} to user {user_id}"
        )

    async def _update_leaderboards(self, user_id: str):
        """Update leaderboards with user's latest achievements."""
        if not self.redis_pool:
            return

        # Calculate user's total score
        user_stats = await self.get_user_stats(user_id)

        # Update global leaderboard
        await self.redis_pool.redis_client.zadd(
            "achievements:leaderboard:global", {user_id: user_stats["total_points"]}
        )

        # Update category leaderboards
        for category in AchievementType:
            category_points = await self._calculate_category_points(user_id, category)
            await self.redis_pool.redis_client.zadd(
                f"achievements:leaderboard:{category.value}", {user_id: category_points}
            )

    async def _load_achievement_definitions(self):
        """Load achievement definitions from database or configuration."""
        # Default achievement definitions
        self.achievements = {
            "first_draft_pick": AchievementDefinition(
                achievement_id="first_draft_pick",
                name="First Pick",
                description="Make your first draft pick",
                category=AchievementType.DRAFT,
                rarity=AchievementRarity.COMMON,
                progress_type=ProgressType.BOOLEAN,
                target_value=1,
                conditions={
                    "trigger_events": ["draft_pick"],
                    "event_rules": {"draft_pick": {"delta": 1}},
                },
                rewards={"points": 10},
                points_value=10,
            ),
            "draft_master": AchievementDefinition(
                achievement_id="draft_master",
                name="Draft Master",
                description="Complete 10 drafts",
                category=AchievementType.DRAFT,
                rarity=AchievementRarity.RARE,
                progress_type=ProgressType.COUNTER,
                target_value=10,
                conditions={
                    "trigger_events": ["draft_completed"],
                    "event_rules": {"draft_completed": {"delta": 1}},
                },
                rewards={"points": 100, "badge": "draft_master"},
                points_value=100,
            ),
            "trade_shark": AchievementDefinition(
                achievement_id="trade_shark",
                name="Trade Shark",
                description="Complete 25 successful trades",
                category=AchievementType.TRADING,
                rarity=AchievementRarity.EPIC,
                progress_type=ProgressType.COUNTER,
                target_value=25,
                conditions={
                    "trigger_events": ["trade_completed"],
                    "event_rules": {"trade_completed": {"delta": 1}},
                },
                rewards={"points": 250, "title": "Trade Shark"},
                points_value=250,
            ),
            "perfect_week": AchievementDefinition(
                achievement_id="perfect_week",
                name="Perfect Week",
                description="Score the highest points in your league for a week",
                category=AchievementType.SCORING,
                rarity=AchievementRarity.UNCOMMON,
                progress_type=ProgressType.BOOLEAN,
                target_value=1,
                conditions={
                    "trigger_events": ["weekly_scoring_complete"],
                    "event_rules": {
                        "weekly_scoring_complete": {
                            "delta": 1,
                            "conditions": {"rank": 1},
                        }
                    },
                },
                rewards={"points": 50},
                points_value=50,
                is_repeatable=True,
            ),
            "social_butterfly": AchievementDefinition(
                achievement_id="social_butterfly",
                name="Social Butterfly",
                description="Send 100 messages in league chat",
                category=AchievementType.SOCIAL,
                rarity=AchievementRarity.COMMON,
                progress_type=ProgressType.COUNTER,
                target_value=100,
                conditions={
                    "trigger_events": ["chat_message_sent"],
                    "event_rules": {"chat_message_sent": {"delta": 1}},
                },
                rewards={"points": 25},
                points_value=25,
            ),
            "champion": AchievementDefinition(
                achievement_id="champion",
                name="Champion",
                description="Win a league championship",
                category=AchievementType.LEAGUE,
                rarity=AchievementRarity.LEGENDARY,
                progress_type=ProgressType.COUNTER,
                target_value=1,
                conditions={
                    "trigger_events": ["league_won"],
                    "event_rules": {"league_won": {"delta": 1}},
                },
                rewards={"points": 500, "badge": "champion", "title": "Champion"},
                points_value=500,
                is_repeatable=True,
            ),
        }

        logger.info(f"Loaded {len(self.achievements)} achievement definitions")

    async def _setup_event_listeners(self):
        """Setup event listeners for achievement tracking."""
        # This would register with the event system

    async def _load_user_progress_cache(self):
        """Load frequently accessed user progress from Redis."""
        if not self.redis_pool:
            return

        # Load top users' progress for better performance

    def _validate_achievement_definition(
        self, definition: AchievementDefinition
    ) -> bool:
        """Validate achievement definition."""
        if not definition.achievement_id or not definition.name:
            return False

        return not (definition.target_value is not None and definition.target_value <= 0)

    async def _store_achievement_definition(self, definition: AchievementDefinition):
        """Store achievement definition in database."""
        # This would save to the Achievement table

    async def _load_user_progress_from_db(
        self, user_id: str, achievement_id: str
    ) -> UserProgress | None:
        """Load user progress from database."""
        # This would query the UserAchievement table
        return None

    async def _save_user_progress_to_db(self, progress: UserProgress):
        """Save user progress to database."""
        # This would save to the UserAchievement table

    async def _get_redis_leaderboard(
        self, category: AchievementType | None, limit: int, league_id: str | None
    ) -> list[LeaderboardEntry]:
        """Get leaderboard from Redis."""
        leaderboard_key = (
            f"achievements:leaderboard:{category.value if category else 'global'}"
        )

        # Get top users
        top_users = await self.redis_pool.redis_client.zrevrange(
            leaderboard_key, 0, limit - 1, withscores=True
        )

        entries = []
        for rank, (user_id, score) in enumerate(top_users, 1):
            user_id = user_id.decode() if isinstance(user_id, bytes) else user_id

            # Get user info
            user_info = await self._get_user_info(user_id)
            user_stats = await self.get_user_stats(user_id)

            entry = LeaderboardEntry(
                user_id=user_id,
                username=user_info.get("username", "Unknown"),
                score=int(score),
                rank=rank,
                achievements_count=user_stats["completed_achievements"],
                rare_achievements=user_stats["rarity_breakdown"].get("rare", 0),
                total_points=user_stats["total_points"],
                avatar_url=user_info.get("avatar_url"),
            )
            entries.append(entry)

        return entries

    async def _get_db_leaderboard(
        self, category: AchievementType | None, limit: int, league_id: str | None
    ) -> list[LeaderboardEntry]:
        """Get leaderboard from database."""
        # This would query the database for top users
        return []

    async def _get_user_rank(self, user_id: str) -> int:
        """Get user's rank in global leaderboard."""
        if not self.redis_pool:
            return 0

        rank = await self.redis_pool.redis_client.zrevrank(
            "achievements:leaderboard:global", user_id
        )
        return (rank + 1) if rank is not None else 0

    async def _calculate_category_points(
        self, user_id: str, category: AchievementType
    ) -> int:
        """Calculate user's points in a specific category."""
        total_points = 0

        for achievement_id, achievement in self.achievements.items():
            if achievement.category == category:
                progress = await self._get_user_progress(user_id, achievement_id)
                if progress.is_completed:
                    total_points += achievement.points_value

        return total_points

    async def _get_user_info(self, user_id: str) -> dict[str, Any]:
        """Get user information."""
        # This would query the User table
        return {"username": f"User{user_id[-4:]}", "avatar_url": None}

    async def _add_user_points(self, user_id: str, points: int):
        """Add points to user's total."""
        if self.redis_pool:
            await self.redis_pool.redis_client.zincrby(
                "achievements:user_points", points, user_id
            )

    async def _grant_badge(self, user_id: str, badge_id: str):
        """Grant badge to user."""
        if self.redis_pool:
            await self.redis_pool.redis_client.sadd(
                f"achievements:badges:{user_id}", badge_id
            )

    async def _grant_title(self, user_id: str, title: str):
        """Grant title to user."""
        if self.redis_pool:
            await self.redis_pool.redis_client.set(
                f"achievements:title:{user_id}", title
            )

    async def _unlock_feature(self, user_id: str, feature: str):
        """Unlock feature for user."""
        if self.redis_pool:
            await self.redis_pool.redis_client.sadd(
                f"achievements:unlocks:{user_id}", feature
            )


# Global service instance
_achievement_service: AchievementService | None = None


async def get_achievement_service(db_session: AsyncSession) -> AchievementService:
    """Get achievement service instance."""
    global _achievement_service

    if _achievement_service is None:
        redis_pool = None
        if get_redis_pool:
            with contextlib.suppress(Exception):
                redis_pool = await get_redis_pool()

        _achievement_service = AchievementService(db_session, redis_pool)
        await _achievement_service.initialize()

    return _achievement_service
