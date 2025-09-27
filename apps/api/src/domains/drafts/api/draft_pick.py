"""
POST /api/v1/draft/{leagueId}/pick endpoint implementation.

Provides draft pick submission and validation functionality including:
- Pick validation against draft order and timing
- Player availability verification
- Real-time pick broadcasting to all participants
- Auto-draft handling for timeout scenarios
- Pick history tracking and validation
- Integration with timer and WebSocket systems
"""

from datetime import datetime

from domains.teams.models.team import Team
from fastapi import APIRouter, Body, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from api.models.response import StandardResponse
from domains.drafts.services.draft_timer import get_draft_timer_service
from domains.leagues.models.league import League
from domains.sports.services.sports_data_service import get_sports_data_service
from domains.users.models.user import User

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging

    get_logger = logging.getLogger  # type: ignore[assignment]

logger = get_logger(__name__)

router = APIRouter()


class DraftPickRequest(BaseModel):
    """Request model for making a draft pick."""

    player_id: str = Field(..., description="External player ID to draft")
    team_id: str = Field(..., description="Team making the pick")
    pick_type: str = Field(
        default="manual",
        regex="^(manual|auto)$",
        description="Type of pick (manual or auto)",
    )


class DraftPickResponse(BaseModel):
    """Response model for draft pick."""

    pick_id: str
    overall_pick: int
    round_number: int
    pick_in_round: int
    team_id: str
    team_name: str
    player_id: str
    player_info: dict
    pick_time: str
    is_autopick: bool
    time_remaining: int | None
    next_pick: dict | None
    draft_status: dict


class PickValidationError(BaseModel):
    """Error details for pick validation."""

    error_type: str
    message: str
    details: dict


@router.post(
    "/draft/{league_id}/pick", response_model=StandardResponse[DraftPickResponse]
)
async def make_draft_pick(
    league_id: str = Path(..., description="League ID for the draft"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: DraftPickRequest = Body(...),
) -> StandardResponse[DraftPickResponse]:
    """
    Submit a draft pick for the current draft.

    This endpoint handles pick submission with comprehensive validation:
    - Verifies it's the correct team's turn to pick
    - Validates player availability and eligibility
    - Ensures pick is within time limits
    - Broadcasts pick to all draft participants via WebSocket
    - Advances to next pick automatically
    - Returns updated draft status

    **Requirements:**
    - User must own the team making the pick
    - Must be the team's turn according to draft order
    - Player must be available (not already drafted)
    - Pick must be made within time limit (unless paused)
    - Draft must be active

    **Returns:**
    - Pick details and player information
    - Next pick information
    - Updated draft status and timer
    """
    try:
        logger.info(
            "Draft pick request",
            extra={
                "user_id": str(current_user.user_id),
                "league_id": league_id,
                "team_id": request.team_id,
                "player_id": request.player_id,
                "pick_type": request.pick_type,
            },
        )

        # Validate league exists
        league = db.query(League).filter(League.league_id == league_id).first()

        if not league:
            raise HTTPException(status_code=404, detail=f"League {league_id} not found")

        # Validate draft is active
        if league.status != "drafting":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot make pick for league in '{league.status}' status. Draft must be active.",
            )

        # Get draft timer
        draft_timer_service = get_draft_timer_service()
        draft_timer = draft_timer_service.get_draft_timer(league_id)

        if not draft_timer:
            raise HTTPException(
                status_code=404, detail="No active draft found for this league"
            )

        # Validate user's team
        team = (
            db.query(Team)
            .filter(
                Team.team_id == request.team_id,
                Team.league_id == league_id,
                Team.owner_id == current_user.user_id,
            )
            .first()
        )

        if not team:
            raise HTTPException(
                status_code=403, detail="You can only make picks for your own team"
            )

        # Get current draft status
        timer_status = draft_timer.get_timer_status()
        current_pick = timer_status.get("current_pick")

        if not current_pick:
            raise HTTPException(
                status_code=400, detail="Draft is complete or no current pick available"
            )

        # Validate it's this team's turn
        if current_pick["team_id"] != request.team_id:
            expected_team = current_pick["team_id"]
            raise HTTPException(
                status_code=400,
                detail=f"It's not your turn to pick. Current pick belongs to team {expected_team}",
            )

        # Validate player is available
        sports_service = await get_sports_data_service()
        player_data = await sports_service.get_player_details(request.player_id)

        if not player_data:
            raise HTTPException(
                status_code=404, detail=f"Player {request.player_id} not found"
            )

        # Check if player is already drafted
        completed_picks = timer_status.get("completed_picks", 0)
        draft_order = draft_timer.draft_order

        already_drafted = False
        for pick in draft_order.picks[:completed_picks]:
            if pick.player_id == request.player_id:
                already_drafted = True
                break

        if already_drafted:
            raise HTTPException(
                status_code=409,
                detail=f"Player {request.player_id} has already been drafted",
            )

        # Validate pick timing (unless auto-pick)
        if request.pick_type == "manual" and not timer_status.get("is_paused", False):
            time_remaining = timer_status.get("time_remaining", 0)
            if time_remaining <= 0:
                raise HTTPException(
                    status_code=408,
                    detail="Pick time has expired. Pick will be processed as auto-pick.",
                )

        # Make the pick
        overall_pick = current_pick["overall_pick"]
        success = await draft_timer.make_pick(
            overall_pick=overall_pick,
            team_id=request.team_id,
            player_id=request.player_id,
        )

        if not success:
            raise HTTPException(
                status_code=400, detail="Failed to process pick. Please try again."
            )

        # Get updated timer status
        updated_status = draft_timer.get_timer_status()
        next_pick = updated_status.get("current_pick")

        # Format player information
        player_info = {
            "player_id": request.player_id,
            "name": player_data.get("name", "Unknown Player"),
            "position": player_data.get("position", ""),
            "team": player_data.get("team", ""),
            "sport": player_data.get("sport", ""),
            "stats": player_data.get("season_stats", {}),
            "injury_status": player_data.get("injury_status", "healthy"),
        }

        # Create response
        response_data = DraftPickResponse(
            pick_id=f"{league_id}_{overall_pick}",
            overall_pick=overall_pick,
            round_number=current_pick["round_number"],
            pick_in_round=current_pick["pick_in_round"],
            team_id=request.team_id,
            team_name=team.team_name,
            player_id=request.player_id,
            player_info=player_info,
            pick_time=datetime.utcnow().isoformat(),
            is_autopick=(request.pick_type == "auto"),
            time_remaining=updated_status.get("time_remaining"),
            next_pick=next_pick,
            draft_status={
                "status": updated_status["status"],
                "completed_picks": updated_status["completed_picks"],
                "total_picks": updated_status["total_picks"],
                "is_paused": updated_status["is_paused"],
            },
        )

        logger.info(
            "Draft pick completed",
            extra={
                "user_id": str(current_user.user_id),
                "league_id": league_id,
                "team_id": request.team_id,
                "player_id": request.player_id,
                "overall_pick": overall_pick,
                "round_number": current_pick["round_number"],
                "pick_type": request.pick_type,
            },
        )

        return StandardResponse(
            success=True,
            data=response_data,
            message=f"Pick {overall_pick}: {team.team_name} selects {player_info['name']}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to process draft pick",
            extra={
                "user_id": str(current_user.user_id),
                "league_id": league_id,
                "team_id": request.team_id,
                "player_id": request.player_id,
                "error": str(e),
            },
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to process draft pick. Please try again later.",
        )


