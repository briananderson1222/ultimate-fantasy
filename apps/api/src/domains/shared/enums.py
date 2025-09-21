"""
Shared enums used across multiple domains.

This module centralizes common enums to avoid duplication and ensure consistency
across the fantasy sports platform.
"""

from enum import Enum


class ScoringType(Enum):
    """Scoring calculation types for fantasy point calculations."""
    GAME = "game"
    WEEKLY = "weekly"
    SEASON = "season"


class DataProvider(Enum):
    """Supported sports data providers for external API integration."""
    ESPN = "espn"
    THE_ATHLETIC = "the_athletic"
    MOCK = "mock"  # For testing


class SportType(Enum):
    """Supported sports types across the platform."""
    MLB = "mlb"
    NFL = "nfl"
    WNBA = "wnba"


class LeagueType(Enum):
    """League format types."""
    HEAD_TO_HEAD = "head_to_head"
    ROTISSERIE = "rotisserie"


class LeagueStatus(Enum):
    """League lifecycle status."""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    SUSPENDED = "suspended"


class DraftStatus(Enum):
    """Draft status enumeration."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TeamStatus(Enum):
    """Team status within a league."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ELIMINATED = "eliminated"


class TransactionType(Enum):
    """Types of player transactions."""
    TRADE = "trade"
    WAIVER_CLAIM = "waiver_claim"
    FREE_AGENT_PICKUP = "free_agent_pickup"
    DROP = "drop"
    DRAFT_PICK = "draft_pick"


class PlayerStatus(Enum):
    """Player availability status."""
    HEALTHY = "healthy"
    QUESTIONABLE = "questionable"
    DOUBTFUL = "doubtful"
    OUT = "out"
    INJURED_RESERVE = "ir"


class LineupStatus(Enum):
    """Lineup validation and lock status."""
    VALID = "valid"
    INVALID = "invalid"
    LOCKED = "locked"
    UNLOCKED = "unlocked"


class EventType(Enum):
    """Domain event types for event publishing."""
    PLAYER_STATS_UPDATED = "player_stats_updated"
    LINEUP_SUBMITTED = "lineup_submitted"
    TRADE_PROPOSED = "trade_proposed"
    TRADE_ACCEPTED = "trade_accepted"
    DRAFT_PICK_MADE = "draft_pick_made"
    SCORING_CALCULATED = "scoring_calculated"
    WAIVER_PROCESSED = "waiver_processed"


class CacheKeyPrefix(Enum):
    """Standard cache key prefixes for Redis operations."""
    SPORTS_DATA = "sports"
    PLAYER_STATS = "player_stats"
    LINEUP_DATA = "lineup"
    SCORING_DATA = "scoring"
    DRAFT_DATA = "draft"
    LEAGUE_DATA = "league"