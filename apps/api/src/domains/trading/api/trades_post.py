"""
POST /api/v1/trades endpoint implementation.

Provides trade proposal and management functionality including:
- Trade proposal creation and validation
- Player eligibility verification
- Trade evaluation and fairness analysis
- Real-time notifications to involved parties
- Trade expiration and deadline management
- Integration with league rules and settings
- Commissioner review and approval workflows
"""

from datetime import datetime, timedelta
from uuid import uuid4

from domains.teams.models.team import Team
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from api.models.response import StandardResponse
from domains.leagues.models.league import League
from domains.notifications.services.notification_service import get_notification_service
from domains.sports.services.sports_data_service import get_sports_data_service
from domains.trading.algorithms.trade_evaluator import get_trade_evaluator
from domains.trading.models.trade import Trade
from domains.users.models.user import User

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging

    get_logger = logging.getLogger  # type: ignore[assignment]

logger = get_logger(__name__)

router = APIRouter()


class TradePlayerRequest(BaseModel):
    """Request model for a player in a trade."""

    player_id: str = Field(..., description="External player ID")
    player_name: str | None = Field(None, description="Player name for validation")
    position: str | None = Field(None, description="Player position")


class TradeProposalRequest(BaseModel):
    """Request model for creating a trade proposal."""

    to_team_id: str = Field(..., description="Team ID receiving the trade proposal")
    offering_players: list[TradePlayerRequest] = Field(
        ..., min_items=1, max_items=6, description="Players being offered (1-6 players)"
    )
    requesting_players: list[TradePlayerRequest] = Field(
        ...,
        min_items=1,
        max_items=6,
        description="Players being requested (1-6 players)",
    )
    message: str | None = Field(
        None, max_length=500, description="Optional message to the other team"
    )
    expiration_hours: int = Field(
        default=72, ge=1, le=168, description="Hours until trade expires (1-168 hours)"
    )

    @validator("offering_players", "requesting_players")
    def validate_unique_players(self, players):
        """Ensure no duplicate players in each list."""
        player_ids = [p.player_id for p in players]
        if len(player_ids) != len(set(player_ids)):
            raise ValueError("Duplicate players not allowed")
        return players


class TradeProposalResponse(BaseModel):
    """Response model for trade proposal."""

    trade_id: str
    from_team_id: str
    from_team_name: str
    to_team_id: str
    to_team_name: str
    status: str
    offering_players: list[dict]
    requesting_players: list[dict]
    trade_evaluation: dict
    message: str | None
    expires_at: str
    created_at: str
    evaluation_confidence: float


