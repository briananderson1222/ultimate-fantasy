"""
Consolidated SportsDataService with multi-provider support and comprehensive API integration.

Combines legacy functionality with domain architecture:
- Multi-provider support (ESPN, The Athletic, Mock)
- Data normalization and caching
- Player statistics and projections
- Injury status tracking
- Team and schedule data
- Database synchronization
- Provider fallback mechanisms
"""

import asyncio
try:
    import aiohttp
except ImportError:  # pragma: no cover - optional dependency not always installed
    aiohttp = None  # type: ignore[assignment]
import logging
import uuid as _uuid
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Protocol, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
import json

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore[assignment]
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from domains.sports.models.player import Player
from domains.scoring.models.score import Score
try:
    from infrastructure.cache.redis_pool import FantasyRedisPool, get_redis_pool
except ImportError:
    FantasyRedisPool = None  # type: ignore[misc,assignment]
    get_redis_pool = None  # type: ignore[misc,assignment]

try:
    from infrastructure.observability.tracing import get_tracer, trace_fantasy_operation
except ImportError:
    class MockSpan:
        def set_attribute(self, key, value):
            pass

    class MockTracer:
        def span(self, name, **kwargs):
            return MockSpan()

    def get_tracer():  # type: ignore[misc]
        return MockTracer()

    def trace_fantasy_operation(tracer, name, **kwargs):  # type: ignore[misc]
        from contextlib import contextmanager

        @contextmanager
        def mock_trace():
            yield MockSpan()

        return mock_trace()

try:
    from infrastructure.database.session_factory import get_db_session
except ImportError:
    get_db_session = None  # type: ignore[misc,assignment]

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging
    get_logger = logging.getLogger  # type: ignore[assignment]


logger = get_logger(__name__)
tracer = get_tracer()


class DataProvider(Enum):
    """Supported sports data providers"""
    ESPN = "espn"
    THE_ATHLETIC = "the_athletic"
    MOCK = "mock"  # For testing


class SportType(Enum):
    """Supported sports"""
    MLB = "mlb"
    NFL = "nfl"
    WNBA = "wnba"


@dataclass
class PlayerData:
    """Normalized player data structure"""
    external_id: str
    name: str
    position: str
    team_id: str
    sport: str
    injury_status: str = "healthy"
    injury_description: Optional[str] = None
    season_stats: Optional[Dict[str, Any]] = None
    game_stats: Optional[Dict[str, Any]] = None
    projections: Optional[Dict[str, Any]] = None


@dataclass
class GameData:
    """Game/match information"""
    game_id: str
    home_team: str
    away_team: str
    game_date: date
    sport: str
    status: str = "scheduled"  # scheduled, in_progress, completed
    scores: Optional[Dict[str, int]] = None


@dataclass
class StatUpdate:
    """Player statistics update"""
    player_external_id: str
    game_id: str
    game_date: date
    stats: Dict[str, Any]
    is_final: bool = False


@dataclass
class PlayerStats:
    """Standardized player statistics."""
    player_id: str
    external_id: str
    season: str
    week: Optional[int]
    games_played: int
    stats: Dict[str, Union[int, float]]
    fantasy_points: float
    position: str
    team: str


@dataclass
class PlayerProjection:
    """Player performance projections."""
    player_id: str
    week: int
    season: str
    projected_stats: Dict[str, float]
    projected_fantasy_points: float
    confidence: float
    last_updated: datetime


@dataclass
class InjuryReport:
    """Player injury information."""
    player_id: str
    status: str  # healthy, questionable, doubtful, out, ir
    description: Optional[str]
    return_date: Optional[datetime]
    severity: str  # low, medium, high
    last_updated: datetime


class SportsDataServiceError(Exception):
    """Base exception for sports data service errors"""
    pass


class ProviderError(SportsDataServiceError):
    """External provider API errors"""
    pass


class DataValidationError(SportsDataServiceError):
    """Data validation errors"""
    pass


class SportsDataProvider(Protocol):
    """Protocol for sports data providers."""

    @abstractmethod
    async def get_players(
        self,
        sport: str = "NFL",
        position: Optional[str] = None,
        team: Optional[str] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get players data."""
        ...

    @abstractmethod
    async def get_player_stats(
        self,
        player_id: str,
        season: str,
        week: Optional[int] = None
    ) -> Optional[PlayerStats]:
        """Get player statistics."""
        ...

    @abstractmethod
    async def get_player_projections(
        self,
        player_id: str,
        week: int,
        season: str
    ) -> Optional[PlayerProjection]:
        """Get player projections."""
        ...

    @abstractmethod
    async def get_injury_report(
        self,
        player_id: Optional[str] = None,
        team: Optional[str] = None
    ) -> List[InjuryReport]:
        """Get injury reports."""
        ...

    @abstractmethod
    async def get_teams(self, sport: str = "NFL") -> List[Dict[str, Any]]:
        """Get teams data."""
        ...

    @abstractmethod
    async def get_schedule(
        self,
        season: str,
        week: Optional[int] = None,
        team: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get schedule data."""
        ...


class MockSportsDataProvider:
    """Mock provider for development and testing."""

    async def get_players(
        self,
        sport: str = "NFL",
        position: Optional[str] = None,
        team: Optional[str] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Return mock player data."""
        mock_players = [
            {
                "player_id": "mock_player_1",
                "external_id": "nfl_12345",
                "name": "Patrick Mahomes",
                "position": "QB",
                "team": "KC",
                "sport": "NFL",
                "status": "active",
                "injury_status": "healthy"
            },
            {
                "player_id": "mock_player_2",
                "external_id": "nfl_12346",
                "name": "Josh Allen",
                "position": "QB",
                "team": "BUF",
                "sport": "NFL",
                "status": "active",
                "injury_status": "healthy"
            },
            {
                "player_id": "mock_player_3",
                "external_id": "nfl_12347",
                "name": "Derrick Henry",
                "position": "RB",
                "team": "TEN",
                "sport": "NFL",
                "status": "active",
                "injury_status": "questionable"
            }
        ]

        # Apply filters
        filtered_players = mock_players
        if position:
            filtered_players = [p for p in filtered_players if p["position"] == position]
        if team:
            filtered_players = [p for p in filtered_players if p["team"] == team]

        return filtered_players

    async def get_player_stats(
        self,
        player_id: str,
        season: str,
        week: Optional[int] = None
    ) -> Optional[PlayerStats]:
        """Return mock player stats."""
        return PlayerStats(
            player_id=player_id,
            external_id=f"nfl_{player_id[-5:]}",
            season=season,
            week=week,
            games_played=16 if week is None else 1,
            stats={
                "passing_yards": 4500,
                "passing_tds": 35,
                "interceptions": 8,
                "rushing_yards": 250,
                "rushing_tds": 3
            },
            fantasy_points=285.5,
            position="QB",
            team="KC"
        )

    async def get_player_projections(
        self,
        player_id: str,
        week: int,
        season: str
    ) -> Optional[PlayerProjection]:
        """Return mock projections."""
        return PlayerProjection(
            player_id=player_id,
            week=week,
            season=season,
            projected_stats={
                "passing_yards": 275.0,
                "passing_tds": 2.1,
                "interceptions": 0.8,
                "rushing_yards": 15.0,
                "rushing_tds": 0.3
            },
            projected_fantasy_points=18.5,
            confidence=0.85,
            last_updated=datetime.utcnow()
        )

    async def get_injury_report(
        self,
        player_id: Optional[str] = None,
        team: Optional[str] = None
    ) -> List[InjuryReport]:
        """Return mock injury data."""
        return [
            InjuryReport(
                player_id="mock_player_3",
                status="questionable",
                description="Ankle sprain",
                return_date=None,
                severity="medium",
                last_updated=datetime.utcnow()
            )
        ]

    async def get_teams(self, sport: str = "NFL") -> List[Dict[str, Any]]:
        """Return mock teams."""
        return [
            {
                "team_id": "KC",
                "name": "Kansas City Chiefs",
                "city": "Kansas City",
                "abbreviation": "KC",
                "conference": "AFC",
                "division": "West",
                "sport": sport
            },
            {
                "team_id": "BUF",
                "name": "Buffalo Bills",
                "city": "Buffalo",
                "abbreviation": "BUF",
                "conference": "AFC",
                "division": "East",
                "sport": sport
            }
        ]

    async def get_schedule(
        self,
        season: str,
        week: Optional[int] = None,
        team: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Return mock schedule."""
        return [
            {
                "game_id": "game_123",
                "home_team": "KC",
                "away_team": "BUF",
                "game_date": "2024-01-21",
                "game_time": "15:30:00",
                "status": "scheduled",
                "week": week or 1,
                "season": season
            }
        ]


class SportsDataService:
    """
    Service for aggregating and managing sports data from multiple providers.

    Features:
    - Multi-provider support with fallback
    - Intelligent caching with TTL
    - Data normalization across providers
    - Rate limiting and error handling
    - Real-time injury updates
    """

    def __init__(
        self,
        primary_provider: DataProvider = DataProvider.ESPN,
        providers: List[SportsDataProvider] = None,
        redis_pool: Optional[FantasyRedisPool] = None,
        default_cache_ttl: int = 300
    ):
        """
        Initialize sports data service.

        Args:
            primary_provider: Primary data provider to use
            providers: List of data providers (defaults to mock)
            redis_pool: Redis connection pool for caching
            default_cache_ttl: Default cache TTL in seconds
        """
        self.primary_provider = primary_provider
        self.fallback_providers = [DataProvider.THE_ATHLETIC, DataProvider.MOCK]
        self.session_timeout = 30
        self.retry_attempts = 3
        self.providers = providers or [MockSportsDataProvider()]
        self.redis_pool = redis_pool
        self.default_cache_ttl = default_cache_ttl

        # Provider configurations
        self.provider_configs = {
            DataProvider.ESPN: {
                "base_url": "https://site.api.espn.com/apis/site/v2/sports",
                "rate_limit": 100,  # requests per minute
                "requires_auth": False
            },
            DataProvider.THE_ATHLETIC: {
                "base_url": "https://api.theathletic.com/v1",
                "rate_limit": 60,
                "requires_auth": True
            },
            DataProvider.MOCK: {
                "base_url": "https://mock-sports-api.example.com",
                "rate_limit": 1000,
                "requires_auth": False
            }
        }

        # Cache TTL for different data types
        self.cache_ttl = {
            "players": 3600,        # 1 hour
            "player_stats": 300,    # 5 minutes
            "projections": 1800,    # 30 minutes
            "injuries": 300,        # 5 minutes
            "teams": 86400,         # 24 hours
            "schedule": 3600        # 1 hour
        }

    async def get_players(
        self,
        sport: str = "NFL",
        position: Optional[str] = None,
        team: Optional[str] = None,
        active_only: bool = True,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get players data with caching and multi-provider support.

        Args:
            sport: Sport type (NFL, NBA, etc.)
            position: Filter by position
            team: Filter by team
            active_only: Only active players
            use_cache: Whether to use cached data

        Returns:
            List of player dictionaries
        """
        with trace_fantasy_operation(
            tracer, "get_players",
            sport=sport, position=position, team=team
        ) as span:
            # Build cache key
            cache_key = f"players:{sport}:{position or 'all'}:{team or 'all'}:{active_only}"

            # Try cache first
            if use_cache and self.redis_pool:
                cached_data = await self.redis_pool.get("sports", cache_key)
                if cached_data:
                    span.set_attribute("cache_hit", True)
                    return cached_data

            # Try providers in order
            for i, provider in enumerate(self.providers):
                try:
                    span.set_attribute(f"provider_{i}_attempted", True)
                    players = await provider.get_players(sport, position, team, active_only)

                    # Cache successful result
                    if use_cache and self.redis_pool and players:
                        await self.redis_pool.set(
                            "sports", cache_key, players,
                            ttl=self.cache_ttl["players"]
                        )

                    span.set_attribute("players_count", len(players))
                    span.set_attribute("successful_provider", i)
                    return players

                except Exception as e:
                    logger.warning(f"Provider {i} failed for get_players: {e}")
                    span.set_attribute(f"provider_{i}_error", str(e))
                    continue

            # All providers failed
            logger.error("All providers failed for get_players")
            span.set_attribute("all_providers_failed", True)
            return []

    async def get_player_details(
        self,
        player_id: str,
        include_stats: bool = True,
        include_projections: bool = True,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive player details.

        Args:
            player_id: Player identifier
            include_stats: Include season statistics
            include_projections: Include projections
            use_cache: Whether to use cached data

        Returns:
            Player details dictionary or None
        """
        with trace_fantasy_operation(
            tracer, "get_player_details",
            player_id=player_id
        ) as span:
            cache_key = f"player_details:{player_id}:{include_stats}:{include_projections}"

            # Try cache first
            if use_cache and self.redis_pool:
                cached_data = await self.redis_pool.get("sports", cache_key)
                if cached_data:
                    span.set_attribute("cache_hit", True)
                    return cached_data

            # Get base player data
            players = await self.get_players(active_only=False, use_cache=use_cache)
            player = next((p for p in players if p["player_id"] == player_id), None)

            if not player:
                span.set_attribute("player_not_found", True)
                return None

            # Enhance with additional data
            enhanced_player = player.copy()

            if include_stats:
                stats = await self.get_player_stats(player_id, "2024", use_cache=use_cache)
                enhanced_player["season_stats"] = stats.__dict__ if stats else None

            if include_projections:
                projections = await self.get_player_projections(
                    player_id, 1, "2024", use_cache=use_cache
                )
                enhanced_player["projections"] = projections.__dict__ if projections else None

            # Get injury status
            injuries = await self.get_injury_report(player_id=player_id, use_cache=use_cache)
            enhanced_player["injury_details"] = injuries[0].__dict__ if injuries else None

            # Cache result
            if use_cache and self.redis_pool:
                await self.redis_pool.set(
                    "sports", cache_key, enhanced_player,
                    ttl=self.cache_ttl["players"]
                )

            span.set_attribute("enhanced_player_created", True)
            return enhanced_player

    async def get_player_stats(
        self,
        player_id: str,
        season: str,
        week: Optional[int] = None,
        use_cache: bool = True
    ) -> Optional[PlayerStats]:
        """Get player statistics."""
        with trace_fantasy_operation(
            tracer, "get_player_stats",
            player_id=player_id, season=season, week=week
        ) as span:
            cache_key = f"stats:{player_id}:{season}:{week or 'season'}"

            if use_cache and self.redis_pool:
                cached_data = await self.redis_pool.get("sports", cache_key)
                if cached_data:
                    return PlayerStats(**cached_data)

            for provider in self.providers:
                try:
                    stats = await provider.get_player_stats(player_id, season, week)
                    if stats and use_cache and self.redis_pool:
                        await self.redis_pool.set(
                            "sports", cache_key, stats.__dict__,
                            ttl=self.cache_ttl["player_stats"]
                        )
                    return stats
                except Exception as e:
                    logger.warning(f"Provider failed for get_player_stats: {e}")
                    continue

            return None

    async def get_player_projections(
        self,
        player_id: str,
        week: int,
        season: str,
        use_cache: bool = True
    ) -> Optional[PlayerProjection]:
        """Get player projections."""
        cache_key = f"projections:{player_id}:{season}:{week}"

        if use_cache and self.redis_pool:
            cached_data = await self.redis_pool.get("sports", cache_key)
            if cached_data:
                return PlayerProjection(**cached_data)

        for provider in self.providers:
            try:
                projections = await provider.get_player_projections(player_id, week, season)
                if projections and use_cache and self.redis_pool:
                    await self.redis_pool.set(
                        "sports", cache_key, projections.__dict__,
                        ttl=self.cache_ttl["projections"]
                    )
                return projections
            except Exception as e:
                logger.warning(f"Provider failed for get_player_projections: {e}")
                continue

        return None

    async def get_injury_report(
        self,
        player_id: Optional[str] = None,
        team: Optional[str] = None,
        use_cache: bool = True
    ) -> List[InjuryReport]:
        """Get injury reports."""
        cache_key = f"injuries:{player_id or 'all'}:{team or 'all'}"

        if use_cache and self.redis_pool:
            cached_data = await self.redis_pool.get("sports", cache_key)
            if cached_data:
                return [InjuryReport(**injury) for injury in cached_data]

        for provider in self.providers:
            try:
                injuries = await provider.get_injury_report(player_id, team)
                if injuries and use_cache and self.redis_pool:
                    injury_dicts = [injury.__dict__ for injury in injuries]
                    await self.redis_pool.set(
                        "sports", cache_key, injury_dicts,
                        ttl=self.cache_ttl["injuries"]
                    )
                return injuries
            except Exception as e:
                logger.warning(f"Provider failed for get_injury_report: {e}")
                continue

        return []

    async def get_teams(
        self,
        sport: str = "NFL",
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Get teams data."""
        cache_key = f"teams:{sport}"

        if use_cache and self.redis_pool:
            cached_data = await self.redis_pool.get("sports", cache_key)
            if cached_data:
                return cached_data

        for provider in self.providers:
            try:
                teams = await provider.get_teams(sport)
                if teams and use_cache and self.redis_pool:
                    await self.redis_pool.set(
                        "sports", cache_key, teams,
                        ttl=self.cache_ttl["teams"]
                    )
                return teams
            except Exception as e:
                logger.warning(f"Provider failed for get_teams: {e}")
                continue

        return []

    async def get_schedule(
        self,
        season: str,
        week: Optional[int] = None,
        team: Optional[str] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Get schedule data."""
        cache_key = f"schedule:{season}:{week or 'all'}:{team or 'all'}"

        if use_cache and self.redis_pool:
            cached_data = await self.redis_pool.get("sports", cache_key)
            if cached_data:
                return cached_data

        for provider in self.providers:
            try:
                schedule = await provider.get_schedule(season, week, team)
                if schedule and use_cache and self.redis_pool:
                    await self.redis_pool.set(
                        "sports", cache_key, schedule,
                        ttl=self.cache_ttl["schedule"]
                    )
                return schedule
            except Exception as e:
                logger.warning(f"Provider failed for get_schedule: {e}")
                continue

        return []

    async def search_players(
        self,
        query: str,
        sport: str = "NFL",
        limit: int = 20,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search players by name.

        Args:
            query: Search query
            sport: Sport type
            limit: Maximum results
            use_cache: Whether to use cached data

        Returns:
            List of matching players
        """
        players = await self.get_players(sport=sport, use_cache=use_cache)

        # Simple text search
        query_lower = query.lower()
        matching_players = [
            player for player in players
            if query_lower in player["name"].lower()
        ]

        return matching_players[:limit]

    async def invalidate_cache(
        self,
        cache_type: Optional[str] = None,
        player_id: Optional[str] = None
    ) -> int:
        """
        Invalidate cached data.

        Args:
            cache_type: Specific cache type to clear
            player_id: Specific player to clear

        Returns:
            Number of cache keys cleared
        """
        if not self.redis_pool:
            return 0

        if player_id:
            # Clear all cache for specific player
            pattern = f"sports:*{player_id}*"
        elif cache_type:
            # Clear specific cache type
            pattern = f"sports:{cache_type}:*"
        else:
            # Clear all sports cache
            pattern = "sports:*"

        keys = await self.redis_pool.get_keys_by_pattern(pattern)
        if keys:
            deleted = await self.redis_pool.redis_client.delete(*keys)
            logger.info(f"Invalidated {deleted} sports cache keys")
            return deleted

        return 0

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        if not self.redis_pool:
            return {"cache_enabled": False}

        # This would require additional tracking in real implementation
        return {
            "cache_enabled": True,
            "cache_ttl_config": self.cache_ttl,
            "providers_count": len(self.providers)
        }

    # Legacy API methods for compatibility
    async def get_player_data(
        self,
        external_id: str,
        sport: SportType,
        provider: Optional[DataProvider] = None
    ) -> Optional[PlayerData]:
        """
        Get player data from external API

        Args:
            external_id: External player ID
            sport: Sport type
            provider: Optional specific provider to use

        Returns:
            PlayerData instance or None if not found

        Raises:
            ProviderError: API request failed
        """
        provider = provider or self.primary_provider

        try:
            if provider == DataProvider.ESPN:
                return await self._get_espn_player_data(external_id, sport)
            elif provider == DataProvider.THE_ATHLETIC:
                return await self._get_athletic_player_data(external_id, sport)
            elif provider == DataProvider.MOCK:
                return await self._get_mock_player_data(external_id, sport)
            else:
                raise ProviderError(f"Unsupported provider: {provider}")

        except Exception as e:
            logger.error(f"Failed to get player data from {provider}: {e}")

            # Try fallback providers
            for fallback_provider in self.fallback_providers:
                if fallback_provider != provider:
                    try:
                        return await self.get_player_data(external_id, sport, fallback_provider)
                    except Exception:
                        continue

            raise ProviderError(f"All providers failed for player {external_id}")

    async def search_players_by_provider(
        self,
        query: str,
        sport: SportType,
        limit: int = 20,
        provider: Optional[DataProvider] = None
    ) -> List[PlayerData]:
        """
        Search for players by name or team using specific provider

        Args:
            query: Search query
            sport: Sport type
            limit: Maximum results to return
            provider: Optional specific provider to use

        Returns:
            List of PlayerData instances
        """
        provider = provider or self.primary_provider

        try:
            if provider == DataProvider.ESPN:
                return await self._search_espn_players(query, sport, limit)
            elif provider == DataProvider.THE_ATHLETIC:
                return await self._search_athletic_players(query, sport, limit)
            elif provider == DataProvider.MOCK:
                return await self._search_mock_players(query, sport, limit)
            else:
                raise ProviderError(f"Unsupported provider: {provider}")

        except Exception as e:
            logger.error(f"Failed to search players with {provider}: {e}")
            raise ProviderError(f"Player search failed: {e}")

    async def get_team_roster(
        self,
        team_id: str,
        sport: SportType,
        provider: Optional[DataProvider] = None
    ) -> List[PlayerData]:
        """
        Get team roster

        Args:
            team_id: Team identifier
            sport: Sport type
            provider: Optional specific provider to use

        Returns:
            List of PlayerData instances for team roster
        """
        provider = provider or self.primary_provider

        try:
            if provider == DataProvider.ESPN:
                return await self._get_espn_team_roster(team_id, sport)
            elif provider == DataProvider.THE_ATHLETIC:
                return await self._get_athletic_team_roster(team_id, sport)
            elif provider == DataProvider.MOCK:
                return await self._get_mock_team_roster(team_id, sport)
            else:
                raise ProviderError(f"Unsupported provider: {provider}")

        except Exception as e:
            logger.error(f"Failed to get team roster from {provider}: {e}")
            raise ProviderError(f"Team roster fetch failed: {e}")

    async def get_games_schedule(
        self,
        sport: SportType,
        start_date: date,
        end_date: date,
        provider: Optional[DataProvider] = None
    ) -> List[GameData]:
        """
        Get games schedule for date range

        Args:
            sport: Sport type
            start_date: Start date
            end_date: End date
            provider: Optional specific provider to use

        Returns:
            List of GameData instances
        """
        provider = provider or self.primary_provider

        try:
            if provider == DataProvider.ESPN:
                return await self._get_espn_schedule(sport, start_date, end_date)
            elif provider == DataProvider.THE_ATHLETIC:
                return await self._get_athletic_schedule(sport, start_date, end_date)
            elif provider == DataProvider.MOCK:
                return await self._get_mock_schedule(sport, start_date, end_date)
            else:
                raise ProviderError(f"Unsupported provider: {provider}")

        except Exception as e:
            logger.error(f"Failed to get schedule from {provider}: {e}")
            raise ProviderError(f"Schedule fetch failed: {e}")

    async def get_live_scores(
        self,
        sport: SportType,
        game_date: Optional[date] = None,
        provider: Optional[DataProvider] = None
    ) -> List[Dict[str, Any]]:
        """
        Get live scores for games

        Args:
            sport: Sport type
            game_date: Optional specific date (defaults to today)
            provider: Optional specific provider to use

        Returns:
            List of score data dictionaries
        """
        provider = provider or self.primary_provider
        game_date = game_date or date.today()

        try:
            if provider == DataProvider.ESPN:
                return await self._get_espn_live_scores(sport, game_date)
            elif provider == DataProvider.THE_ATHLETIC:
                return await self._get_athletic_live_scores(sport, game_date)
            elif provider == DataProvider.MOCK:
                return await self._get_mock_live_scores(sport, game_date)
            else:
                raise ProviderError(f"Unsupported provider: {provider}")

        except Exception as e:
            logger.error(f"Failed to get live scores from {provider}: {e}")
            raise ProviderError(f"Live scores fetch failed: {e}")

    async def get_player_stats_by_provider(
        self,
        external_id: str,
        sport: SportType,
        season: str,
        stat_type: str = "season",
        provider: Optional[DataProvider] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get player statistics

        Args:
            external_id: External player ID
            sport: Sport type
            season: Season identifier (e.g., "2024")
            stat_type: Type of stats ("season", "game", "career")
            provider: Optional specific provider to use

        Returns:
            Statistics dictionary or None if not found
        """
        provider = provider or self.primary_provider

        try:
            if provider == DataProvider.ESPN:
                return await self._get_espn_player_stats(external_id, sport, season, stat_type)
            elif provider == DataProvider.THE_ATHLETIC:
                return await self._get_athletic_player_stats(external_id, sport, season, stat_type)
            elif provider == DataProvider.MOCK:
                return await self._get_mock_player_stats(external_id, sport, season, stat_type)
            else:
                raise ProviderError(f"Unsupported provider: {provider}")

        except Exception as e:
            logger.error(f"Failed to get player stats from {provider}: {e}")
            return None

    async def get_injury_reports(
        self,
        sport: SportType,
        team_id: Optional[str] = None,
        provider: Optional[DataProvider] = None
    ) -> List[Dict[str, Any]]:
        """
        Get injury reports

        Args:
            sport: Sport type
            team_id: Optional team filter
            provider: Optional specific provider to use

        Returns:
            List of injury report dictionaries
        """
        provider = provider or self.primary_provider

        try:
            if provider == DataProvider.ESPN:
                return await self._get_espn_injury_reports(sport, team_id)
            elif provider == DataProvider.THE_ATHLETIC:
                return await self._get_athletic_injury_reports(sport, team_id)
            elif provider == DataProvider.MOCK:
                return await self._get_mock_injury_reports(sport, team_id)
            else:
                raise ProviderError(f"Unsupported provider: {provider}")

        except Exception as e:
            logger.error(f"Failed to get injury reports from {provider}: {e}")
            return []

    async def sync_player_data(
        self,
        player_ids: List[str],
        sport: SportType,
        db: Optional[Session] = None
    ) -> Dict[str, bool]:
        """
        Synchronize player data with database

        Args:
            player_ids: List of external player IDs to sync
            sport: Sport type
            db: Optional database session

        Returns:
            Dictionary mapping player_id to success status
        """
        results = {}

        if db is None:
            if get_db_session is None:
                raise RuntimeError("Database session factory not available and no session provided")
            session_context = get_db_session()
        else:
            session_context = db

        with session_context as session:
            for player_id in player_ids:
                try:
                    # Get latest data from API
                    player_data = await self.get_player_data(player_id, sport)
                    if not player_data:
                        results[player_id] = False
                        continue

                    # Find or create player in database
                    player = session.query(Player).filter(
                        and_(
                            Player.external_id == player_id,
                            Player.sport == sport.value
                        )
                    ).first()

                    if player:
                        # Update existing player
                        player.name = player_data.name
                        player.position = player_data.position
                        player.team_id = player_data.team_id
                        player.injury_status = player_data.injury_status
                        player.injury_description = player_data.injury_description
                        player.season_stats = player_data.season_stats
                        player.game_stats = player_data.game_stats
                        player.projections = player_data.projections
                    else:
                        # Create new player
                        player = Player(
                            external_id=player_data.external_id,
                            name=player_data.name,
                            position=player_data.position,
                            team_id=player_data.team_id,
                            sport=player_data.sport,
                            injury_status=player_data.injury_status,
                            injury_description=player_data.injury_description,
                            season_stats=player_data.season_stats,
                            game_stats=player_data.game_stats,
                            projections=player_data.projections
                        )
                        session.add(player)

                    results[player_id] = True

                except Exception as e:
                    logger.error(f"Failed to sync player {player_id}: {e}")
                    results[player_id] = False

            session.commit()

        logger.info(f"Synced {sum(results.values())}/{len(player_ids)} players")
        return results

    def validate_player_data(self, data: Dict[str, Any]) -> PlayerData:
        """
        Validate and normalize player data

        Args:
            data: Raw player data from API

        Returns:
            Validated PlayerData instance

        Raises:
            DataValidationError: Invalid data format
        """
        try:
            # Extract required fields
            external_id = str(data.get("id", ""))
            name = str(data.get("name", "")).strip()
            position = str(data.get("position", "")).upper()
            team_id = str(data.get("team_id", "")).upper()
            sport = str(data.get("sport", "")).lower()

            # Validate required fields
            if not all([external_id, name, position, sport]):
                raise DataValidationError("Missing required player fields")

            # Validate sport
            if sport not in [s.value for s in SportType]:
                raise DataValidationError(f"Invalid sport: {sport}")

            # Normalize injury status
            injury_status = str(data.get("injury_status", "healthy")).lower()
            if injury_status not in ["healthy", "questionable", "doubtful", "out"]:
                injury_status = "healthy"

            return PlayerData(
                external_id=external_id,
                name=name,
                position=position,
                team_id=team_id,
                sport=sport,
                injury_status=injury_status,
                injury_description=data.get("injury_description"),
                season_stats=data.get("season_stats"),
                game_stats=data.get("game_stats"),
                projections=data.get("projections")
            )

        except Exception as e:
            raise DataValidationError(f"Player data validation failed: {e}")

    # Provider implementation methods
    async def _get_espn_player_data(self, external_id: str, sport: SportType) -> Optional[PlayerData]:
        """Get player data from ESPN API"""
        if not aiohttp:
            return await self._get_mock_player_data(external_id, sport)

        base_url = self.provider_configs[DataProvider.ESPN]["base_url"]
        url = f"{base_url}/{sport.value}/athletes/{external_id}"

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.session_timeout)) as session:
            async with session.get(url) as response:
                if response.status == 404:
                    return None
                response.raise_for_status()

                data = await response.json()

                # ESPN data structure adaptation
                athlete = data.get("athlete", {})
                return PlayerData(
                    external_id=str(athlete.get("id", external_id)),
                    name=athlete.get("displayName", ""),
                    position=athlete.get("position", {}).get("abbreviation", ""),
                    team_id=athlete.get("team", {}).get("abbreviation", ""),
                    sport=sport.value,
                    injury_status="healthy",  # ESPN injury data requires separate call
                    season_stats=athlete.get("statistics"),
                    projections=athlete.get("projections")
                )

    async def _search_espn_players(self, query: str, sport: SportType, limit: int) -> List[PlayerData]:
        """Search players via ESPN API"""
        # ESPN doesn't have a direct search API, so we'll implement a mock response
        return await self._search_mock_players(query, sport, limit)

    async def _get_espn_team_roster(self, team_id: str, sport: SportType) -> List[PlayerData]:
        """Get team roster from ESPN API"""
        if not aiohttp:
            return await self._get_mock_team_roster(team_id, sport)

        base_url = self.provider_configs[DataProvider.ESPN]["base_url"]
        url = f"{base_url}/{sport.value}/teams/{team_id}/roster"

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.session_timeout)) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()

                roster = []
                for athlete in data.get("athletes", []):
                    roster.append(PlayerData(
                        external_id=str(athlete.get("id", "")),
                        name=athlete.get("displayName", ""),
                        position=athlete.get("position", {}).get("abbreviation", ""),
                        team_id=team_id,
                        sport=sport.value
                    ))

                return roster

    async def _get_espn_schedule(self, sport: SportType, start_date: date, end_date: date) -> List[GameData]:
        """Get schedule from ESPN API"""
        if not aiohttp:
            return await self._get_mock_schedule(sport, start_date, end_date)

        base_url = self.provider_configs[DataProvider.ESPN]["base_url"]
        url = f"{base_url}/{sport.value}/scoreboard"

        games = []
        current_date = start_date

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.session_timeout)) as session:
            while current_date <= end_date:
                date_str = current_date.strftime("%Y%m%d")
                daily_url = f"{url}?dates={date_str}"

                try:
                    async with session.get(daily_url) as response:
                        response.raise_for_status()
                        data = await response.json()

                        for event in data.get("events", []):
                            competitions = event.get("competitions", [])
                            if competitions:
                                competition = competitions[0]
                                competitors = competition.get("competitors", [])

                                if len(competitors) >= 2:
                                    home_team = next((c for c in competitors if c.get("homeAway") == "home"), {})
                                    away_team = next((c for c in competitors if c.get("homeAway") == "away"), {})

                                    games.append(GameData(
                                        game_id=str(event.get("id", "")),
                                        home_team=home_team.get("team", {}).get("abbreviation", ""),
                                        away_team=away_team.get("team", {}).get("abbreviation", ""),
                                        game_date=current_date,
                                        sport=sport.value,
                                        status=event.get("status", {}).get("type", {}).get("name", "scheduled")
                                    ))

                except Exception as e:
                    logger.warning(f"Failed to get ESPN schedule for {current_date}: {e}")

                current_date += timedelta(days=1)

        return games

    async def _get_espn_live_scores(self, sport: SportType, game_date: date) -> List[Dict[str, Any]]:
        """Get live scores from ESPN API"""
        if not aiohttp:
            return await self._get_mock_live_scores(sport, game_date)

        base_url = self.provider_configs[DataProvider.ESPN]["base_url"]
        date_str = game_date.strftime("%Y%m%d")
        url = f"{base_url}/{sport.value}/scoreboard?dates={date_str}"

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.session_timeout)) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()

                scores = []
                for event in data.get("events", []):
                    competitions = event.get("competitions", [])
                    if competitions:
                        competition = competitions[0]
                        scores.append({
                            "game_id": str(event.get("id", "")),
                            "status": event.get("status", {}).get("type", {}).get("name", ""),
                            "competitors": competition.get("competitors", []),
                            "last_updated": datetime.utcnow().isoformat()
                        })

                return scores

    async def _get_espn_player_stats(self, external_id: str, sport: SportType, season: str, stat_type: str) -> Optional[Dict[str, Any]]:
        """Get player stats from ESPN API"""
        # ESPN stats API requires complex navigation, implementing mock for now
        return await self._get_mock_player_stats(external_id, sport, season, stat_type)

    async def _get_espn_injury_reports(self, sport: SportType, team_id: Optional[str]) -> List[Dict[str, Any]]:
        """Get injury reports from ESPN API"""
        # ESPN injury reports require separate endpoint, implementing mock for now
        return await self._get_mock_injury_reports(sport, team_id)

    # Mock provider methods
    async def _get_mock_player_data(self, external_id: str, sport: SportType) -> Optional[PlayerData]:
        """Mock player data for testing"""
        # Generate consistent mock data based on ID
        import hashlib
        hash_obj = hashlib.md5(external_id.encode())
        hash_hex = hash_obj.hexdigest()

        positions_by_sport = {
            SportType.MLB: ["C", "1B", "2B", "3B", "SS", "OF", "P"],
            SportType.NFL: ["QB", "RB", "WR", "TE", "K", "DEF"],
            SportType.WNBA: ["PG", "SG", "SF", "PF", "C"]
        }

        teams_by_sport = {
            SportType.MLB: ["LAA", "HOU", "NYY", "TB", "BOS"],
            SportType.NFL: ["BUF", "MIA", "NE", "NYJ", "BAL"],
            SportType.WNBA: ["LAS", "NY", "CON", "IND", "ATL"]
        }

        position_idx = int(hash_hex[:2], 16) % len(positions_by_sport[sport])
        team_idx = int(hash_hex[2:4], 16) % len(teams_by_sport[sport])

        return PlayerData(
            external_id=external_id,
            name=f"Mock Player {external_id[-4:]}",
            position=positions_by_sport[sport][position_idx],
            team_id=teams_by_sport[sport][team_idx],
            sport=sport.value,
            injury_status="healthy",
            season_stats={"games": 50, "points": 15.5},
            projections={"fantasy_points": 18.2}
        )

    async def _search_mock_players(self, query: str, sport: SportType, limit: int) -> List[PlayerData]:
        """Mock player search for testing"""
        players = []
        for i in range(min(limit, 10)):
            external_id = f"mock_{sport.value}_{query}_{i}"
            player_data = await self._get_mock_player_data(external_id, sport)
            if player_data:
                player_data.name = f"{query} Player {i+1}"
                players.append(player_data)
        return players

    async def _get_mock_team_roster(self, team_id: str, sport: SportType) -> List[PlayerData]:
        """Mock team roster for testing"""
        roster = []
        for i in range(25):  # Mock roster size
            external_id = f"mock_{sport.value}_{team_id}_{i}"
            player_data = await self._get_mock_player_data(external_id, sport)
            if player_data:
                player_data.team_id = team_id
                roster.append(player_data)
        return roster

    async def _get_mock_schedule(self, sport: SportType, start_date: date, end_date: date) -> List[GameData]:
        """Mock schedule for testing"""
        games = []
        current_date = start_date
        game_id = 1

        while current_date <= end_date:
            # Generate 2-5 games per day
            for i in range(2, 6):
                games.append(GameData(
                    game_id=f"mock_game_{game_id}",
                    home_team=f"TEAM{i}",
                    away_team=f"TEAM{i+1}",
                    game_date=current_date,
                    sport=sport.value
                ))
                game_id += 1

            current_date += timedelta(days=1)

        return games

    async def _get_mock_live_scores(self, sport: SportType, game_date: date) -> List[Dict[str, Any]]:
        """Mock live scores for testing"""
        return [
            {
                "game_id": "mock_game_1",
                "status": "in_progress",
                "home_score": 7,
                "away_score": 3,
                "period": "3rd Quarter",
                "time_remaining": "10:45"
            },
            {
                "game_id": "mock_game_2",
                "status": "completed",
                "home_score": 21,
                "away_score": 14,
                "final": True
            }
        ]

    async def _get_mock_player_stats(self, external_id: str, sport: SportType, season: str, stat_type: str) -> Optional[Dict[str, Any]]:
        """Mock player stats for testing"""
        if sport == SportType.MLB:
            return {
                "batting": {"avg": 0.285, "hr": 25, "rbi": 85, "runs": 78},
                "pitching": {"era": 3.45, "wins": 12, "saves": 5, "strikeouts": 150}
            }
        elif sport == SportType.NFL:
            return {
                "passing": {"yards": 3500, "touchdowns": 28, "interceptions": 10},
                "rushing": {"yards": 1200, "touchdowns": 8, "attempts": 250},
                "receiving": {"yards": 900, "touchdowns": 6, "receptions": 65}
            }
        elif sport == SportType.WNBA:
            return {
                "points": 18.5, "rebounds": 7.2, "assists": 5.8, "steals": 1.8, "blocks": 1.1
            }

        return None

    async def _get_mock_injury_reports(self, sport: SportType, team_id: Optional[str]) -> List[Dict[str, Any]]:
        """Mock injury reports for testing"""
        return [
            {
                "player_id": "mock_injured_1",
                "player_name": "Mock Player 1",
                "injury_status": "questionable",
                "injury_description": "Knee soreness",
                "expected_return": (date.today() + timedelta(days=3)).isoformat()
            },
            {
                "player_id": "mock_injured_2",
                "player_name": "Mock Player 2",
                "injury_status": "out",
                "injury_description": "Ankle sprain",
                "expected_return": (date.today() + timedelta(days=14)).isoformat()
            }
        ]

    # The Athletic Provider Methods (stubs for future implementation)
    async def _get_athletic_player_data(self, external_id: str, sport: SportType) -> Optional[PlayerData]:
        """Get player data from The Athletic API (future implementation)"""
        return await self._get_mock_player_data(external_id, sport)

    async def _search_athletic_players(self, query: str, sport: SportType, limit: int) -> List[PlayerData]:
        """Search players via The Athletic API (future implementation)"""
        return await self._search_mock_players(query, sport, limit)

    async def _get_athletic_team_roster(self, team_id: str, sport: SportType) -> List[PlayerData]:
        """Get team roster from The Athletic API (future implementation)"""
        return await self._get_mock_team_roster(team_id, sport)

    async def _get_athletic_schedule(self, sport: SportType, start_date: date, end_date: date) -> List[GameData]:
        """Get schedule from The Athletic API (future implementation)"""
        return await self._get_mock_schedule(sport, start_date, end_date)

    async def _get_athletic_live_scores(self, sport: SportType, game_date: date) -> List[Dict[str, Any]]:
        """Get live scores from The Athletic API (future implementation)"""
        return await self._get_mock_live_scores(sport, game_date)

    async def _get_athletic_player_stats(self, external_id: str, sport: SportType, season: str, stat_type: str) -> Optional[Dict[str, Any]]:
        """Get player stats from The Athletic API (future implementation)"""
        return await self._get_mock_player_stats(external_id, sport, season, stat_type)

    async def _get_athletic_injury_reports(self, sport: SportType, team_id: Optional[str]) -> List[Dict[str, Any]]:
        """Get injury reports from The Athletic API (future implementation)"""
        return await self._get_mock_injury_reports(sport, team_id)


# Global service instance
_sports_data_service: Optional[SportsDataService] = None


async def get_sports_data_service() -> SportsDataService:
    """Get the global sports data service instance."""
    global _sports_data_service
    if _sports_data_service is None:
        redis_pool = None
        if get_redis_pool:
            try:
                redis_pool = await get_redis_pool()
            except Exception:
                pass  # Redis not available, will use without caching
        _sports_data_service = SportsDataService(redis_pool=redis_pool)
    return _sports_data_service


def reset_sports_data_service():
    """Reset the global service (useful for testing)."""
    global _sports_data_service
    _sports_data_service = None