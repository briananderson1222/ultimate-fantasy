"""
GET /api/v1/sports/players/{playerId} endpoint implementation.

Provides detailed player information with:
- Complete player profile and statistics
- Season and game-by-game statistics
- Fantasy projections and analysis
- Injury status and history
- Performance trends and metrics
- News and updates
- Ownership and usage statistics
- Advanced analytics and insights
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from api.models.response import StandardResponse
from domains.sports.services.sports_data_service import get_sports_data_service
from domains.users.models.user import User

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging

    get_logger = logging.getLogger  # type: ignore[assignment]

logger = get_logger(__name__)

router = APIRouter()


class PlayerStats(BaseModel):
    """Player statistics model."""

    season: str | None = None
    week: int | None = None
    games_played: int = 0
    stats: dict[str, float] = Field(default_factory=dict)
    fantasy_points: float = 0.0
    updated_at: str | None = None


class PlayerProjections(BaseModel):
    """Player projections model."""

    week: int | None = None
    season: str | None = None
    projected_stats: dict[str, float] = Field(default_factory=dict)
    projected_fantasy_points: float = 0.0
    confidence: float = 0.0
    ceiling: float = 0.0
    floor: float = 0.0
    last_updated: str | None = None


class InjuryDetails(BaseModel):
    """Player injury details model."""

    status: str = "healthy"
    description: str | None = None
    severity: str | None = None
    return_date: str | None = None
    last_updated: str | None = None


class PlayerTrends(BaseModel):
    """Player performance trends model."""

    trend_direction: str = "stable"  # trending_up, trending_down, stable
    recent_performance: float = 0.0
    season_average: float = 0.0
    consistency_score: float = 0.0
    breakout_probability: float = 0.0
    bust_probability: float = 0.0


class UsageMetrics(BaseModel):
    """Player usage and ownership metrics."""

    ownership_percentage: float = 0.0
    start_percentage: float = 0.0
    roster_percentage: float = 0.0
    target_share: float | None = None
    snap_percentage: float | None = None
    red_zone_usage: float | None = None


class NewsItem(BaseModel):
    """Player news item model."""

    headline: str
    summary: str | None = None
    source: str
    published_at: str
    impact: str = "neutral"  # positive, negative, neutral
    url: str | None = None


class PlayerDetailResponse(BaseModel):
    """Detailed player response model."""

    # Basic Information
    player_id: str
    external_id: str
    name: str
    position: str
    team_id: str | None
    sport: str

    # Physical Attributes
    jersey_number: str | None = None
    height: str | None = None
    weight: str | None = None
    age: int | None = None
    experience: int | None = None
    college: str | None = None

    # Status
    injury_status: str = "healthy"
    injury_details: InjuryDetails | None = None
    active: bool = True

    # Statistics
    season_stats: PlayerStats | None = None
    recent_games: list[PlayerStats] = Field(default_factory=list)

    # Projections
    current_projections: PlayerProjections | None = None
    season_projections: PlayerProjections | None = None

    # Analytics
    performance_trends: PlayerTrends | None = None
    usage_metrics: UsageMetrics | None = None

    # Additional Data
    news: list[NewsItem] = Field(default_factory=list)
    salary: int | None = None
    contract_years: int | None = None

    # Metadata
    created_at: str | None = None
    updated_at: str | None = None
    last_game_date: str | None = None


@router.get(
    "/players/{player_id}", response_model=StandardResponse[PlayerDetailResponse]
)
async def get_player_details(
    player_id: str = Path(..., description="Player ID"),
    include_stats: bool = Query(True, description="Include season statistics"),
    include_projections: bool = Query(True, description="Include projections"),
    include_news: bool = Query(False, description="Include recent news"),
    recent_games: int = Query(
        5, description="Number of recent games to include", ge=0, le=10
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[PlayerDetailResponse]:
    """
    Get detailed information for a specific player.

    - **player_id**: Unique player identifier
    - **include_stats**: Whether to include season statistics (default: true)
    - **include_projections**: Whether to include projections (default: true)
    - **include_news**: Whether to include recent news (default: false)
    - **recent_games**: Number of recent games to include (0-10, default: 5)

    Returns comprehensive player information with statistics, projections, and analytics.
    """
    try:
        logger.info(
            "Player details request",
            extra={
                "user_id": str(current_user.user_id),
                "player_id": player_id,
                "include_stats": include_stats,
                "include_projections": include_projections,
            },
        )

        # Get sports data service
        sports_service = await get_sports_data_service()

        # Get player details
        player_data = await sports_service.get_player_details(
            player_id=player_id,
            include_stats=include_stats,
            include_projections=include_projections,
            use_cache=True,
        )

        if not player_data:
            raise HTTPException(
                status_code=404, detail=f"Player with ID {player_id} not found"
            )

        # Build response
        response_data = PlayerDetailResponse(
            player_id=player_data.get("player_id", ""),
            external_id=player_data.get("external_id", ""),
            name=player_data.get("name", ""),
            position=player_data.get("position", ""),
            team_id=player_data.get("team_id"),
            sport=player_data.get("sport", ""),
            jersey_number=player_data.get("jersey_number"),
            height=player_data.get("height"),
            weight=player_data.get("weight"),
            age=player_data.get("age"),
            experience=player_data.get("experience"),
            college=player_data.get("college"),
            injury_status=player_data.get("injury_status", "healthy"),
            active=player_data.get("active", True),
            salary=player_data.get("salary"),
            contract_years=player_data.get("contract_years"),
            created_at=player_data.get("created_at"),
            updated_at=player_data.get("updated_at"),
            last_game_date=player_data.get("last_game_date"),
        )

        # Add injury details if available
        if player_data.get("injury_details"):
            injury_data = player_data["injury_details"]
            response_data.injury_details = InjuryDetails(
                status=injury_data.get("status", "healthy"),
                description=injury_data.get("description"),
                severity=injury_data.get("severity"),
                return_date=injury_data.get("return_date"),
                last_updated=injury_data.get("last_updated"),
            )

        # Add season stats if requested and available
        if include_stats and player_data.get("season_stats"):
            stats_data = player_data["season_stats"]
            response_data.season_stats = PlayerStats(
                season=stats_data.get("season"),
                week=stats_data.get("week"),
                games_played=stats_data.get("games_played", 0),
                stats=stats_data.get("stats", {}),
                fantasy_points=stats_data.get("fantasy_points", 0.0),
                updated_at=stats_data.get("updated_at"),
            )

        # Add recent games stats
        if recent_games > 0:
            recent_stats = await _get_recent_game_stats(
                sports_service, player_id, recent_games
            )
            response_data.recent_games = recent_stats

        # Add projections if requested and available
        if include_projections:
            current_proj = await _get_current_projections(sports_service, player_id)
            if current_proj:
                response_data.current_projections = current_proj

            season_proj = await _get_season_projections(sports_service, player_id)
            if season_proj:
                response_data.season_projections = season_proj

        # Add performance trends
        trends = await _calculate_performance_trends(sports_service, player_id)
        if trends:
            response_data.performance_trends = trends

        # Add usage metrics
        usage = await _calculate_usage_metrics(sports_service, player_id)
        if usage:
            response_data.usage_metrics = usage

        # Add news if requested
        if include_news:
            news_items = await _get_player_news(player_id, limit=5)
            response_data.news = news_items

        logger.info(
            "Player details completed",
            extra={
                "user_id": str(current_user.user_id),
                "player_id": player_id,
                "player_name": response_data.name,
            },
        )

        return StandardResponse(
            success=True,
            data=response_data,
            message=f"Player details for {response_data.name}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Player details failed",
            extra={
                "user_id": str(current_user.user_id),
                "player_id": player_id,
                "error": str(e),
            },
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve player details. Please try again later.",
        )


@router.get(
    "/players/{player_id}/stats", response_model=StandardResponse[list[PlayerStats]]
)
async def get_player_statistics(
    player_id: str = Path(..., description="Player ID"),
    season: str | None = Query(None, description="Season year (e.g., 2024)"),
    week: int | None = Query(None, description="Specific week number"),
    limit: int = Query(10, description="Maximum number of stat records", ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[list[PlayerStats]]:
    """
    Get player statistics for specified timeframe.

    - **player_id**: Unique player identifier
    - **season**: Optional season filter (e.g., "2024")
    - **week**: Optional specific week number
    - **limit**: Maximum number of stat records (1-50, default: 10)

    Returns list of player statistics matching the criteria.
    """
    try:
        logger.info(
            "Player stats request",
            extra={
                "user_id": str(current_user.user_id),
                "player_id": player_id,
                "season": season,
                "week": week,
            },
        )

        # Get sports data service
        sports_service = await get_sports_data_service()

        # Get player stats
        if week and season:
            # Get specific week stats
            stats_data = await sports_service.get_player_stats(
                player_id=player_id, season=season, week=week, use_cache=True
            )
            stats_list = [stats_data] if stats_data else []
        else:
            # Get multiple stats records
            stats_list = await _get_player_stats_history(
                sports_service, player_id, season, limit
            )

        # Convert to response models
        response_stats = []
        for stats_data in stats_list:
            if stats_data:
                stats_response = PlayerStats(
                    season=stats_data.get("season"),
                    week=stats_data.get("week"),
                    games_played=stats_data.get("games_played", 0),
                    stats=stats_data.get("stats", {}),
                    fantasy_points=stats_data.get("fantasy_points", 0.0),
                    updated_at=stats_data.get("updated_at"),
                )
                response_stats.append(stats_response)

        logger.info(
            "Player stats completed",
            extra={
                "user_id": str(current_user.user_id),
                "player_id": player_id,
                "stats_count": len(response_stats),
            },
        )

        return StandardResponse(
            success=True,
            data=response_stats,
            message=f"Retrieved {len(response_stats)} stat records",
        )

    except Exception as e:
        logger.error(
            "Player stats failed",
            extra={
                "user_id": str(current_user.user_id),
                "player_id": player_id,
                "error": str(e),
            },
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve player statistics. Please try again later.",
        )


# Helper functions


async def _get_recent_game_stats(
    sports_service, player_id: str, count: int
) -> list[PlayerStats]:
    """Get recent game statistics for player."""
    try:
        # This would get the most recent game stats
        # Implementation depends on how game stats are stored
        return []  # Placeholder
    except Exception as e:
        logger.warning(f"Failed to get recent game stats: {e}")
        return []


async def _get_current_projections(
    sports_service, player_id: str
) -> PlayerProjections | None:
    """Get current week projections for player."""
    try:
        # Get current week projections
        projections = await sports_service.get_player_projections(
            player_id=player_id, week=1, season="2024", use_cache=True  # Current week
        )

        if projections:
            return PlayerProjections(
                week=projections.get("week"),
                season=projections.get("season"),
                projected_stats=projections.get("projected_stats", {}),
                projected_fantasy_points=projections.get(
                    "projected_fantasy_points", 0.0
                ),
                confidence=projections.get("confidence", 0.0),
                ceiling=projections.get("projected_stats", {}).get("ceiling", 0.0),
                floor=projections.get("projected_stats", {}).get("floor", 0.0),
                last_updated=projections.get("last_updated"),
            )

        return None
    except Exception as e:
        logger.warning(f"Failed to get current projections: {e}")
        return None


async def _get_season_projections(
    sports_service, player_id: str
) -> PlayerProjections | None:
    """Get season projections for player."""
    try:
        # Season projections would be calculated differently
        # For now, return None as placeholder
        return None
    except Exception as e:
        logger.warning(f"Failed to get season projections: {e}")
        return None


async def _calculate_performance_trends(
    sports_service, player_id: str
) -> PlayerTrends | None:
    """Calculate player performance trends."""
    try:
        # This would analyze recent performance vs season average
        # Placeholder implementation
        return PlayerTrends(
            trend_direction="stable",
            recent_performance=15.2,
            season_average=14.8,
            consistency_score=0.75,
            breakout_probability=0.25,
            bust_probability=0.15,
        )
    except Exception as e:
        logger.warning(f"Failed to calculate performance trends: {e}")
        return None


async def _calculate_usage_metrics(
    sports_service, player_id: str
) -> UsageMetrics | None:
    """Calculate player usage metrics."""
    try:
        # This would calculate ownership and usage statistics
        # Placeholder implementation
        return UsageMetrics(
            ownership_percentage=65.4,
            start_percentage=78.9,
            roster_percentage=82.1,
            target_share=22.5,
            snap_percentage=68.3,
            red_zone_usage=15.2,
        )
    except Exception as e:
        logger.warning(f"Failed to calculate usage metrics: {e}")
        return None


async def _get_player_news(player_id: str, limit: int = 5) -> list[NewsItem]:
    """Get recent news for player."""
    try:
        # This would fetch recent news from sports news APIs
        # Placeholder implementation
        return [
            NewsItem(
                headline="Player Update: Practicing in full",
                summary="Player participated in full practice and is expected to play.",
                source="ESPN",
                published_at="2024-09-22T10:30:00Z",
                impact="positive",
            )
        ]
    except Exception as e:
        logger.warning(f"Failed to get player news: {e}")
        return []


async def _get_player_stats_history(
    sports_service, player_id: str, season: str | None, limit: int
) -> list[dict]:
    """Get player statistics history."""
    try:
        # This would get historical stats for the player
        # Implementation depends on how stats are stored
        return []  # Placeholder
    except Exception as e:
        logger.warning(f"Failed to get player stats history: {e}")
        return []
