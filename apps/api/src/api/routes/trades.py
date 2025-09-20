"""
Trade API endpoints for Ultimate Fantasy Platform
Provides REST API for trade proposals, evaluations, voting, and management
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ...infrastructure.database.session_factory import get_db_session
from ...domains.trading.services.trading_service import TradingService
from ...domains.leagues.services.league_service import LeagueService
from ...domains.shared.exceptions import (
    TradeNotFoundError, LeagueNotFoundError, UserNotFoundError,
    InvalidTradeError, TradeExpiredError, TradeAlreadyProcessedError,
    InsufficientPermissionsError, PlayerNotFoundError, InvalidRosterError
)
from ..middleware.auth import get_current_user
from ..models.response import APIResponse, ErrorResponse
from ...models.trade import Trade, TradeStatus, VoteType


router = APIRouter(prefix="/api/v1/trades", tags=["trades"])

trading_service = TradingService()
league_service = LeagueService()


# Pydantic Models for Request/Response
class TradePlayerRequest(BaseModel):
    player_id: str = Field(..., description="Player ID")
    position: str = Field(..., description="Player position")


class ProposeTradeRequest(BaseModel):
    league_id: str = Field(..., description="League ID")
    to_team_id: str = Field(..., description="Receiving team ID")
    offering_players: List[TradePlayerRequest] = Field(..., description="Players being offered")
    requesting_players: List[TradePlayerRequest] = Field(..., description="Players being requested")
    message: Optional[str] = Field(None, max_length=500, description="Optional trade message")
    expiration_hours: int = Field(default=72, ge=24, le=168, description="Trade expiration in hours")

    @validator('offering_players', 'requesting_players')
    def validate_players_not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one player must be included")
        return v


class RespondToTradeRequest(BaseModel):
    action: str = Field(..., description="accept, counter, or decline")
    counter_offering_players: Optional[List[TradePlayerRequest]] = None
    counter_requesting_players: Optional[List[TradePlayerRequest]] = None
    message: Optional[str] = Field(None, max_length=500)

    @validator('action')
    def validate_action(cls, v):
        valid_actions = ['accept', 'counter', 'decline']
        if v.lower() not in valid_actions:
            raise ValueError(f"Action must be one of: {valid_actions}")
        return v.lower()


class VoteOnTradeRequest(BaseModel):
    vote: str = Field(..., description="approve or veto")
    reason: Optional[str] = Field(None, max_length=200, description="Reason for vote")

    @validator('vote')
    def validate_vote(cls, v):
        valid_votes = ['approve', 'veto']
        if v.lower() not in valid_votes:
            raise ValueError(f"Vote must be one of: {valid_votes}")
        return v.lower()


class TradePlayerResponse(BaseModel):
    player_id: str
    player_name: str
    position: str
    team: str
    projected_points: float
    current_value: float

    class Config:
        from_attributes = True


class TradeEvaluationResponse(BaseModel):
    fairness_score: float
    value_difference: float
    offering_team_value: float
    receiving_team_value: float
    position_analysis: Dict[str, Any]
    injury_risk_analysis: Dict[str, Any]
    recommendation: str
    warnings: List[str]

    class Config:
        from_attributes = True


class TradeResponse(BaseModel):
    trade_id: str
    league_id: str
    from_team_id: str
    to_team_id: str
    status: str
    offering_players: List[TradePlayerResponse]
    requesting_players: List[TradePlayerResponse]
    message: Optional[str]
    proposed_at: datetime
    expires_at: datetime
    processed_at: Optional[datetime]
    processed_by: Optional[str]
    evaluation: Optional[TradeEvaluationResponse]
    votes_for: int
    votes_against: int
    veto_threshold: int

    class Config:
        from_attributes = True


class TradeVoteResponse(BaseModel):
    vote_id: str
    trade_id: str
    user_id: str
    username: str
    vote_type: str
    reason: Optional[str]
    voted_at: datetime

    class Config:
        from_attributes = True


class TradeHistoryResponse(BaseModel):
    trade_id: str
    action: str
    timestamp: datetime
    user_id: str
    username: str
    details: Dict[str, Any]

    class Config:
        from_attributes = True


# Trade Proposal Endpoints
@router.post("/", response_model=APIResponse[TradeResponse])
async def propose_trade(
    request: ProposeTradeRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Propose a new trade to another team"""
    try:
        # Verify user is in the league and owns the from_team
        from_team = league_service.get_user_team_in_league(
            request.league_id, current_user["user_id"], db
        )

        trade = trading_service.propose_trade(
            league_id=request.league_id,
            from_team_id=str(from_team.team_id),
            to_team_id=request.to_team_id,
            offering_players=[p.dict() for p in request.offering_players],
            requesting_players=[p.dict() for p in request.requesting_players],
            message=request.message,
            expiration_hours=request.expiration_hours,
            db=db
        )

        return APIResponse(
            success=True,
            data=TradeResponse.from_orm(trade),
            message="Trade proposed successfully"
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found in league"
        )
    except InvalidTradeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PlayerNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidRosterError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{trade_id}", response_model=APIResponse[TradeResponse])
