"""
GET /api/v1/sports/scores endpoint implementation.

Provides comprehensive live scores and game statistics with:
- Real-time game scores and updates
- Player statistics and performance
- Fantasy point calculations
- Live game tracking
- Historical score data
- Game state information
- Player performance highlights
"""

from datetime import date, datetime
from typing import Dict, List, Optional

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


class PlayerGameStats(BaseModel):
    """Player game statistics model."""

    player_id: str
    player_name: str
    position: str
    team: str
    stats: Dict[str, float] = Field(default_factory=dict)
    fantasy_points: float = 0.0
    is_final: bool = False
    updated_at: Optional[str] = None


class GameScore(BaseModel):
    """Game score model."""

    game_id: str
    sport: str
    home_team: str
    away_team: str
    home_score: int = 0
    away_score: int = 0
    status: str = "scheduled"  # scheduled, in_progress, final, postponed, cancelled

    # Game state
    period: Optional[int] = None
    time_remaining: Optional[str] = None
    is_final: bool = False

    # Game information
    scheduled_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    # Additional data
    venue: Optional[str] = None
    attendance: Optional[int] = None
    weather: Optional[str] = None

    # Last update information
    last_updated: str
    update_frequency: Optional[str] = None  # live, final, etc.


class ScoresResponse(BaseModel):
    """Scores response model."""

    games: List[GameScore]
    player_stats: List[PlayerGameStats] = Field(default_factory=list)
    sport: str
    date: Optional[str] = None
    live_games_count: int = 0
    completed_games_count: int = 0
    total_games: int = 0
    last_updated: str


