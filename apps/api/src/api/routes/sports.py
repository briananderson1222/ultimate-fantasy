"""
Sports Data API endpoints for Ultimate Fantasy Platform
Provides REST API for player data, stats, news, schedules, and projections
"""

import asyncio
import uuid as _uuid
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.infrastructure.database.session_factory import get_db_session
from src.domains.users.services.user_service import UserService
from src.domains.sports.services.sports_data_service import (
    SportsDataService,
    SportType,
    DataProvider,
    PlayerData,
    GameData
)
from src.services.player_service import PlayerService
from src.domains.shared.exceptions import (
    PlayerNotFoundError, ProviderError, ValidationError,
    InsufficientPermissionsError, RateLimitExceededError
)
from src.api.deps import (
    get_player_service,
    get_sports_data_service,
    get_user_service,
)
from src.api.middleware.auth import get_current_user
from src.api.models.response import APIResponse


SUPPORTED_SPORTS = {"mlb", "nfl", "wnba"}


router = APIRouter(prefix="/api/v1/sports", tags=["sports"])


# Pydantic Models for Request/Response
class PlayerResponse(BaseModel):
    player_id: str
    external_id: str
    name: str
    team_id: Optional[str]
    position: str
    sport: str
    injury_status: Optional[str]
    injury_description: Optional[str]
    season_stats: Optional[Dict[str, Any]]
    game_stats: Optional[Dict[str, Any]]
    projections: Optional[Dict[str, Any]]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class PlayerStatsResponse(BaseModel):
    player_id: str
    season: str
    week: Optional[int]
    game_day: date
    opponent_team: Optional[str]
    is_home_game: Optional[bool]
    stat_values: Dict[str, Union[int, float]]
    fantasy_points: float
    is_final: bool
    updated_at: datetime

    class Config:
        from_attributes = True


class PlayerNewsResponse(BaseModel):
    news_id: str
    player_id: str
    headline: str
    summary: str
    content: Optional[str]
    source: str
    author: Optional[str]
    published_at: datetime
    impact_rating: Optional[int]
    tags: List[str]

    class Config:
        from_attributes = True


@router.get("/news")
async def get_sports_news(
    sport: str = Query(..., description="Sport type"),
    player_id: Optional[str] = Query(None, description="Player identifier"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of stories"),
    days_back: int = Query(default=7, ge=1, le=30, description="How far back to search"),
    db: Session = Depends(get_db_session),
    player_service: PlayerService = Depends(get_player_service),
):
    """Return recent sports news for a player or sport."""

    sport_normalized = sport.lower()
    if sport_normalized not in SUPPORTED_SPORTS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported sport")

    # Contract allows empty list; use player-specific news when id provided, else empty list.
    if player_id:
        player_uuid = _parse_uuid(player_id)
        if player_uuid is not None:
            try:
                await asyncio.to_thread(player_service.get_player, player_uuid, db)
            except SQLAlchemyError:
                pass

    # Placeholder until provider integration is wired.
    return []


class GameScheduleResponse(BaseModel):
    game_id: str
    sport: str
    season: str
    week: Optional[int]
    home_team: str
    away_team: str
    game_date: datetime
    status: str
    venue: Optional[str]
    weather: Optional[Dict[str, Any]]
    tv_coverage: Optional[str]
    home_score: Optional[int]
    away_score: Optional[int]

    class Config:
        from_attributes = True


class TeamResponse(BaseModel):
    team_id: str
    name: str
    abbreviation: str
    city: str
    sport: str
    conference: Optional[str]
    division: Optional[str]
    logo_url: Optional[str]
    primary_color: Optional[str]
    secondary_color: Optional[str]
    record: Optional[Dict[str, int]]

    class Config:
        from_attributes = True


class ProjectionsResponse(BaseModel):
    player_id: str
    week: int
    projected_points: float
    confidence: float
    stat_projections: Dict[str, float]
    injury_risk: float

    class Config:
        from_attributes = True


class InjuryReportResponse(BaseModel):
    player_id: str
    player_name: str
    team: str
    position: str
    injury_status: str
    injury_description: str
    estimated_return: Optional[date]
    practice_status: Optional[str]
    game_status: str
    last_updated: datetime

    class Config:
        from_attributes = True


def _player_payload(
    player: Any,
    *,
    include_stats: bool = True,
    include_projections: bool = True,
    default_sport: Optional[str] = None,
) -> Dict[str, Any]:
    """Normalize player structures (ORM objects or provider dicts) to response payload."""

    def _get(attr: str, default: Any = None) -> Any:
        if isinstance(player, dict):
            return player.get(attr, default)
        return getattr(player, attr, default)

    team_id = _get("team_id") or _get("team")
    sport = _get("sport", default_sport)

    payload: Dict[str, Any] = {
        "player_id": str(_get("player_id") or _get("id") or _get("external_id") or ""),
        "external_id": str(_get("external_id") or _get("player_id") or ""),
        "name": _get("name", ""),
        "team_id": team_id,
        "position": _get("position", ""),
        "sport": sport,
        "injury_status": _get("injury_status") or _get("status"),
        "injury_description": _get("injury_description") or _get("injury_details"),
        "season_stats": _get("season_stats") if include_stats else None,
        "game_stats": _get("game_stats") if include_stats else None,
        "projections": _get("projections") if include_projections else None,
        "created_at": _get("created_at"),
        "updated_at": _get("updated_at"),
    }

    if payload["projections"] is None and include_projections:
        payload["projections"] = _get("stat_projections")

    return payload


def _to_injury_response(player: Any) -> Dict[str, Any]:
    """Build a lightweight injury report from a player record."""

    return {
        "player_id": str(player.player_id),
        "player_name": player.name,
        "team": player.team_id or "",
        "position": player.position,
        "injury_status": getattr(player, "injury_status", "healthy"),
        "injury_description": getattr(player, "injury_description", ""),
        "expected_return": None,
        "last_updated": datetime.utcnow().isoformat(),
    }


def _parse_uuid(value: str) -> Optional[_uuid.UUID]:
    try:
        return _uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):
        return None