@router.get("/draft/{league_id}/picks", response_model=StandardResponse[list[dict]])
async def get_draft_picks(
    league_id: str = Path(..., description="League ID for the draft"),
    round_number: int | None = None,
    team_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[list[dict]]:
    """
    Get draft picks for a league.

    Returns historical and current pick information with optional filtering:
    - All completed picks with player details
    - Optional filtering by round or team
    - Pick timing and auto-pick indicators
    - Player information and team context

    **Query Parameters:**
    - **round_number**: Filter picks by specific round
    - **team_id**: Filter picks by specific team

    **Returns:**
    - List of completed picks with player details
    - Pick timing and context information
    """
    try:
        logger.info(
            "Draft picks request",
            extra={
                "user_id": str(current_user.user_id),
                "league_id": league_id,
                "round_number": round_number,
                "team_id": team_id,
            },
        )

        # Validate league and user access
        league = db.query(League).filter(League.league_id == league_id).first()

        if not league:
            raise HTTPException(status_code=404, detail=f"League {league_id} not found")

        # Check if user is member of the league
        user_team = (
            db.query(Team)
            .filter(Team.league_id == league_id, Team.owner_id == current_user.user_id)
            .first()
        )

        if not user_team and league.commissioner_id != current_user.user_id:
            raise HTTPException(
                status_code=403,
                detail="You must be a league member to view draft picks",
            )

        # Get draft timer
        draft_timer_service = get_draft_timer_service()
        draft_timer = draft_timer_service.get_draft_timer(league_id)

        if not draft_timer:
            return StandardResponse(
                success=True, data=[], message="No draft found for this league"
            )

        # Get all picks
        draft_order = draft_timer.draft_order
        sports_service = await get_sports_data_service()

        # Filter completed picks
        completed_picks = []
        for pick in draft_order.picks:
            if not pick.player_id or pick.player_id == "AUTO_PICK_PLACEHOLDER":
                continue

            # Apply filters
            if round_number and pick.round_number != round_number:
                continue

            if team_id and pick.team_id != team_id:
                continue

            # Get team info
            team = db.query(Team).filter(Team.team_id == pick.team_id).first()

            # Get player info
            player_data = {}
            if pick.player_id != "AUTO_PICK_PLACEHOLDER":
                try:
                    player_data = (
                        await sports_service.get_player_details(pick.player_id) or {}
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to get player data for {pick.player_id}: {e}"
                    )

            pick_data = {
                "overall_pick": pick.overall_pick,
                "round_number": pick.round_number,
                "pick_in_round": pick.pick_in_round,
                "team_id": pick.team_id,
                "team_name": team.team_name if team else "Unknown Team",
                "player_id": pick.player_id,
                "player_info": {
                    "name": player_data.get("name", "Unknown Player"),
                    "position": player_data.get("position", ""),
                    "team": player_data.get("team", ""),
                    "sport": player_data.get("sport", ""),
                },
                "pick_time": pick.pick_time.isoformat() if pick.pick_time else None,
                "is_autopick": pick.is_autopick,
                "is_keeper": pick.is_keeper,
            }

            completed_picks.append(pick_data)

        # Sort by overall pick
        completed_picks.sort(key=lambda x: x["overall_pick"])

        logger.info(
            "Draft picks retrieved",
            extra={
                "user_id": str(current_user.user_id),
                "league_id": league_id,
                "picks_count": len(completed_picks),
                "round_filter": round_number,
                "team_filter": team_id,
            },
        )

        return StandardResponse(
            success=True,
            data=completed_picks,
            message=f"Retrieved {len(completed_picks)} draft picks",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get draft picks",
            extra={
                "user_id": str(current_user.user_id),
                "league_id": league_id,
                "error": str(e),
            },
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve draft picks. Please try again later.",
        )


@router.get(
    "/draft/{league_id}/available-players", response_model=StandardResponse[list[dict]]
)
async def get_available_players(
    league_id: str = Path(..., description="League ID for the draft"),
    sport: str | None = None,
    position: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[list[dict]]:
    """
    Get available players for drafting.

    Returns players that haven't been drafted yet, with optional filtering:
    - Excludes already drafted players
    - Optional sport and position filtering
    - Search by player name
    - Pagination support

    **Query Parameters:**
    - **sport**: Filter by sport (nfl, mlb, wnba)
    - **position**: Filter by position
    - **search**: Search player names
    - **limit**: Number of results (default: 50, max: 100)
    - **offset**: Pagination offset

    **Returns:**
    - List of available players with stats and projections
    """
    try:
        logger.info(
            "Available players request",
            extra={
                "user_id": str(current_user.user_id),
                "league_id": league_id,
                "sport": sport,
                "position": position,
                "search": search,
            },
        )

        # Validate league and user access
        league = db.query(League).filter(League.league_id == league_id).first()

        if not league:
            raise HTTPException(status_code=404, detail=f"League {league_id} not found")

        # Check if user is member of the league
        user_team = (
            db.query(Team)
            .filter(Team.league_id == league_id, Team.owner_id == current_user.user_id)
            .first()
        )

        if not user_team and league.commissioner_id != current_user.user_id:
            raise HTTPException(
                status_code=403,
                detail="You must be a league member to view available players",
            )

        # Validate limit
        limit = min(limit, 100)

        # Get drafted players
        drafted_players = set()
        draft_timer_service = get_draft_timer_service()
        draft_timer = draft_timer_service.get_draft_timer(league_id)

        if draft_timer:
            for pick in draft_timer.draft_order.picks:
                if pick.player_id and pick.player_id != "AUTO_PICK_PLACEHOLDER":
                    drafted_players.add(pick.player_id)

        # Get sports data service
        sports_service = await get_sports_data_service()

        # Get players
        players_data = await sports_service.search_players(
            query=search or "",
            sport=sport.upper() if sport else "NFL",
            limit=limit + len(drafted_players),
            use_cache=True,
        )

        # Filter out drafted players
        available_players = []
        for player in players_data:
            if player.get("player_id") not in drafted_players:
                available_players.append(
                    {
                        "player_id": player.get("player_id"),
                        "name": player.get("name"),
                        "position": player.get("position"),
                        "team": player.get("team"),
                        "sport": player.get("sport"),
                        "injury_status": player.get("injury_status", "healthy"),
                        "season_stats": player.get("season_stats", {}),
                        "projections": player.get("projections", {}),
                    }
                )

            # Stop when we have enough
            if len(available_players) >= limit:
                break

        logger.info(
            "Available players retrieved",
            extra={
                "user_id": str(current_user.user_id),
                "league_id": league_id,
                "available_count": len(available_players),
                "drafted_count": len(drafted_players),
            },
        )

        return StandardResponse(
            success=True,
            data=available_players,
            message=f"Found {len(available_players)} available players",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get available players",
            extra={
                "user_id": str(current_user.user_id),
                "league_id": league_id,
                "error": str(e),
            },
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve available players. Please try again later.",
        )
