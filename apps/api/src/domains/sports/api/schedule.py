"""
GET /api/v1/sports/schedule endpoint implementation.

Provides comprehensive game schedule information with:
- Game schedules by sport and timeframe
- Team-specific schedules
- Week and season filtering
- Game status and timing
- Venue and broadcast information
- Playoff and tournament schedules
"""

from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
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


class GameResponse(BaseModel):
    """Game response model."""

    game_id: str
    external_id: Optional[str] = None
    sport: str
    home_team: str
    away_team: str
    scheduled_at: str
    status: str = "scheduled"  # scheduled, in_progress, final, postponed, cancelled
    week: Optional[int] = None
    season: Optional[str] = None

    # Score information (if available)
    home_score: Optional[int] = None
    away_score: Optional[int] = None

    # Game state information
    period: Optional[int] = None
    time_remaining: Optional[str] = None
    is_final: bool = False

    # Additional information
    venue: Optional[str] = None
    attendance: Optional[int] = None
    weather: Optional[str] = None
    broadcast: Optional[str] = None
    officials: List[str] = Field(default_factory=list)

    # Metadata
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ScheduleResponse(BaseModel):
    """Schedule response model."""

    items: List[GameResponse]
    total: int
    sport: str
    season: Optional[str] = None
    week: Optional[int] = None
    date_range: Optional[dict] = None
    teams_involved: List[str] = Field(default_factory=list)