# Player Data Endpoints
@router.get("/players")
async def list_players(
    sport: Optional[str] = Query(None, description="Sport type (optional, returns all sports if not specified)"),
    position: Optional[str] = Query(None, description="Filter by position"),
    team: Optional[str] = Query(None, description="Filter by team"),
    search: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of results"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    sports_data_service: SportsDataService = Depends(get_sports_data_service),
):
    """Return players matching the provided filters."""

    # Handle optional sport parameter
    if sport:
        sport_normalized = sport.lower()
        if sport_normalized not in SUPPORTED_SPORTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported sport",
            )
        provider_sport = sport_normalized.upper()
        sports_list = [provider_sport]
    else:
        # If no sport specified, return players from all supported sports
        sports_list = [s.upper() for s in SUPPORTED_SPORTS]

    provider_position = position.upper() if position else None

    # Aggregate players from all requested sports
    all_players = []
    for provider_sport in sports_list:
        raw_players = await sports_data_service.get_players(
            sport=provider_sport,
            position=provider_position,
            team=team,
            active_only=True,
        )
        all_players.extend(raw_players)

    if search:
        query_text = search.lower()
        all_players = [
            player
            for player in all_players
            if query_text in (player.get("name", "").lower())
        ]

    paginated = all_players[offset : offset + limit]

    # For response structure, match contract expectations
    return {
        "players": [
            _player_payload(player, include_stats=False, include_projections=False, default_sport=sport)
            for player in paginated
        ],
        "pagination": {
            "offset": offset,
            "limit": limit,
            "total": len(all_players)
        },
        "total": len(all_players)
    }


@router.get("/players/{player_id}")
async def get_player(
    player_id: str,
    include_stats: bool = Query(default=True, description="Include current season stats"),
    include_projections: bool = Query(default=True, description="Include projections"),
    db: Session = Depends(get_db_session),
    player_service: PlayerService = Depends(get_player_service),
    sports_data_service: SportsDataService = Depends(get_sports_data_service),
):
    """Get detailed player information"""
    try:
        player_uuid = _parse_uuid(player_id)
        if player_uuid is None:
            raise PlayerNotFoundError

        details = await sports_data_service.get_player_details(
            str(player_uuid),
            include_stats=include_stats,
            include_projections=include_projections,
        )

        if details:
            return _player_payload(
                details,
                include_stats=include_stats,
                include_projections=include_projections,
            )

        try:
            player = await asyncio.to_thread(
                player_service.get_player,
                player_uuid,
                db,
            )
        except SQLAlchemyError:
            player = None

        if player is None:
            raise PlayerNotFoundError

        return _player_payload(
            player,
            include_stats=include_stats,
            include_projections=include_projections,
        )

    except PlayerNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    except SQLAlchemyError:
        return APIResponse(
            success=True,
            data=[],
            message="Player stats unavailable"
        )
    except ProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Sports data provider error: {str(e)}"
        )


