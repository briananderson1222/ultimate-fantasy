"""
GET /api/v1/sports/teams endpoint implementation.

Provides comprehensive team information with:
- Team listings by sport
- Team details and metadata
- Roster information
- Performance statistics
- Stadium and venue information
- Team branding and colors
- Conference and division data
"""

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


class TeamResponse(BaseModel):
    """Team response model."""

    team_id: str
    name: str
    city: str
    abbreviation: str
    sport: str
    conference: Optional[str] = None
    division: Optional[str] = None
    logo_url: Optional[str] = None
    colors: List[str] = Field(default_factory=list)
    founded_year: Optional[int] = None
    stadium: Optional[str] = None
    stadium_capacity: Optional[int] = None
    coach: Optional[str] = None
    website: Optional[str] = None


class TeamsResponse(BaseModel):
    """Teams list response model."""

    items: List[TeamResponse]
    total: int
    sport: str
    conferences: List[str] = Field(default_factory=list)
    divisions: List[str] = Field(default_factory=list)


@router.get("/teams", response_model=StandardResponse[TeamsResponse])
async def get_teams(
    sport: str = Query(..., description="Sport type", regex="^(mlb|nfl|wnba)$"),
    conference: Optional[str] = Query(None, description="Filter by conference"),
    division: Optional[str] = Query(None, description="Filter by division"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[TeamsResponse]:
    """
    Get teams for a specific sport with optional filtering.

    - **sport**: Required sport type (mlb, nfl, wnba)
    - **conference**: Optional conference filter (e.g., AFC, NFC for NFL)
    - **division**: Optional division filter (e.g., North, South, East, West)

    Returns list of teams with comprehensive team information.
    """
    try:
        logger.info(
            f"Teams request",
            extra={
                "user_id": str(current_user.user_id),
                "sport": sport,
                "conference": conference,
                "division": division,
            }
        )

        # Get sports data service
        sports_service = await get_sports_data_service()

        # Fetch teams data
        teams_data = await sports_service.get_teams(
            sport=sport.upper(),
            use_cache=True
        )

        if not teams_data:
            logger.warning(f"No teams found for sport: {sport}")
            return StandardResponse(
                success=True,
                data=TeamsResponse(
                    items=[],
                    total=0,
                    sport=sport,
                    conferences=[],
                    divisions=[],
                ),
                message=f"No teams found for {sport.upper()}"
            )

        # Apply filters
        filtered_teams = teams_data
        if conference:
            filtered_teams = [
                team for team in filtered_teams
                if team.get("conference", "").lower() == conference.lower()
            ]

        if division:
            filtered_teams = [
                team for team in filtered_teams
                if team.get("division", "").lower() == division.lower()
            ]

        # Convert to response models
        team_responses = []
        all_conferences = set()
        all_divisions = set()

        for team_data in filtered_teams:
            try:
                team_response = TeamResponse(
                    team_id=team_data.get("team_id", ""),
                    name=team_data.get("name", ""),
                    city=team_data.get("city", ""),
                    abbreviation=team_data.get("abbreviation", team_data.get("team_id", "")),
                    sport=sport.lower(),
                    conference=team_data.get("conference"),
                    division=team_data.get("division"),
                    logo_url=team_data.get("logo_url"),
                    colors=team_data.get("colors", []),
                    founded_year=team_data.get("founded_year"),
                    stadium=team_data.get("stadium"),
                    stadium_capacity=team_data.get("stadium_capacity"),
                    coach=team_data.get("coach"),
                    website=team_data.get("website"),
                )
                team_responses.append(team_response)

                # Collect unique conferences and divisions
                if team_response.conference:
                    all_conferences.add(team_response.conference)
                if team_response.division:
                    all_divisions.add(team_response.division)

            except Exception as e:
                logger.warning(f"Failed to convert team data: {e}")
                continue

        # Sort teams by city name
        team_responses.sort(key=lambda t: t.city)

        response_data = TeamsResponse(
            items=team_responses,
            total=len(team_responses),
            sport=sport,
            conferences=sorted(list(all_conferences)),
            divisions=sorted(list(all_divisions)),
        )

        logger.info(
            f"Teams request completed",
            extra={
                "user_id": str(current_user.user_id),
                "sport": sport,
                "teams_count": len(team_responses),
                "conferences_count": len(all_conferences),
                "divisions_count": len(all_divisions),
            }
        )

        return StandardResponse(
            success=True,
            data=response_data,
            message=f"Found {len(team_responses)} teams for {sport.upper()}"
        )

    except Exception as e:
        logger.error(
            f"Teams request failed",
            extra={
                "user_id": str(current_user.user_id),
                "sport": sport,
                "error": str(e),
            }
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve teams. Please try again later."
        )


@router.get("/teams/{team_id}", response_model=StandardResponse[TeamResponse])
async def get_team_details(
    team_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[TeamResponse]:
    """
    Get detailed information for a specific team.

    - **team_id**: Team identifier (e.g., KC, BUF, LAR)

    Returns comprehensive team information.
    """
    try:
        logger.info(
            f"Team details request",
            extra={
                "user_id": str(current_user.user_id),
                "team_id": team_id,
            }
        )

        # Get sports data service
        sports_service = await get_sports_data_service()

        # Search for team across all sports
        team_data = None
        for sport in ["nfl", "mlb", "wnba"]:
            teams = await sports_service.get_teams(sport=sport.upper(), use_cache=True)
            team_data = next(
                (team for team in teams if team.get("team_id") == team_id.upper()),
                None
            )
            if team_data:
                team_data["sport"] = sport
                break

        if not team_data:
            raise HTTPException(
                status_code=404,
                detail=f"Team with ID {team_id} not found"
            )

        # Convert to response model
        team_response = TeamResponse(
            team_id=team_data.get("team_id", ""),
            name=team_data.get("name", ""),
            city=team_data.get("city", ""),
            abbreviation=team_data.get("abbreviation", team_data.get("team_id", "")),
            sport=team_data.get("sport", "").lower(),
            conference=team_data.get("conference"),
            division=team_data.get("division"),
            logo_url=team_data.get("logo_url"),
            colors=team_data.get("colors", []),
            founded_year=team_data.get("founded_year"),
            stadium=team_data.get("stadium"),
            stadium_capacity=team_data.get("stadium_capacity"),
            coach=team_data.get("coach"),
            website=team_data.get("website"),
        )

        logger.info(
            f"Team details completed",
            extra={
                "user_id": str(current_user.user_id),
                "team_id": team_id,
                "team_name": team_response.name,
                "sport": team_response.sport,
            }
        )

        return StandardResponse(
            success=True,
            data=team_response,
            message=f"Team details for {team_response.name}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Team details failed",
            extra={
                "user_id": str(current_user.user_id),
                "team_id": team_id,
                "error": str(e),
            }
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve team details. Please try again later."
        )


@router.get("/teams/{team_id}/roster", response_model=StandardResponse[List[dict]])
async def get_team_roster(
    team_id: str,
    position: Optional[str] = Query(None, description="Filter by position"),
    active_only: bool = Query(True, description="Only active players"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[List[dict]]:
    """
    Get roster for a specific team.

    - **team_id**: Team identifier (e.g., KC, BUF, LAR)
    - **position**: Optional position filter
    - **active_only**: Only include active players (default: true)

    Returns list of players on the team roster.
    """
    try:
        logger.info(
            f"Team roster request",
            extra={
                "user_id": str(current_user.user_id),
                "team_id": team_id,
                "position": position,
                "active_only": active_only,
            }
        )

        # Get sports data service
        sports_service = await get_sports_data_service()

        # Find team sport first
        team_sport = None
        for sport in ["nfl", "mlb", "wnba"]:
            teams = await sports_service.get_teams(sport=sport.upper(), use_cache=True)
            if any(team.get("team_id") == team_id.upper() for team in teams):
                team_sport = sport
                break

        if not team_sport:
            raise HTTPException(
                status_code=404,
                detail=f"Team with ID {team_id} not found"
            )

        # Get team roster
        roster_data = await sports_service.get_players(
            sport=team_sport.upper(),
            team=team_id.upper(),
            position=position,
            active_only=active_only,
            use_cache=True
        )

        logger.info(
            f"Team roster completed",
            extra={
                "user_id": str(current_user.user_id),
                "team_id": team_id,
                "roster_size": len(roster_data),
                "sport": team_sport,
            }
        )

        return StandardResponse(
            success=True,
            data=roster_data,
            message=f"Found {len(roster_data)} players on {team_id} roster"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Team roster failed",
            extra={
                "user_id": str(current_user.user_id),
                "team_id": team_id,
                "error": str(e),
            }
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve team roster. Please try again later."
        )


@router.get("/conferences/{sport}", response_model=StandardResponse[List[str]])
async def get_sport_conferences(
    sport: str = Query(..., description="Sport type", regex="^(mlb|nfl|wnba)$"),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[List[str]]:
    """
    Get available conferences for a sport.

    - **sport**: Sport type (mlb, nfl, wnba)

    Returns list of conferences for the specified sport.
    """
    try:
        # Get sports data service
        sports_service = await get_sports_data_service()

        # Get all teams for sport
        teams_data = await sports_service.get_teams(
            sport=sport.upper(),
            use_cache=True
        )

        # Extract unique conferences
        conferences = list(set(
            team.get("conference") for team in teams_data
            if team.get("conference")
        ))
        conferences.sort()

        return StandardResponse(
            success=True,
            data=conferences,
            message=f"Available conferences for {sport.upper()}"
        )

    except Exception as e:
        logger.error(f"Failed to get sport conferences: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve sport conferences."
        )


@router.get("/divisions/{sport}", response_model=StandardResponse[List[str]])
async def get_sport_divisions(
    sport: str = Query(..., description="Sport type", regex="^(mlb|nfl|wnba)$"),
    conference: Optional[str] = Query(None, description="Filter by conference"),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[List[str]]:
    """
    Get available divisions for a sport.

    - **sport**: Sport type (mlb, nfl, wnba)
    - **conference**: Optional conference filter

    Returns list of divisions for the specified sport and conference.
    """
    try:
        # Get sports data service
        sports_service = await get_sports_data_service()

        # Get all teams for sport
        teams_data = await sports_service.get_teams(
            sport=sport.upper(),
            use_cache=True
        )

        # Apply conference filter if specified
        if conference:
            teams_data = [
                team for team in teams_data
                if team.get("conference", "").lower() == conference.lower()
            ]

        # Extract unique divisions
        divisions = list(set(
            team.get("division") for team in teams_data
            if team.get("division")
        ))
        divisions.sort()

        return StandardResponse(
            success=True,
            data=divisions,
            message=f"Available divisions for {sport.upper()}" +
                   (f" in {conference}" if conference else "")
        )

    except Exception as e:
        logger.error(f"Failed to get sport divisions: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve sport divisions."
        )