@router.get("/scores", response_model=StandardResponse[ScoresResponse])
async def get_scores(
    sport: str = Query(..., description="Sport type", regex="^(mlb|nfl|wnba)$"),
    date: Optional[date] = Query(None, description="Specific date (YYYY-MM-DD)"),
    live_only: bool = Query(False, description="Only in-progress games"),
    include_player_stats: bool = Query(False, description="Include player statistics"),
    team: Optional[str] = Query(None, description="Filter by team"),
    week: Optional[int] = Query(None, description="Specific week number"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[ScoresResponse]:
    """
    Get live scores and game statistics.

    - **sport**: Required sport type (mlb, nfl, wnba)
    - **date**: Optional specific date (defaults to today)
    - **live_only**: Only return in-progress games (default: false)
    - **include_player_stats**: Include player statistics (default: false)
    - **team**: Optional team filter
    - **week**: Optional week number for schedule context

    Returns real-time game scores with optional player statistics.
    """
    try:
        logger.info(
            f"Scores request",
            extra={
                "user_id": str(current_user.user_id),
                "sport": sport,
                "date": str(date) if date else None,
                "live_only": live_only,
                "include_player_stats": include_player_stats,
                "team": team,
            }
        )

        # Get sports data service
        sports_service = await get_sports_data_service()

        # Fetch scores data
        scores_data = await sports_service.get_scores(
            sport=sport.upper(),
            date=date,
            live_only=live_only,
            use_cache=False  # Always get fresh score data
        )

        if not scores_data:
            logger.warning(f"No scores found for {sport} on {date}")
            return StandardResponse(
                success=True,
                data=ScoresResponse(
                    games=[],
                    player_stats=[],
                    sport=sport,
                    date=str(date) if date else None,
                    live_games_count=0,
                    completed_games_count=0,
                    total_games=0,
                    last_updated=datetime.utcnow().isoformat(),
                ),
                message=f"No games found for {sport.upper()}"
            )

        # Filter by team if specified
        if team:
            scores_data = [
                game for game in scores_data
                if game.get("home_team", "").upper() == team.upper() or
                   game.get("away_team", "").upper() == team.upper()
            ]

        # Convert to response models
        game_scores = []
        live_count = 0
        completed_count = 0

        for game_data in scores_data:
            try:
                # Determine if game is live or completed
                status = game_data.get("status", "scheduled").lower()
                is_live = status == "in_progress"
                is_completed = status == "final"

                if is_live:
                    live_count += 1
                elif is_completed:
                    completed_count += 1

                game_score = GameScore(
                    game_id=game_data.get("game_id", ""),
                    sport=sport.lower(),
                    home_team=game_data.get("home_team", ""),
                    away_team=game_data.get("away_team", ""),
                    home_score=game_data.get("home_score", 0),
                    away_score=game_data.get("away_score", 0),
                    status=status,
                    period=game_data.get("period"),
                    time_remaining=game_data.get("time_remaining"),
                    is_final=is_completed,
                    scheduled_at=game_data.get("scheduled_at"),
                    started_at=game_data.get("started_at"),
                    completed_at=game_data.get("completed_at"),
                    venue=game_data.get("venue"),
                    attendance=game_data.get("attendance"),
                    weather=game_data.get("weather"),
                    last_updated=game_data.get("last_updated", datetime.utcnow().isoformat()),
                    update_frequency="live" if is_live else "final" if is_completed else "scheduled",
                )
                game_scores.append(game_score)

            except Exception as e:
                logger.warning(f"Failed to convert game score data: {e}")
                continue

        # Sort games by status (live first, then by start time)
        game_scores.sort(key=lambda g: (
            0 if g.status == "in_progress" else 1 if g.status == "final" else 2,
            g.scheduled_at or ""
        ))

        # Get player stats if requested
        player_stats = []
        if include_player_stats:
            player_stats = await _get_player_game_stats(
                sports_service, sport, game_scores, date
            )

        response_data = ScoresResponse(
            games=game_scores,
            player_stats=player_stats,
            sport=sport,
            date=str(date) if date else None,
            live_games_count=live_count,
            completed_games_count=completed_count,
            total_games=len(game_scores),
            last_updated=datetime.utcnow().isoformat(),
        )

        logger.info(
            f"Scores request completed",
            extra={
                "user_id": str(current_user.user_id),
                "sport": sport,
                "total_games": len(game_scores),
                "live_games": live_count,
                "completed_games": completed_count,
                "player_stats_count": len(player_stats),
            }
        )

        return StandardResponse(
            success=True,
            data=response_data,
            message=f"Found {len(game_scores)} games for {sport.upper()}"
        )

    except Exception as e:
        logger.error(
            f"Scores request failed",
            extra={
                "user_id": str(current_user.user_id),
                "sport": sport,
                "error": str(e),
            }
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve scores. Please try again later."
        )


@router.get("/scores/live", response_model=StandardResponse[ScoresResponse])
async def get_live_scores(
    sport: Optional[str] = Query(None, description="Sport type", regex="^(mlb|nfl|wnba)$"),
    include_player_stats: bool = Query(True, description="Include player statistics"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[ScoresResponse]:
    """
    Get only live (in-progress) games with real-time updates.

    - **sport**: Optional sport filter (returns all sports if not specified)
    - **include_player_stats**: Include live player statistics (default: true)

    Returns only games that are currently in progress.
    """
    if sport:
        return await get_scores(
            sport=sport,
            live_only=True,
            include_player_stats=include_player_stats,
            db=db,
            current_user=current_user,
        )
    else:
        # Get live scores for all sports
        all_live_games = []
        all_player_stats = []
        total_live = 0

        for sport_type in ["nfl", "mlb", "wnba"]:
            try:
                sport_response = await get_scores(
                    sport=sport_type,
                    live_only=True,
                    include_player_stats=include_player_stats,
                    db=db,
                    current_user=current_user,
                )

                if sport_response.success and sport_response.data:
                    all_live_games.extend(sport_response.data.games)
                    all_player_stats.extend(sport_response.data.player_stats)
                    total_live += sport_response.data.live_games_count

            except Exception as e:
                logger.warning(f"Failed to get live scores for {sport_type}: {e}")
                continue

        # Sort by sport and start time
        all_live_games.sort(key=lambda g: (g.sport, g.scheduled_at or ""))

        response_data = ScoresResponse(
            games=all_live_games,
            player_stats=all_player_stats,
            sport="all",
            live_games_count=total_live,
            completed_games_count=0,
            total_games=len(all_live_games),
            last_updated=datetime.utcnow().isoformat(),
        )

        return StandardResponse(
            success=True,
            data=response_data,
            message=f"Found {total_live} live games across all sports"
        )


@router.get("/scores/{game_id}", response_model=StandardResponse[GameScore])
async def get_game_score(
    game_id: str,
    include_player_stats: bool = Query(False, description="Include player statistics"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[GameScore]:
    """
    Get score and details for a specific game.

    - **game_id**: Unique game identifier
    - **include_player_stats**: Include player statistics (default: false)

    Returns real-time score information for the specified game.
    """
    try:
        logger.info(
            f"Game score request",
            extra={
                "user_id": str(current_user.user_id),
                "game_id": game_id,
            }
        )

        # Get sports data service
        sports_service = await get_sports_data_service()

        # Search for game across all sports
        game_data = None
        sport_found = None

        for sport in ["nfl", "mlb", "wnba"]:
            scores = await sports_service.get_scores(
                sport=sport.upper(),
                use_cache=False  # Get fresh data
            )

            game_data = next(
                (game for game in scores if game.get("game_id") == game_id),
                None
            )

            if game_data:
                sport_found = sport
                break

        if not game_data:
            raise HTTPException(
                status_code=404,
                detail=f"Game with ID {game_id} not found"
            )

        # Convert to response model
        status = game_data.get("status", "scheduled").lower()
        is_completed = status == "final"

        game_score = GameScore(
            game_id=game_data.get("game_id", ""),
            sport=sport_found.lower(),
            home_team=game_data.get("home_team", ""),
            away_team=game_data.get("away_team", ""),
            home_score=game_data.get("home_score", 0),
            away_score=game_data.get("away_score", 0),
            status=status,
            period=game_data.get("period"),
            time_remaining=game_data.get("time_remaining"),
            is_final=is_completed,
            scheduled_at=game_data.get("scheduled_at"),
            started_at=game_data.get("started_at"),
            completed_at=game_data.get("completed_at"),
            venue=game_data.get("venue"),
            attendance=game_data.get("attendance"),
            weather=game_data.get("weather"),
            last_updated=game_data.get("last_updated", datetime.utcnow().isoformat()),
            update_frequency="live" if status == "in_progress" else "final" if is_completed else "scheduled",
        )

        logger.info(
            f"Game score completed",
            extra={
                "user_id": str(current_user.user_id),
                "game_id": game_id,
                "home_team": game_score.home_team,
                "away_team": game_score.away_team,
                "status": game_score.status,
            }
        )

        return StandardResponse(
            success=True,
            data=game_score,
            message=f"Game score for {game_score.away_team} @ {game_score.home_team}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Game score failed",
            extra={
                "user_id": str(current_user.user_id),
                "game_id": game_id,
                "error": str(e),
            }
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve game score. Please try again later."
        )


@router.get("/scores/{game_id}/stats", response_model=StandardResponse[List[PlayerGameStats]])
async def get_game_player_stats(
    game_id: str,
    team: Optional[str] = Query(None, description="Filter by team"),
    position: Optional[str] = Query(None, description="Filter by position"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[List[PlayerGameStats]]:
    """
    Get player statistics for a specific game.

    - **game_id**: Unique game identifier
    - **team**: Optional team filter
    - **position**: Optional position filter

    Returns player statistics for the specified game.
    """
    try:
        logger.info(
            f"Game player stats request",
            extra={
                "user_id": str(current_user.user_id),
                "game_id": game_id,
                "team": team,
                "position": position,
            }
        )

        # Get game info first
        game_response = await get_game_score(game_id, db=db, current_user=current_user)

        if not game_response.success or not game_response.data:
            raise HTTPException(
                status_code=404,
                detail=f"Game with ID {game_id} not found"
            )

        game_score = game_response.data

        # Get sports data service
        sports_service = await get_sports_data_service()

        # Get player stats for this game
        player_stats = await _get_game_specific_player_stats(
            sports_service, game_score.sport, game_id, team, position
        )

        logger.info(
            f"Game player stats completed",
            extra={
                "user_id": str(current_user.user_id),
                "game_id": game_id,
                "stats_count": len(player_stats),
            }
        )

        return StandardResponse(
            success=True,
            data=player_stats,
            message=f"Found {len(player_stats)} player stat records for game"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Game player stats failed",
            extra={
                "user_id": str(current_user.user_id),
                "game_id": game_id,
                "error": str(e),
            }
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve game player statistics. Please try again later."
        )


# Helper functions

async def _get_player_game_stats(
    sports_service,
    sport: str,
    game_scores: List[GameScore],
    target_date: Optional[date],
) -> List[PlayerGameStats]:
    """Get player statistics for multiple games."""
    try:
        player_stats = []

        # For each game, get player stats
        for game in game_scores:
            if game.status in ["in_progress", "final"]:
                game_stats = await _get_game_specific_player_stats(
                    sports_service, sport, game.game_id
                )
                player_stats.extend(game_stats)

        return player_stats

    except Exception as e:
        logger.warning(f"Failed to get player game stats: {e}")
        return []


async def _get_game_specific_player_stats(
    sports_service,
    sport: str,
    game_id: str,
    team_filter: Optional[str] = None,
    position_filter: Optional[str] = None,
) -> List[PlayerGameStats]:
    """Get player statistics for a specific game."""
    try:
        # This would fetch player stats for the specific game
        # Implementation depends on how game stats are stored and accessed

        # Placeholder implementation
        mock_stats = [
            PlayerGameStats(
                player_id="player_123",
                player_name="Mock Player",
                position="QB",
                team="KC",
                stats={
                    "passing_yards": 275,
                    "passing_tds": 2,
                    "rushing_yards": 15,
                },
                fantasy_points=18.5,
                is_final=True,
                updated_at=datetime.utcnow().isoformat(),
            )
        ]

        # Apply filters
        if team_filter:
            mock_stats = [stat for stat in mock_stats if stat.team.upper() == team_filter.upper()]

        if position_filter:
            mock_stats = [stat for stat in mock_stats if stat.position.upper() == position_filter.upper()]

        return mock_stats

    except Exception as e:
        logger.warning(f"Failed to get game-specific player stats: {e}")
        return []