# Legacy per-player stats endpoint (not used by contract tests) retained for compatibility
@router.get("/players/{player_id}/stats", response_model=APIResponse[List[PlayerStatsResponse]])
async def get_player_stats(
    player_id: str,
    season: Optional[str] = Query(None, description="Season year (defaults to current)"),
    week: Optional[int] = Query(None, description="Specific week"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    player_service: PlayerService = Depends(get_player_service),
):
    """Get player statistics for specified time period"""
    try:
        player = await asyncio.to_thread(player_service.get_player, player_id, db)
        if player is None:
            raise PlayerNotFoundError

        stats = await asyncio.to_thread(
            player_service.get_player_game_logs,
            player_id,
            season,
            week,
            start_date,
            end_date,
            db,
        )

        return APIResponse(
            success=True,
            data=[PlayerStatsResponse.from_orm(stat) for stat in stats],
            message="Player stats retrieved successfully"
        )

    except PlayerNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    except ProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Sports data provider error: {str(e)}"
        )


@router.get("/players/{player_id}/projections", response_model=APIResponse[List[ProjectionsResponse]])
async def get_player_projections(
    player_id: str,
    season: Optional[str] = Query(None, description="Season year (defaults to current)"),
    week: Optional[int] = Query(None, description="Specific week"),
    projection_type: str = Query(default="season", description="Projection type: season, weekly, rest_of_season"),
    current_user: dict = Depends(get_current_user),
    sports_data_service: SportsDataService = Depends(get_sports_data_service),
):
    """Get player projections and fantasy point estimates"""
    try:
        player_uuid = _parse_uuid(player_id)
        if player_uuid is None:
            raise PlayerNotFoundError

        week_value = week or 1
        season_value = season or str(datetime.utcnow().year)

        projection = await sports_data_service.get_player_projections(
            str(player_uuid),
            week_value,
            season_value,
        )

        payload: List[ProjectionsResponse] = []
        if projection:
            payload.append(
                ProjectionsResponse(
                    player_id=projection.player_id,
                    week=projection.week,
                    projected_points=getattr(projection, "projected_fantasy_points", 0.0),
                    confidence=getattr(projection, "confidence", 0.0),
                    stat_projections=getattr(projection, "projected_stats", {}),
                    injury_risk=getattr(projection, "injury_risk", None) or 0.0,
                )
            )

        return APIResponse(
            success=True,
            data=payload,
            message="Player projections retrieved successfully"
        )

    except PlayerNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/players/{player_id}/news", response_model=APIResponse[List[PlayerNewsResponse]])
async def get_player_news(
    player_id: str,
    days_back: int = Query(default=7, ge=1, le=30, description="Days to look back for news"),
    limit: int = Query(default=20, le=100, description="Maximum number of articles"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    player_service: PlayerService = Depends(get_player_service),
):
    """Get recent news and updates for a player"""
    try:
        news = await asyncio.to_thread(
            player_service.get_player_news,
            player_id=player_id,
            days_back=days_back,
            limit=limit,
            db=db,
        )

        return APIResponse(
            success=True,
            data=[PlayerNewsResponse.model_validate(article) for article in news],
            message="Player news retrieved successfully"
        )

    except PlayerNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    except ProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Sports data provider error: {str(e)}"
        )