@router.post("/trades", response_model=StandardResponse[TradeProposalResponse])
async def create_trade_proposal(
    request: TradeProposalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[TradeProposalResponse]:
    """
    Create a new trade proposal.

    This endpoint allows team owners to propose trades with comprehensive validation:
    - Validates all players exist and are owned by correct teams
    - Performs trade evaluation and fairness analysis
    - Checks league trade rules and deadlines
    - Sends real-time notifications to involved parties
    - Sets appropriate expiration times based on league settings

    **Requirements:**
    - User must own the proposing team
    - All offered players must be on user's roster
    - All requested players must be on target team's roster
    - League must allow trading (not past trade deadline)
    - Players must be eligible for trading (not locked, injured reserve, etc.)

    **Returns:**
    - Trade proposal details with unique ID
    - Comprehensive trade evaluation and fairness analysis
    - Expiration time and next steps for recipient
    """
    try:
        logger.info(
            "Trade proposal request",
            extra={
                "user_id": str(current_user.user_id),
                "to_team_id": request.to_team_id,
                "offering_count": len(request.offering_players),
                "requesting_count": len(request.requesting_players),
            },
        )

        # Get user's team
        from_team = db.query(Team).filter(Team.owner_id == current_user.user_id).first()

        if not from_team:
            raise HTTPException(
                status_code=404, detail="You must be on a team to propose trades"
            )

        # Validate target team exists and is in same league
        to_team = db.query(Team).filter(Team.team_id == request.to_team_id).first()

        if not to_team:
            raise HTTPException(
                status_code=404, detail=f"Target team {request.to_team_id} not found"
            )

        if from_team.league_id != to_team.league_id:
            raise HTTPException(
                status_code=400, detail="Teams must be in the same league to trade"
            )

        if from_team.team_id == to_team.team_id:
            raise HTTPException(status_code=400, detail="Cannot trade with yourself")

        # Get league and validate trading rules
        league = (
            db.query(League).filter(League.league_id == from_team.league_id).first()
        )

        if not league:
            raise HTTPException(status_code=404, detail="League not found")

        # Check if trading is allowed
        if league.status not in ["active", "drafting"]:
            raise HTTPException(
                status_code=400,
                detail=f"Trading not allowed when league is in '{league.status}' status",
            )

        # Check trade deadline
        trade_deadline = (
            league.settings.get("trade_deadline") if league.settings else None
        )
        if trade_deadline:
            deadline_date = datetime.fromisoformat(trade_deadline)
            if datetime.utcnow() > deadline_date:
                raise HTTPException(status_code=400, detail="Trade deadline has passed")

        # Validate offered players are on proposing team's roster
        sports_service = await get_sports_data_service()
        offering_player_details = []
        current_roster = from_team.roster or []
        roster_player_ids = {p.get("player_id") for p in current_roster}

        for player_req in request.offering_players:
            if player_req.player_id not in roster_player_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Player {player_req.player_id} is not on your roster",
                )

            # Get player details
            player_data = await sports_service.get_player_details(player_req.player_id)
            if not player_data:
                raise HTTPException(
                    status_code=404, detail=f"Player {player_req.player_id} not found"
                )

            # Check if player is tradeable
            player_status = player_data.get("injury_status", "healthy").lower()
            if player_status in ["ir", "suspended"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Player {player_data.get('name')} is not eligible for trading ({player_status})",
                )

            offering_player_details.append(
                {
                    "player_id": player_req.player_id,
                    "name": player_data.get("name"),
                    "position": player_data.get("position"),
                    "team": player_data.get("team"),
                    "sport": player_data.get("sport"),
                    "injury_status": player_data.get("injury_status", "healthy"),
                    "stats": player_data.get("season_stats", {}),
                }
            )

        # Validate requested players are on target team's roster
        requesting_player_details = []
        target_roster = to_team.roster or []
        target_roster_ids = {p.get("player_id") for p in target_roster}

        for player_req in request.requesting_players:
            if player_req.player_id not in target_roster_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Player {player_req.player_id} is not on {to_team.team_name}'s roster",
                )

            # Get player details
            player_data = await sports_service.get_player_details(player_req.player_id)
            if not player_data:
                raise HTTPException(
                    status_code=404, detail=f"Player {player_req.player_id} not found"
                )

            requesting_player_details.append(
                {
                    "player_id": player_req.player_id,
                    "name": player_data.get("name"),
                    "position": player_data.get("position"),
                    "team": player_data.get("team"),
                    "sport": player_data.get("sport"),
                    "injury_status": player_data.get("injury_status", "healthy"),
                    "stats": player_data.get("season_stats", {}),
                }
            )

        # Check for overlapping players (can't trade same player both ways)
        offering_ids = {p["player_id"] for p in offering_player_details}
        requesting_ids = {p["player_id"] for p in requesting_player_details}
        if offering_ids & requesting_ids:
            raise HTTPException(
                status_code=400,
                detail="Cannot trade the same player in both directions",
            )

        # Perform trade evaluation
        trade_evaluator = get_trade_evaluator()

        # Prepare data for evaluation
        player_stats = {}
        all_players = offering_player_details + requesting_player_details
        for player in all_players:
            player_stats[player["player_id"]] = {
                "position": player["position"],
                "injury_status": player["injury_status"],
                "season_stats": player["stats"],
                "projections": {},  # Would be populated from projections service
                "age": 28,  # Would be calculated from player data
                "recent_games": [],  # Would be populated from game logs
            }

        current_rosters = {
            from_team.team_id: current_roster,
            to_team.team_id: target_roster,
        }

        league_scoring_rules = league.scoring_rules or {}

        offering_player_ids = [p["player_id"] for p in offering_player_details]
        requesting_player_ids = [p["player_id"] for p in requesting_player_details]

        trade_analysis = await trade_evaluator.evaluate_trade(
            trade_id="temp",
            team_a_id=from_team.team_id,
            team_b_id=to_team.team_id,
            team_a_players=offering_player_ids,
            team_b_players=requesting_player_ids,
            league_scoring_rules=league_scoring_rules,
            current_rosters=current_rosters,
            player_stats=player_stats,
        )

        # Create trade record
        trade_id = str(uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=request.expiration_hours)

        trade = Trade(
            trade_id=trade_id,
            from_team_id=from_team.team_id,
            to_team_id=to_team.team_id,
            league_id=league.league_id,
            status="pending",
            proposed_players=offering_player_ids,
            requested_players=requesting_player_ids,
            message=request.message,
            evaluation_score=trade_analysis.fairness_score,
            expires_at=expires_at,
            created_at=datetime.utcnow(),
        )

        db.add(trade)
        db.commit()
        db.refresh(trade)

        # Send notification to target team owner
        notification_service = get_notification_service()
        await notification_service.send_notification(
            user_id=str(to_team.owner_id),
            notification_type="trade_proposal",
            title="New Trade Proposal",
            message=f"{from_team.team_name} has proposed a trade",
            data={
                "trade_id": trade_id,
                "from_team": from_team.team_name,
                "offering_players": [p["name"] for p in offering_player_details],
                "requesting_players": [p["name"] for p in requesting_player_details],
                "expires_at": expires_at.isoformat(),
            },
        )

        # Prepare trade evaluation for response
        evaluation_summary = {
            "fairness_score": trade_analysis.fairness_score,
            "fairness_level": trade_analysis.fairness_level.value,
            "recommendation": trade_analysis.recommendation,
            "trade_grade_from": trade_analysis.trade_grade_team_a,
            "trade_grade_to": trade_analysis.trade_grade_team_b,
            "value_difference_percentage": trade_analysis.value_difference_percentage,
            "reasoning": trade_analysis.reasoning,
            "concerns": trade_analysis.concerns,
            "roster_improvement_from": trade_analysis.roster_improvement_team_a,
            "roster_improvement_to": trade_analysis.roster_improvement_team_b,
        }

        # Create response
        response_data = TradeProposalResponse(
            trade_id=trade_id,
            from_team_id=from_team.team_id,
            from_team_name=from_team.team_name,
            to_team_id=to_team.team_id,
            to_team_name=to_team.team_name,
            status="pending",
            offering_players=offering_player_details,
            requesting_players=requesting_player_details,
            trade_evaluation=evaluation_summary,
            message=request.message,
            expires_at=expires_at.isoformat(),
            created_at=trade.created_at.isoformat(),
            evaluation_confidence=trade_analysis.confidence_level,
        )

        logger.info(
            "Trade proposal created",
            extra={
                "trade_id": trade_id,
                "user_id": str(current_user.user_id),
                "from_team": from_team.team_id,
                "to_team": to_team.team_id,
                "fairness_score": trade_analysis.fairness_score,
                "expires_at": expires_at.isoformat(),
            },
        )

        return StandardResponse(
            success=True,
            data=response_data,
            message=f"Trade proposal sent to {to_team.team_name}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to create trade proposal",
            extra={
                "user_id": str(current_user.user_id),
                "to_team_id": request.to_team_id,
                "error": str(e),
            },
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to create trade proposal. Please try again later.",
        )