@router.get("/schedule", response_model=StandardResponse[ScheduleResponse])
async def get_schedule(
    sport: str = Query(..., description="Sport type", regex="^(mlb|nfl|wnba)$"),
    season: Optional[str] = Query(None, description="Season year (e.g., 2024)"),
    week: Optional[int] = Query(None, description="Specific week number"),
    team: Optional[str] = Query(None, description="Filter by team"),
    date: Optional[date] = Query(None, description="Specific date (YYYY-MM-DD)"),
    start_date: Optional[date] = Query(None, description="Start date for range"),
    end_date: Optional[date] = Query(None, description="End date for range"),
    status: Optional[str] = Query(
        None,
        description="Filter by game status",
        regex="^(scheduled|in_progress|final|postponed|cancelled)$"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[ScheduleResponse]:
    """
    Get game schedule with comprehensive filtering options.

    - **sport**: Required sport type (mlb, nfl, wnba)
    - **season**: Optional season filter (e.g., "2024")
    - **week**: Optional week number (sport-specific)
    - **team**: Optional team filter (e.g., "KC", "BUF")
    - **date**: Optional specific date filter
    - **start_date**: Optional start date for date range
    - **end_date**: Optional end date for date range
    - **status**: Optional game status filter

    Returns list of games matching the specified criteria.
    """
    try:
        logger.info(
            f"Schedule request",
            extra={
                "user_id": str(current_user.user_id),
                "sport": sport,
                "season": season,
                "week": week,
                "team": team,
                "date": str(date) if date else None,
            }
        )

        # Get sports data service
        sports_service = await get_sports_data_service()

        # Build parameters for schedule request
        schedule_params = {
            "sport": sport.upper(),
            "use_cache": True
        }

        if season:
            schedule_params["season"] = season
        if week:
            schedule_params["week"] = week
        if team:
            schedule_params["team"] = team.upper()

        # Fetch schedule data
        schedule_data = await sports_service.get_schedule(**schedule_params)

        if not schedule_data:
            logger.warning(f"No schedule found for criteria: {schedule_params}")
            return StandardResponse(
                success=True,
                data=ScheduleResponse(
                    items=[],
                    total=0,
                    sport=sport,
                    season=season,
                    week=week,
                ),
                message="No games found matching the criteria"
            )

        # Apply additional filters
        filtered_games = schedule_data

        # Date filtering
        if date:
            target_date = date.isoformat()
            filtered_games = [
                game for game in filtered_games
                if game.get("scheduled_at", "").startswith(target_date)
            ]
        elif start_date or end_date:
            if start_date:
                start_str = start_date.isoformat()
                filtered_games = [
                    game for game in filtered_games
                    if game.get("scheduled_at", "") >= start_str
                ]
            if end_date:
                end_str = end_date.isoformat()
                filtered_games = [
                    game for game in filtered_games
                    if game.get("scheduled_at", "") <= end_str
                ]

        # Status filtering
        if status:
            filtered_games = [
                game for game in filtered_games
                if game.get("status", "").lower() == status.lower()
            ]

        # Convert to response models
        game_responses = []
        teams_involved = set()

        for game_data in filtered_games:
            try:
                game_response = GameResponse(
                    game_id=game_data.get("game_id", ""),
                    external_id=game_data.get("external_id"),
                    sport=sport.lower(),
                    home_team=game_data.get("home_team", ""),
                    away_team=game_data.get("away_team", ""),
                    scheduled_at=game_data.get("scheduled_at", ""),
                    status=game_data.get("status", "scheduled"),
                    week=game_data.get("week"),
                    season=game_data.get("season"),
                    home_score=game_data.get("home_score"),
                    away_score=game_data.get("away_score"),
                    period=game_data.get("period"),
                    time_remaining=game_data.get("time_remaining"),
                    is_final=game_data.get("is_final", False),
                    venue=game_data.get("venue"),
                    attendance=game_data.get("attendance"),
                    weather=game_data.get("weather"),
                    broadcast=game_data.get("broadcast"),
                    officials=game_data.get("officials", []),
                    created_at=game_data.get("created_at"),
                    updated_at=game_data.get("updated_at"),
                )
                game_responses.append(game_response)

                # Collect teams
                if game_response.home_team:
                    teams_involved.add(game_response.home_team)
                if game_response.away_team:
                    teams_involved.add(game_response.away_team)

            except Exception as e:
                logger.warning(f"Failed to convert game data: {e}")
                continue

        # Sort games by scheduled time
        game_responses.sort(key=lambda g: g.scheduled_at)

        # Build date range info
        date_range = None
        if game_responses:
            dates = [g.scheduled_at.split('T')[0] for g in game_responses if g.scheduled_at]
            if dates:
                date_range = {
                    "start_date": min(dates),
                    "end_date": max(dates),
                    "total_days": len(set(dates))
                }

        response_data = ScheduleResponse(
            items=game_responses,
            total=len(game_responses),
            sport=sport,
            season=season,
            week=week,
            date_range=date_range,
            teams_involved=sorted(list(teams_involved)),
        )

        logger.info(
            f"Schedule request completed",
            extra={
                "user_id": str(current_user.user_id),
                "sport": sport,
                "games_count": len(game_responses),
                "teams_count": len(teams_involved),
            }
        )

        return StandardResponse(
            success=True,
            data=response_data,
            message=f"Found {len(game_responses)} games for {sport.upper()}"
        )

    except Exception as e:
        logger.error(
            f"Schedule request failed",
            extra={
                "user_id": str(current_user.user_id),
                "sport": sport,
                "error": str(e),
            }
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve schedule. Please try again later."
        )


@router.get("/schedule/{game_id}", response_model=StandardResponse[GameResponse])
async def get_game_details(
    game_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[GameResponse]:
    """
    Get detailed information for a specific game.

    - **game_id**: Unique game identifier

    Returns comprehensive game information.
    """
    try:
        logger.info(
            f"Game details request",
            extra={
                "user_id": str(current_user.user_id),
                "game_id": game_id,
            }
        )

        # Get sports data service
        sports_service = await get_sports_data_service()

        # Search for game across all sports
        game_data = None
        for sport in ["nfl", "mlb", "wnba"]:
            schedule = await sports_service.get_schedule(
                sport=sport.upper(),
                season="2024",  # Current season
                use_cache=True
            )
            game_data = next(
                (game for game in schedule if game.get("game_id") == game_id),
                None
            )
            if game_data:
                game_data["sport"] = sport
                break

        if not game_data:
            raise HTTPException(
                status_code=404,
                detail=f"Game with ID {game_id} not found"
            )

        # Convert to response model
        game_response = GameResponse(
            game_id=game_data.get("game_id", ""),
            external_id=game_data.get("external_id"),
            sport=game_data.get("sport", "").lower(),
            home_team=game_data.get("home_team", ""),
            away_team=game_data.get("away_team", ""),
            scheduled_at=game_data.get("scheduled_at", ""),
            status=game_data.get("status", "scheduled"),
            week=game_data.get("week"),
            season=game_data.get("season"),
            home_score=game_data.get("home_score"),
            away_score=game_data.get("away_score"),
            period=game_data.get("period"),
            time_remaining=game_data.get("time_remaining"),
            is_final=game_data.get("is_final", False),
            venue=game_data.get("venue"),
            attendance=game_data.get("attendance"),
            weather=game_data.get("weather"),
            broadcast=game_data.get("broadcast"),
            officials=game_data.get("officials", []),
            created_at=game_data.get("created_at"),
            updated_at=game_data.get("updated_at"),
        )

        logger.info(
            f"Game details completed",
            extra={
                "user_id": str(current_user.user_id),
                "game_id": game_id,
                "home_team": game_response.home_team,
                "away_team": game_response.away_team,
                "sport": game_response.sport,
            }
        )

        return StandardResponse(
            success=True,
            data=game_response,
            message=f"Game details for {game_response.away_team} @ {game_response.home_team}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Game details failed",
            extra={
                "user_id": str(current_user.user_id),
                "game_id": game_id,
                "error": str(e),
            }
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve game details. Please try again later."
        )


@router.get("/schedule/week/{sport}/{week}", response_model=StandardResponse[ScheduleResponse])
async def get_week_schedule(
    sport: str,
    week: int,
    season: Optional[str] = Query("2024", description="Season year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[ScheduleResponse]:
    """
    Get schedule for a specific week.

    - **sport**: Sport type (mlb, nfl, wnba)
    - **week**: Week number
    - **season**: Season year (default: 2024)

    Returns all games for the specified week.
    """
    return await get_schedule(
        sport=sport,
        season=season,
        week=week,
        db=db,
        current_user=current_user,
    )