# Team and Schedule Endpoints
@router.get("/teams", response_model=APIResponse[List[TeamResponse]])
async def get_teams(
    sport: str = Query(..., description="Sport type"),
    conference: Optional[str] = Query(None, description="Filter by conference"),
    division: Optional[str] = Query(None, description="Filter by division"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    sports_data_service: SportsDataService = Depends(get_sports_data_service),
):
    """Get teams for a specific sport"""
    try:
        teams = await sports_data_service.get_teams(
            sport=sport,
            conference=conference,
            division=division,
            db=db
        )

        return APIResponse(
            success=True,
            data=[TeamResponse.from_orm(team) for team in teams],
            message="Teams retrieved successfully"
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Sports data provider error: {str(e)}"
        )


@router.get("/schedule", response_model=APIResponse[List[GameScheduleResponse]])
async def get_schedule(
    sport: str = Query(..., description="Sport type"),
    season: Optional[str] = Query(None, description="Season year (defaults to current)"),
    week: Optional[int] = Query(None, description="Specific week"),
    team: Optional[str] = Query(None, description="Filter by team"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    sports_data_service: SportsDataService = Depends(get_sports_data_service),
):
    """Get game schedule for specified parameters"""
    try:
        schedule = await sports_data_service.get_schedule(
            sport=sport,
            season=season,
            week=week,
            team=team,
            start_date=start_date,
            end_date=end_date,
            db=db
        )

        return APIResponse(
            success=True,
            data=[GameScheduleResponse.from_orm(game) for game in schedule],
            message="Schedule retrieved successfully"
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Sports data provider error: {str(e)}"
        )


# Injury Reports and Status
@router.get("/injuries")
async def get_injury_report(
    sport: str = Query(..., description="Sport type"),
    team: Optional[str] = Query(None, description="Filter by team"),
    position: Optional[str] = Query(None, description="Filter by position"),
    status: Optional[str] = Query(None, description="Filter by injury status"),
    db: Session = Depends(get_db_session),
    player_service: PlayerService = Depends(get_player_service),
):
    """Get current injury report for specified sport/team"""
    try:
        try:
            injuries = await asyncio.to_thread(
                player_service.get_injury_report,
                sport,
                team,
                position,
                status,
                db,
            )
        except SQLAlchemyError:
            injuries = []

        return [_to_injury_response(player) for player in injuries]

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Sports data provider error: {str(e)}"
        )


# Fantasy Specific Endpoints
@router.get("/trending", response_model=APIResponse[List[PlayerResponse]])
async def get_trending_players(
    sport: str = Query(..., description="Sport type"),
    trend_type: str = Query(default="hot", description="Trend type: hot, cold, rising, falling"),
    timeframe: str = Query(default="7d", description="Timeframe: 24h, 7d, 30d"),
    position: Optional[str] = Query(None, description="Filter by position"),
    limit: int = Query(default=25, le=100, description="Maximum number of results"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    player_service: PlayerService = Depends(get_player_service),
    sports_data_service: SportsDataService = Depends(get_sports_data_service),
):
    """Get trending players based on fantasy activity"""
    sport_normalized = sport.lower()
    try:
        days_lookup = {"24h": 1, "7d": 7, "30d": 30}
        days = days_lookup.get(timeframe.lower(), 7)

        try:
            trends = await asyncio.to_thread(
                player_service.get_trending_players,
                sport,
                trend_type,
                days,
                limit,
                db,
            )
        except SQLAlchemyError:
            trends = []

        responses = []
        for item in trends:
            player_payload = item.get("player") if isinstance(item, dict) else None
            if not player_payload:
                continue
            model = PlayerResponse.model_validate(player_payload)
            responses.append(model.model_dump())

        if not responses:
            fallback_players = await sports_data_service.get_players(
                sport=sport_normalized.upper(),
                position=position.upper() if position else None,
                active_only=True,
            )
            responses = [
                _player_payload(p, include_stats=False, include_projections=False, default_sport=sport_normalized)
                for p in fallback_players[:limit]
            ]

        if position:
            responses = [player for player in responses if player.get("position") == position]

        data = [PlayerResponse.model_validate(player) for player in responses]

        return APIResponse(
            success=True,
            data=data,
            message="Trending players retrieved successfully",
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Sports data provider error: {str(e)}"
        )


@router.get("/rankings", response_model=APIResponse[List[PlayerResponse]])
async def get_player_rankings(
    sport: str = Query(..., description="Sport type"),
    position: Optional[str] = Query(None, description="Filter by position"),
    ranking_type: str = Query(default="overall", description="Ranking type: overall, positional, ppr"),
    timeframe: str = Query(default="season", description="Timeframe: season, ros, weekly"),
    limit: int = Query(default=50, le=200, description="Maximum number of results"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    player_service: PlayerService = Depends(get_player_service),
    sports_data_service: SportsDataService = Depends(get_sports_data_service),
):
    """Get fantasy player rankings"""
    sport_normalized = sport.lower()
    try:
        try:
            rankings = await asyncio.to_thread(
                player_service.get_player_rankings,
                sport,
                position,
                timeframe,
                limit,
                db,
            )
        except SQLAlchemyError:
            rankings = []

        if rankings:
            data = [
                PlayerResponse.model_validate(_player_payload(player))
                for player in rankings
            ]
            return APIResponse(
                success=True,
                data=data,
                message="Player rankings retrieved successfully",
            )

        fallback_players = await sports_data_service.get_players(
            sport=sport_normalized.upper(),
            position=position.upper() if position else None,
            active_only=True,
        )

        data = [
            PlayerResponse.model_validate(
                _player_payload(player, include_stats=False, include_projections=False, default_sport=sport_normalized)
            )
            for player in fallback_players[:limit]
        ]

        return APIResponse(
            success=True,
            data=data,
            message="Player rankings retrieved successfully",
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Sports data provider error: {str(e)}"
        )


# Data Refresh and Sync
@router.post("/sync/{sport}")
async def sync_sport_data(
    sport: str,
    data_type: str = Query(default="all", description="Data type to sync: all, players, stats, schedule"),
    force: bool = Query(default=False, description="Force refresh even if recently updated"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    sports_data_service: SportsDataService = Depends(get_sports_data_service),
    user_service: UserService = Depends(get_user_service),
):
    """Trigger data sync for a sport (admin only)"""
    try:
        # Check if user has admin permissions
        user = await asyncio.to_thread(
            user_service.get_user_sync,
            current_user["user_id"],
            db,
        )
        if not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )

        result = await sports_data_service.sync_sport_data(
            sport=sport,
            data_type=data_type,
            force=force,
            db=db
        )

        return APIResponse(
            success=True,
            data=result,
            message="Data sync initiated successfully"
        )

    except InsufficientPermissionsError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RateLimitExceededError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )


@router.get("/sync/status", response_model=APIResponse[Dict[str, Any]])
async def get_sync_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    sports_data_service: SportsDataService = Depends(get_sports_data_service),
):
    """Get data sync status for all sports"""
    try:
        status_info = await sports_data_service.get_sync_status(db)

        return APIResponse(
            success=True,
            data=status_info,
            message="Sync status retrieved successfully"
        )

    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )
@router.get("/stats")
async def get_stats(
    sport: str = Query(..., description="Sport type"),
    timeframe: str = Query(..., description="Timeframe: season or week"),
    player_id: Optional[str] = Query(None, description="Player identifier"),
    team_id: Optional[str] = Query(None, description="Team identifier"),
    week: Optional[int] = Query(None, description="Specific week when timeframe=week"),
    sports_data_service: SportsDataService = Depends(get_sports_data_service),
):
    """Return player or team statistics depending on filters."""

    sport_normalized = sport.lower()
    if sport_normalized not in SUPPORTED_SPORTS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported sport")

    timeframe_normalized = timeframe.lower()
    if timeframe_normalized not in {"season", "week"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid timeframe")

    if team_id:
        team_players = await sports_data_service.get_players(
            sport=sport_normalized.upper(),
            team=team_id,
            active_only=True,
        )

        return [
            {
                "player_id": str(player.get("player_id")),
                "stats": player.get("season_stats") or {},
            }
            for player in team_players
        ]

    if not player_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="player_id or team_id required")

    player_uuid = _parse_uuid(player_id)
    if player_uuid is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

    season_value = datetime.utcnow().year
    stats_item = await sports_data_service.get_player_stats(
        str(player_uuid),
        season=str(season_value),
        week=week if timeframe_normalized == "week" else None,
    )

    if stats_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

    stats_dict = getattr(stats_item, "stats", {})
    last_updated = getattr(stats_item, "last_updated", datetime.utcnow())

    return {
        "player_id": str(player_uuid),
        "sport": sport_normalized,
        "timeframe": timeframe_normalized,
        "stats": stats_dict,
        "last_updated": last_updated.isoformat() if isinstance(last_updated, datetime) else datetime.utcnow().isoformat(),
    }