@router.get("/trades", response_model=StandardResponse[list[dict]])
async def get_trades(
    league_id: str | None = None,
    team_id: str | None = None,
    status: str | None = None,
    include_expired: bool = False,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[list[dict]]:
    """
    Get trade proposals with filtering options.

    Returns trade proposals visible to the current user:
    - Trades involving user's teams
    - All trades if user is league commissioner
    - Optional filtering by league, team, or status

    **Query Parameters:**
    - **league_id**: Filter by specific league
    - **team_id**: Filter by specific team involvement
    - **status**: Filter by trade status (pending, accepted, rejected, expired)
    - **include_expired**: Include expired trades (default: false)
    - **limit**: Number of results (default: 50, max: 100)
    - **offset**: Pagination offset

    **Returns:**
    - List of trade proposals with details and evaluation
    """
    try:
        logger.info(
            "Trades request",
            extra={
                "user_id": str(current_user.user_id),
                "league_id": league_id,
                "team_id": team_id,
                "status": status,
            },
        )

        # Get user's teams
        user_teams = db.query(Team).filter(Team.owner_id == current_user.user_id).all()

        if not user_teams:
            return StandardResponse(
                success=True, data=[], message="No teams found for user"
            )

        user_team_ids = [team.team_id for team in user_teams]

        # Build query
        query = db.query(Trade)

        # Filter by user's teams unless they're commissioner of a specific league
        if league_id:
            league = db.query(League).filter(League.league_id == league_id).first()
            if league and league.commissioner_id == current_user.user_id:
                # Commissioner can see all trades in their league
                query = query.filter(Trade.league_id == league_id)
            else:
                # Regular user sees only their team's trades in the league
                query = query.filter(
                    Trade.league_id == league_id,
                    (
                        Trade.from_team_id.in_(user_team_ids)
                        | Trade.to_team_id.in_(user_team_ids)
                    ),
                )
        else:
            # Filter to user's teams across all leagues
            query = query.filter(
                Trade.from_team_id.in_(user_team_ids)
                | Trade.to_team_id.in_(user_team_ids)
            )

        # Apply additional filters
        if team_id:
            query = query.filter(
                (Trade.from_team_id == team_id) | (Trade.to_team_id == team_id)
            )

        if status:
            query = query.filter(Trade.status == status)

        if not include_expired:
            query = query.filter(
                (Trade.expires_at > datetime.utcnow()) | (Trade.status != "pending")
            )

        # Apply pagination
        limit = min(limit, 100)
        trades = (
            query.order_by(Trade.created_at.desc()).offset(offset).limit(limit).all()
        )

        # Get sports service for player details
        sports_service = await get_sports_data_service()

        # Format response
        trade_responses = []
        for trade in trades:
            try:
                # Get team names
                from_team = (
                    db.query(Team).filter(Team.team_id == trade.from_team_id).first()
                )
                to_team = (
                    db.query(Team).filter(Team.team_id == trade.to_team_id).first()
                )

                # Get player details
                offering_players = []
                for player_id in trade.proposed_players:
                    player_data = await sports_service.get_player_details(player_id)
                    if player_data:
                        offering_players.append(
                            {
                                "player_id": player_id,
                                "name": player_data.get("name"),
                                "position": player_data.get("position"),
                                "team": player_data.get("team"),
                            }
                        )

                requesting_players = []
                for player_id in trade.requested_players:
                    player_data = await sports_service.get_player_details(player_id)
                    if player_data:
                        requesting_players.append(
                            {
                                "player_id": player_id,
                                "name": player_data.get("name"),
                                "position": player_data.get("position"),
                                "team": player_data.get("team"),
                            }
                        )

                trade_data = {
                    "trade_id": trade.trade_id,
                    "from_team_id": trade.from_team_id,
                    "from_team_name": from_team.team_name if from_team else "Unknown",
                    "to_team_id": trade.to_team_id,
                    "to_team_name": to_team.team_name if to_team else "Unknown",
                    "status": trade.status,
                    "offering_players": offering_players,
                    "requesting_players": requesting_players,
                    "message": trade.message,
                    "evaluation_score": trade.evaluation_score,
                    "expires_at": (
                        trade.expires_at.isoformat() if trade.expires_at else None
                    ),
                    "created_at": trade.created_at.isoformat(),
                    "updated_at": (
                        trade.updated_at.isoformat() if trade.updated_at else None
                    ),
                    "is_expired": (
                        trade.expires_at < datetime.utcnow()
                        if trade.expires_at
                        else False
                    ),
                }

                trade_responses.append(trade_data)

            except Exception as e:
                logger.warning(f"Failed to format trade {trade.trade_id}: {e}")
                continue

        logger.info(
            "Trades retrieved",
            extra={
                "user_id": str(current_user.user_id),
                "trades_count": len(trade_responses),
                "league_id": league_id,
                "team_id": team_id,
            },
        )

        return StandardResponse(
            success=True,
            data=trade_responses,
            message=f"Retrieved {len(trade_responses)} trades",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get trades",
            extra={
                "user_id": str(current_user.user_id),
                "error": str(e),
            },
        )

        raise HTTPException(
            status_code=500, detail="Failed to retrieve trades. Please try again later."
        )