async def get_trade(
    trade_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get trade details by ID"""
    try:
        trade = trading_service.get_trade(trade_id, db)

        # Verify user is in the league
        if not league_service.is_user_in_league(trade.league_id, current_user["user_id"], db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - not a league member"
            )

        return APIResponse(
            success=True,
            data=TradeResponse.from_orm(trade),
            message="Trade retrieved successfully"
        )

    except TradeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )


@router.post("/{trade_id}/respond", response_model=APIResponse[TradeResponse])
async def respond_to_trade(
    trade_id: str,
    request: RespondToTradeRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Accept, decline, or counter a trade proposal"""
    try:
        if request.action == "accept":
            trade = trading_service.accept_trade(trade_id, current_user["user_id"], db)
        elif request.action == "decline":
            trade = trading_service.decline_trade(trade_id, current_user["user_id"], db)
        elif request.action == "counter":
            if not request.counter_offering_players or not request.counter_requesting_players:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Counter offer must include players for both sides"
                )

            trade = trading_service.counter_trade(
                trade_id=trade_id,
                user_id=current_user["user_id"],
                counter_offering_players=[p.dict() for p in request.counter_offering_players],
                counter_requesting_players=[p.dict() for p in request.counter_requesting_players],
                message=request.message,
                db=db
            )

        return APIResponse(
            success=True,
            data=TradeResponse.from_orm(trade),
            message=f"Trade {request.action}ed successfully"
        )

    except TradeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
    except TradeExpiredError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trade has expired"
        )
    except TradeAlreadyProcessedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trade has already been processed"
        )
    except InsufficientPermissionsError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to respond to this trade"
        )
    except InvalidTradeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{trade_id}")
async def cancel_trade(
    trade_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Cancel a pending trade proposal (proposer only)"""
    try:
        trading_service.cancel_trade(trade_id, current_user["user_id"], db)

        return APIResponse(
            success=True,
            data=None,
            message="Trade cancelled successfully"
        )

    except TradeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
    except InsufficientPermissionsError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the trade proposer can cancel a trade"
        )
    except TradeAlreadyProcessedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a processed trade"
        )


# Trade Evaluation Endpoints
@router.get("/{trade_id}/evaluation", response_model=APIResponse[TradeEvaluationResponse])
async def get_trade_evaluation(
    trade_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get AI-powered trade fairness evaluation"""
    try:
        trade = trading_service.get_trade(trade_id, db)

        # Verify user is in the league
        if not league_service.is_user_in_league(trade.league_id, current_user["user_id"], db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - not a league member"
            )

        evaluation = trading_service.evaluate_trade_fairness(trade_id, db)

        return APIResponse(
            success=True,
            data=TradeEvaluationResponse.from_orm(evaluation),
            message="Trade evaluation retrieved successfully"
        )

    except TradeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )


# Trade Voting Endpoints
@router.post("/{trade_id}/vote", response_model=APIResponse[TradeVoteResponse])
async def vote_on_trade(
    trade_id: str,
    request: VoteOnTradeRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Vote to approve or veto a trade (league members only)"""
    try:
        vote_type = VoteType.APPROVE if request.vote == "approve" else VoteType.VETO

        vote = trading_service.vote_on_trade(
            trade_id=trade_id,
            user_id=current_user["user_id"],
            vote_type=vote_type,
            reason=request.reason,
            db=db
        )

        return APIResponse(
            success=True,
            data=TradeVoteResponse.from_orm(vote),
            message="Vote submitted successfully"
        )

    except TradeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
    except InsufficientPermissionsError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to vote on this trade"
        )
    except TradeAlreadyProcessedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot vote on a processed trade"
        )


@router.get("/{trade_id}/votes", response_model=APIResponse[List[TradeVoteResponse]])
async def get_trade_votes(
    trade_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get all votes for a trade"""
    try:
        trade = trading_service.get_trade(trade_id, db)

        # Verify user is in the league
        if not league_service.is_user_in_league(trade.league_id, current_user["user_id"], db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - not a league member"
            )

        votes = trading_service.get_trade_votes(trade_id, db)

        return APIResponse(
            success=True,
            data=[TradeVoteResponse.from_orm(vote) for vote in votes],
            message="Trade votes retrieved successfully"
        )

    except TradeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )


# Trade History and Management
@router.get("/league/{league_id}", response_model=APIResponse[List[TradeResponse]])
async def get_league_trades(
    league_id: str,
    current_user: dict = Depends(get_current_user),
    status_filter: Optional[str] = Query(None, description="Filter by trade status"),
    team_id: Optional[str] = Query(None, description="Filter by team involvement"),
    limit: int = Query(default=50, le=100, description="Maximum number of results"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db_session)
):
    """Get all trades for a league"""
    try:
        # Verify user is in the league
        if not league_service.is_user_in_league(league_id, current_user["user_id"], db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - not a league member"
            )

        trades = trading_service.get_league_trades(
            league_id=league_id,
            status_filter=status_filter,
            team_id=team_id,
            limit=limit,
            offset=offset,
            db=db
        )

        return APIResponse(
            success=True,
            data=[TradeResponse.from_orm(trade) for trade in trades],
            message="League trades retrieved successfully"
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )


@router.get("/user/trades", response_model=APIResponse[List[TradeResponse]])
async def get_user_trades(
    current_user: dict = Depends(get_current_user),
    league_id: Optional[str] = Query(None, description="Filter by league"),
    status_filter: Optional[str] = Query(None, description="Filter by trade status"),
    limit: int = Query(default=50, le=100, description="Maximum number of results"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db_session)
):
    """Get all trades involving the current user"""
    try:
        trades = trading_service.get_user_trades(
            user_id=current_user["user_id"],
            league_id=league_id,
            status_filter=status_filter,
            limit=limit,
            offset=offset,
            db=db
        )

        return APIResponse(
            success=True,
            data=[TradeResponse.from_orm(trade) for trade in trades],
            message="User trades retrieved successfully"
        )

    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )


@router.get("/{trade_id}/history", response_model=APIResponse[List[TradeHistoryResponse]])
async def get_trade_history(
    trade_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get complete history of a trade including all actions and changes"""
    try:
        trade = trading_service.get_trade(trade_id, db)

        # Verify user is in the league
        if not league_service.is_user_in_league(trade.league_id, current_user["user_id"], db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - not a league member"
            )

        history = trading_service.get_trade_history(trade_id, db)

        return APIResponse(
            success=True,
            data=[TradeHistoryResponse.from_orm(entry) for entry in history],
            message="Trade history retrieved successfully"
        )

    except TradeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )


# Commissioner Trade Management
@router.post("/{trade_id}/force-process")
async def force_process_trade(
    trade_id: str,
    action: str = Query(..., description="approve or veto"),
    reason: Optional[str] = Query(None, description="Reason for action"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Force process a trade (commissioner only)"""
    try:
        trade = trading_service.get_trade(trade_id, db)

        # Verify user is commissioner
        if not league_service.is_commissioner(trade.league_id, current_user["user_id"], db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only commissioners can force process trades"
            )

        if action.lower() == "approve":
            result = trading_service.force_approve_trade(trade_id, current_user["user_id"], reason, db)
        elif action.lower() == "veto":
            result = trading_service.force_veto_trade(trade_id, current_user["user_id"], reason, db)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action must be 'approve' or 'veto'"
            )

        return APIResponse(
            success=True,
            data=TradeResponse.from_orm(result),
            message=f"Trade {action}d by commissioner"
        )

    except TradeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
    except InsufficientPermissionsError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only commissioners can force process trades"
        )


@router.get("/league/{league_id}/analytics", response_model=APIResponse[Dict[str, Any]])
async def get_trade_analytics(
    league_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get trade analytics for the league (commissioner only)"""
    try:
        # Verify user is commissioner
        if not league_service.is_commissioner(league_id, current_user["user_id"], db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only commissioners can view trade analytics"
            )

        analytics = trading_service.get_league_trade_analytics(league_id, db)

        return APIResponse(
            success=True,
            data=analytics,
            message="Trade analytics retrieved successfully"
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )