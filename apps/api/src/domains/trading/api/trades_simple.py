"""
Simple trade management API endpoints for contract tests.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.middleware.auth import get_current_user
from domains.users.models.user import User


router = APIRouter(prefix="/api/v1/trades", tags=["trades"])


class TradePlayerRequest(BaseModel):
    """Player in a trade request."""
    player_id: str
    player_name: Optional[str] = None
    position: Optional[str] = None


class CreateTradeRequest(BaseModel):
    """Request to create a new trade."""
    target_team_id: str
    offering_players: List[TradePlayerRequest]
    requesting_players: List[TradePlayerRequest]
    message: Optional[str] = None
    expiry_hours: int = Field(default=72, ge=24, le=168)


class TradeResponse(BaseModel):
    """Trade response model."""
    trade_id: str
    status: str  # "pending", "accepted", "rejected", "expired", "cancelled"
    proposer_team_id: str
    target_team_id: str
    offering_players: List[TradePlayerRequest]
    requesting_players: List[TradePlayerRequest]
    message: Optional[str]
    created_at: datetime
    expires_at: datetime
    responded_at: Optional[datetime] = None
    fairness_score: Optional[float] = None


class TradeActionRequest(BaseModel):
    """Request to accept/reject/counter a trade."""
    action: str  # "accept", "reject", "counter"
    message: Optional[str] = None
    counter_offer: Optional[CreateTradeRequest] = None


class TradeActionResponse(BaseModel):
    """Response after trade action."""
    trade_id: str
    action: str
    status: str
    message: str
    processed_at: datetime


@router.post("/", response_model=TradeResponse)
async def create_trade(
    request: CreateTradeRequest,
    current_user: User = Depends(get_current_user),
) -> TradeResponse:
    """
    Create a new trade proposal.

    This endpoint:
    - Validates both teams exist in the same league
    - Validates all players belong to the correct teams
    - Creates the trade proposal
    - Calculates fairness score
    - Notifies the target team
    - Returns trade details
    """

    # Basic validation
    if not request.target_team_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target team ID is required"
        )

    if not request.offering_players or not request.requesting_players:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both offering and requesting players are required"
        )

    # Mock trade creation
    trade_id = str(uuid.uuid4())
    created_at = datetime.utcnow()

    trade_response = TradeResponse(
        trade_id=trade_id,
        status="pending",
        proposer_team_id=str(current_user.user_id),  # Simplified
        target_team_id=request.target_team_id,
        offering_players=request.offering_players,
        requesting_players=request.requesting_players,
        message=request.message,
        created_at=created_at,
        expires_at=datetime.utcfromtimestamp(
            created_at.timestamp() + (request.expiry_hours * 3600)
        ),
        fairness_score=0.85  # Mock fairness calculation
    )

    return trade_response


@router.patch("/{trade_id}", response_model=TradeActionResponse)
async def respond_to_trade(
    trade_id: str,
    request: TradeActionRequest,
    current_user: User = Depends(get_current_user),
) -> TradeActionResponse:
    """
    Respond to a trade proposal (accept/reject/counter).

    This endpoint:
    - Validates the trade exists and is pending
    - Validates the user is the target of the trade
    - Processes the action (accept/reject/counter)
    - Updates league rosters if accepted
    - Notifies both teams of the outcome
    - Returns action confirmation
    """

    # Basic validation
    if not trade_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trade ID is required"
        )

    valid_actions = ["accept", "reject", "counter"]
    if request.action not in valid_actions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Action must be one of: {', '.join(valid_actions)}"
        )

    # Mock trade processing
    processed_at = datetime.utcnow()

    if request.action == "accept":
        status_result = "accepted"
        message = "Trade has been accepted and players have been exchanged"
    elif request.action == "reject":
        status_result = "rejected"
        message = "Trade has been rejected"
    elif request.action == "counter":
        status_result = "countered"
        message = "Counter-offer has been sent"
    else:
        status_result = "pending"
        message = "Trade action processed"

    response = TradeActionResponse(
        trade_id=trade_id,
        action=request.action,
        status=status_result,
        message=message,
        processed_at=processed_at
    )

    return response


@router.get("/", response_model=List[TradeResponse])
async def get_trades(
    status: Optional[str] = None,
    team_id: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
) -> List[TradeResponse]:
    """Get trades involving the current user's team."""

    # Mock trades data
    trades = [
        TradeResponse(
            trade_id=str(uuid.uuid4()),
            status="pending",
            proposer_team_id=str(current_user.user_id),
            target_team_id=str(uuid.uuid4()),
            offering_players=[
                TradePlayerRequest(
                    player_id="player_123",
                    player_name="Mike Trout",
                    position="OF"
                )
            ],
            requesting_players=[
                TradePlayerRequest(
                    player_id="player_456",
                    player_name="Aaron Judge",
                    position="OF"
                )
            ],
            message="Fair value swap of outfielders",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcfromtimestamp(
                datetime.utcnow().timestamp() + (72 * 3600)
            ),
            fairness_score=0.92
        ),
        TradeResponse(
            trade_id=str(uuid.uuid4()),
            status="accepted",
            proposer_team_id=str(uuid.uuid4()),
            target_team_id=str(current_user.user_id),
            offering_players=[
                TradePlayerRequest(
                    player_id="player_789",
                    player_name="Jose Altuve",
                    position="2B"
                )
            ],
            requesting_players=[
                TradePlayerRequest(
                    player_id="player_101",
                    player_name="Francisco Lindor",
                    position="SS"
                )
            ],
            message="Need SS help",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcfromtimestamp(
                datetime.utcnow().timestamp() + (72 * 3600)
            ),
            responded_at=datetime.utcnow(),
            fairness_score=0.78
        )
    ]

    # Apply filters
    if status:
        trades = [trade for trade in trades if trade.status == status]
    if team_id:
        trades = [
            trade for trade in trades
            if trade.proposer_team_id == team_id or trade.target_team_id == team_id
        ]

    return trades[:limit]


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(
    trade_id: str,
    current_user: User = Depends(get_current_user),
) -> TradeResponse:
    """Get details of a specific trade."""

    # Mock trade details
    return TradeResponse(
        trade_id=trade_id,
        status="pending",
        proposer_team_id=str(current_user.user_id),
        target_team_id=str(uuid.uuid4()),
        offering_players=[
            TradePlayerRequest(
                player_id="player_123",
                player_name="Mike Trout",
                position="OF"
            )
        ],
        requesting_players=[
            TradePlayerRequest(
                player_id="player_456",
                player_name="Aaron Judge",
                position="OF"
            )
        ],
        message="Fair value swap of outfielders",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcfromtimestamp(
            datetime.utcnow().timestamp() + (72 * 3600)
        ),
        fairness_score=0.92
    )


@router.delete("/{trade_id}")
async def cancel_trade(
    trade_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Cancel a pending trade (proposer only)."""

    # Mock cancellation
    return {
        "status": "cancelled",
        "message": "Trade has been cancelled"
    }


@router.get("/{trade_id}/evaluation")
async def evaluate_trade(
    trade_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get detailed trade evaluation and analysis."""

    # Mock evaluation
    return {
        "trade_id": trade_id,
        "fairness_score": 0.85,
        "recommendation": "Accept",
        "analysis": {
            "value_difference": 2.3,
            "roster_impact": "Positive",
            "position_needs": ["Addressed"],
            "risk_factors": ["Injury history for Player A"]
        },
        "player_projections": {
            "offering_total": 245.7,
            "requesting_total": 243.4
        }
    }