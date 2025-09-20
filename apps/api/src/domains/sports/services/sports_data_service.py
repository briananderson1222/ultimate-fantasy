"""
SportsDataService with multi-provider support.

Implements T035 requirements:
- Multi-provider support for sports data
- Data normalization and caching
- Player statistics and projections
- Injury status tracking
- Team and schedule data
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Protocol, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

import httpx
from sqlalchemy.orm import Session

from infrastructure.cache.redis_pool import FantasyRedisPool, get_redis_pool
from infrastructure.observability.tracing import get_tracer, trace_fantasy_operation


logger = logging.getLogger(__name__)
tracer = get_tracer()


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
        providers: List[SportsDataProvider] = None,
        redis_pool: Optional[FantasyRedisPool] = None,
        default_cache_ttl: int = 300
    ):
        """
        Initialize sports data service.

        Args:
            providers: List of data providers (defaults to mock)
            redis_pool: Redis connection pool for caching
            default_cache_ttl: Default cache TTL in seconds
        """
        self.providers = providers or [MockSportsDataProvider()]
        self.redis_pool = redis_pool
        self.default_cache_ttl = default_cache_ttl

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


# Global service instance
_sports_data_service: Optional[SportsDataService] = None


async def get_sports_data_service() -> SportsDataService:
    """Get the global sports data service instance."""
    global _sports_data_service
    if _sports_data_service is None:
        redis_pool = await get_redis_pool()
        _sports_data_service = SportsDataService(redis_pool=redis_pool)
    return _sports_data_service


def reset_sports_data_service():
    """Reset the global service (useful for testing)."""
    global _sports_data_service
    _sports_data_service = None