"""
GET /api/v1/sports/players endpoint implementation.

Provides comprehensive player search and filtering with:
- Multi-sport player search (NFL, MLB, WNBA)
- Position-based filtering
- Team-based filtering
- Injury status filtering
- Active player filtering
- Text search by player name
- Pagination support
- Performance optimizations
- Response caching
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
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


class PlayerResponse(BaseModel):
    """Player response model."""

    player_id: str
    external_id: str
    name: str
    position: str
    team_id: str | None
    sport: str
    injury_status: str = "healthy"
    injury_description: str | None = None
    season_stats: dict | None = None
    game_stats: dict | None = None
    projections: dict | None = None
    created_at: str | None = None
    updated_at: str | None = None


class PlayersResponse(BaseModel):
    """Paginated players response model."""

    items: list[PlayerResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


@router.get("/players", response_model=StandardResponse[PlayersResponse])
async def get_players(
    sport: str = Query(..., description="Sport type", regex="^(mlb|nfl|wnba)$"),
    position: str | None = Query(None, description="Filter by position"),
    team: str | None = Query(None, description="Filter by team"),
    status: str | None = Query(
        None, description="Filter by status", regex="^(active|injured|inactive)$"
    ),
    search: str | None = Query(None, description="Search by player name"),
    limit: int = Query(50, description="Maximum results", ge=1, le=100),
    offset: int = Query(0, description="Results offset", ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[PlayersResponse]:
    """
    Search and filter players with comprehensive filtering options.

    - **sport**: Required sport type (mlb, nfl, wnba)
    - **position**: Optional position filter (e.g., QB, RB, WR for NFL)
    - **team**: Optional team filter (e.g., KC, BUF, NE for NFL)
    - **status**: Optional status filter (active, injured, inactive)
    - **search**: Optional text search by player name
    - **limit**: Maximum number of results (1-100, default 50)
    - **offset**: Results offset for pagination (default 0)

    Returns paginated list of players matching the criteria.
    """
    try:
        logger.info(
            "Players search request",
            extra={
                "user_id": str(current_user.user_id),
                "sport": sport,
                "position": position,
                "team": team,
                "search": search,
                "limit": limit,
                "offset": offset,
            },
        )

        # Get sports data service
        sports_service = await get_sports_data_service()

        # Handle text search
        if search:
            players_data = await sports_service.search_players(
                query=search,
                sport=sport.upper(),
                limit=limit + offset,  # Get extra to handle offset
                use_cache=True,
            )

            # Apply offset manually for search results
            players_data = players_data[offset : offset + limit]
            total_count = len(players_data)  # Approximate for search

        else:
            # Use structured filtering
            players_data = await sports_service.get_players(
                sport=sport.upper(),
                position=position,
                team=team,
                active_only=(status == "active" if status else True),
                use_cache=True,
            )

            # Apply pagination
            total_count = len(players_data)
            players_data = players_data[offset : offset + limit]

        # Apply status filter if specified
        if status:
            if status == "injured":
                players_data = [
                    p
                    for p in players_data
                    if p.get("injury_status", "healthy") not in ["healthy", ""]
                ]
            elif status == "inactive":
                players_data = [p for p in players_data if not p.get("active", True)]

        # Convert to response models
        player_responses = []
        for player_data in players_data:
            try:
                player_response = PlayerResponse(
                    player_id=player_data.get("player_id", ""),
                    external_id=player_data.get("external_id", ""),
                    name=player_data.get("name", ""),
                    position=player_data.get("position", ""),
                    team_id=player_data.get("team_id"),
                    sport=player_data.get("sport", sport.lower()),
                    injury_status=player_data.get("injury_status", "healthy"),
                    injury_description=player_data.get("injury_description"),
                    season_stats=player_data.get("season_stats"),
                    game_stats=player_data.get("game_stats"),
                    projections=player_data.get("projections"),
                    created_at=player_data.get("created_at"),
                    updated_at=player_data.get("updated_at"),
                )
                player_responses.append(player_response)

            except Exception as e:
                logger.warning(f"Failed to convert player data: {e}")
                continue

        # Calculate pagination metadata
        has_more = (offset + len(player_responses)) < total_count

        response_data = PlayersResponse(
            items=player_responses,
            total=total_count,
            limit=limit,
            offset=offset,
            has_more=has_more,
        )

        logger.info(
            "Players search completed",
            extra={
                "user_id": str(current_user.user_id),
                "results_count": len(player_responses),
                "total_count": total_count,
            },
        )

        return StandardResponse(
            success=True,
            data=response_data,
            message=f"Found {len(player_responses)} players",
        )

    except Exception as e:
        logger.error(
            "Players search failed",
            extra={
                "user_id": str(current_user.user_id),
                "error": str(e),
            },
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve players. Please try again later.",
        )


@router.get("/players/search", response_model=StandardResponse[PlayersResponse])
async def search_players_by_name(
    query: str = Query(..., description="Search query", min_length=2),
    sport: str = Query("nfl", description="Sport type", regex="^(mlb|nfl|wnba)$"),
    limit: int = Query(20, description="Maximum results", ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[PlayersResponse]:
    """
    Search players by name with text matching.

    - **query**: Search query (minimum 2 characters)
    - **sport**: Sport type to search within (default: nfl)
    - **limit**: Maximum number of results (1-50, default 20)

    Returns players whose names match the search query.
    """
    try:
        logger.info(
            "Player name search request",
            extra={
                "user_id": str(current_user.user_id),
                "query": query,
                "sport": sport,
                "limit": limit,
            },
        )

        # Get sports data service
        sports_service = await get_sports_data_service()

        # Perform text search
        players_data = await sports_service.search_players(
            query=query, sport=sport.upper(), limit=limit, use_cache=True
        )

        # Convert to response models
        player_responses = []
        for player_data in players_data:
            try:
                player_response = PlayerResponse(
                    player_id=player_data.get("player_id", ""),
                    external_id=player_data.get("external_id", ""),
                    name=player_data.get("name", ""),
                    position=player_data.get("position", ""),
                    team_id=player_data.get("team_id"),
                    sport=player_data.get("sport", sport.lower()),
                    injury_status=player_data.get("injury_status", "healthy"),
                    injury_description=player_data.get("injury_description"),
                    season_stats=player_data.get("season_stats"),
                    game_stats=player_data.get("game_stats"),
                    projections=player_data.get("projections"),
                )
                player_responses.append(player_response)

            except Exception as e:
                logger.warning(f"Failed to convert player data: {e}")
                continue

        response_data = PlayersResponse(
            items=player_responses,
            total=len(player_responses),
            limit=limit,
            offset=0,
            has_more=False,  # Search results don't support pagination
        )

        logger.info(
            "Player name search completed",
            extra={
                "user_id": str(current_user.user_id),
                "results_count": len(player_responses),
                "query": query,
            },
        )

        return StandardResponse(
            success=True,
            data=response_data,
            message=f"Found {len(player_responses)} players matching '{query}'",
        )

    except Exception as e:
        logger.error(
            "Player name search failed",
            extra={
                "user_id": str(current_user.user_id),
                "query": query,
                "error": str(e),
            },
        )

        raise HTTPException(
            status_code=500, detail="Failed to search players. Please try again later."
        )


@router.get("/players/positions/{sport}", response_model=StandardResponse[list[str]])
async def get_sport_positions(
    sport: str = Query(..., description="Sport type", regex="^(mlb|nfl|wnba)$"),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[list[str]]:
    """
    Get available positions for a sport.

    - **sport**: Sport type (mlb, nfl, wnba)

    Returns list of valid positions for the specified sport.
    """
    try:
        # Define positions by sport
        sport_positions = {
            "nfl": ["QB", "RB", "WR", "TE", "K", "DEF"],
            "mlb": ["C", "1B", "2B", "3B", "SS", "OF", "P"],
            "wnba": ["PG", "SG", "SF", "PF", "C"],
        }

        positions = sport_positions.get(sport.lower(), [])

        return StandardResponse(
            success=True,
            data=positions,
            message=f"Available positions for {sport.upper()}",
        )

    except Exception as e:
        logger.error(f"Failed to get sport positions: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve sport positions."
        )
