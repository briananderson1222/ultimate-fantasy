"""
Sports Data API endpoints for Ultimate Fantasy Platform
Provides REST API for player data, stats, news, schedules, and projections
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ...infrastructure.database.session_factory import get_db_session
from ...domains.users.services.user_service import UserService
from ...services.sports_data_service import SportsDataService
from ...services.player_service import PlayerService
from ...domains.shared.exceptions import (
    PlayerNotFoundError, ProviderError, ValidationError,
    InsufficientPermissionsError, RateLimitExceededError
)
from ..middleware.auth import get_current_user
from ..models.response import APIResponse, ErrorResponse
from ...models.player import Player, PlayerStats, SportType


router = APIRouter(prefix="/api/v1/sports", tags=["sports"])

sports_data_service = SportsDataService()
player_service = PlayerService()
user_service = UserService()


# Pydantic Models for Request/Response
class PlayerSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Search query (name, team, position)")
    sport: str = Field(..., description="Sport type")
    position: Optional[str] = Field(None, description="Filter by position")
    team: Optional[str] = Field(None, description="Filter by team")
    active_only: bool = Field(default=True, description="Only active players")

    @validator('sport')
    def validate_sport(cls, v):
        valid_sports = ['mlb', 'nfl', 'nba', 'nhl']
        if v.lower() not in valid_sports:
            raise ValueError(f"Sport must be one of: {valid_sports}")
        return v.lower()


class PlayerResponse(BaseModel):
    player_id: str
    external_id: str
    name: str
    team: str
    position: str
    sport: str
    jersey_number: Optional[int]
    height: Optional[str]
    weight: Optional[int]
    age: Optional[int]
    experience: Optional[int]
    status: str
    injury_status: Optional[str]
    injury_description: Optional[str]
    fantasy_positions: List[str]
    current_season_stats: Optional[Dict[str, Any]]
    projected_stats: Optional[Dict[str, Any]]
    last_updated: datetime

    class Config:
        from_attributes = True


class PlayerStatsResponse(BaseModel):
    player_id: str
    season: str
    week: Optional[int]
    game_date: Optional[date]
    opponent: Optional[str]
    home_away: Optional[str]
    stats: Dict[str, Union[int, float]]
    fantasy_points: Optional[float]
    is_final: bool
    last_updated: datetime

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
    season: str
    week: Optional[int]
    projections: Dict[str, float]
    confidence_score: float
    projection_source: str
    factors: List[str]
    last_updated: datetime

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


# Player Data Endpoints
@router.get("/players/search", response_model=APIResponse[List[PlayerResponse]])
async def search_players(
    query: str = Query(..., min_length=2, description="Search query"),
    sport: str = Query(..., description="Sport type"),
    position: Optional[str] = Query(None, description="Filter by position"),
    team: Optional[str] = Query(None, description="Filter by team"),
    active_only: bool = Query(default=True, description="Only active players"),
    limit: int = Query(default=50, le=200, description="Maximum number of results"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Search for players across all sports"""
    try:
        players = await player_service.search_players(
            query=query,
            sport=sport,
            position=position,
            team=team,
            active_only=active_only,
            limit=limit,
            offset=offset,
            db=db
        )

        return APIResponse(
            success=True,
            data=[PlayerResponse.from_orm(player) for player in players],
            message="Players retrieved successfully"
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


@router.get("/players/{player_id}", response_model=APIResponse[PlayerResponse])
async def get_player(
    player_id: str,
    include_stats: bool = Query(default=True, description="Include current season stats"),
    include_projections: bool = Query(default=True, description="Include projections"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get detailed player information"""
    try:
        player = await player_service.get_player_details(
            player_id=player_id,
            include_stats=include_stats,
            include_projections=include_projections,
            db=db
        )

        return APIResponse(
            success=True,
            data=PlayerResponse.from_orm(player),
            message="Player retrieved successfully"
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


@router.get("/players/{player_id}/stats", response_model=APIResponse[List[PlayerStatsResponse]])
async def get_player_stats(
    player_id: str,
    season: Optional[str] = Query(None, description="Season year (defaults to current)"),
    week: Optional[int] = Query(None, description="Specific week"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get player statistics for specified time period"""
    try:
        stats = await player_service.get_player_stats(
            player_id=player_id,
            season=season,
            week=week,
            start_date=start_date,
            end_date=end_date,
            db=db
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
    db: Session = Depends(get_db_session)
):
    """Get player projections and fantasy point estimates"""
    try:
        projections = await player_service.get_player_projections(
            player_id=player_id,
            season=season,
            week=week,
            projection_type=projection_type,
            db=db
        )

        return APIResponse(
            success=True,
            data=[ProjectionsResponse.from_orm(proj) for proj in projections],
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
    db: Session = Depends(get_db_session)
):
    """Get recent news and updates for a player"""
    try:
        news = await player_service.get_player_news(
            player_id=player_id,
            days_back=days_back,
            limit=limit,
            db=db
        )

        return APIResponse(
            success=True,
            data=[PlayerNewsResponse.from_orm(article) for article in news],
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
    db: Session = Depends(get_db_session)
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
    db: Session = Depends(get_db_session)
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
@router.get("/injuries", response_model=APIResponse[List[InjuryReportResponse]])
async def get_injury_report(
    sport: str = Query(..., description="Sport type"),
    team: Optional[str] = Query(None, description="Filter by team"),
    position: Optional[str] = Query(None, description="Filter by position"),
    status: Optional[str] = Query(None, description="Filter by injury status"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get current injury report for specified sport/team"""
    try:
        injuries = await player_service.get_injury_report(
            sport=sport,
            team=team,
            position=position,
            status=status,
            db=db
        )

        return APIResponse(
            success=True,
            data=[InjuryReportResponse.from_orm(injury) for injury in injuries],
            message="Injury report retrieved successfully"
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


# Fantasy Specific Endpoints
@router.get("/trending", response_model=APIResponse[List[PlayerResponse]])
async def get_trending_players(
    sport: str = Query(..., description="Sport type"),
    trend_type: str = Query(default="added", description="Trend type: added, dropped, traded"),
    timeframe: str = Query(default="24h", description="Timeframe: 24h, 7d, 30d"),
    position: Optional[str] = Query(None, description="Filter by position"),
    limit: int = Query(default=25, le=100, description="Maximum number of results"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get trending players based on fantasy activity"""
    try:
        players = await player_service.get_trending_players(
            sport=sport,
            trend_type=trend_type,
            timeframe=timeframe,
            position=position,
            limit=limit,
            db=db
        )

        return APIResponse(
            success=True,
            data=[PlayerResponse.from_orm(player) for player in players],
            message="Trending players retrieved successfully"
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
    db: Session = Depends(get_db_session)
):
    """Get fantasy player rankings"""
    try:
        rankings = await player_service.get_player_rankings(
            sport=sport,
            position=position,
            ranking_type=ranking_type,
            timeframe=timeframe,
            limit=limit,
            db=db
        )

        return APIResponse(
            success=True,
            data=[PlayerResponse.from_orm(player) for player in rankings],
            message="Player rankings retrieved successfully"
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
    db: Session = Depends(get_db_session)
):
    """Trigger data sync for a sport (admin only)"""
    try:
        # Check if user has admin permissions
        user = user_service.get_user(current_user["user_id"], db)
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
    db: Session = Depends(get_db_session)
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