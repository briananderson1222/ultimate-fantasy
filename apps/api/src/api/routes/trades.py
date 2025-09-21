"""Trade API endpoints backed by the consolidated TradingService."""

from __future__ import annotations

import uuid as _uuid
from datetime import datetime
from typing import List, Optional

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, validator

from api.deps import (
    get_current_user_id,
    get_trading_service,
)
from domains.leagues.models.team import Team
from domains.shared.exceptions import (
    InsufficientPermissionsError,
    InvalidTradeError,
    LeagueNotFoundError,
    PlayerNotFoundError,
    TradeAlreadyProcessedError,
    TradeExpiredError,
    TradeNotFoundError,
)
from domains.trading.services.trading_service import TradeEvaluation, TradingService

router = APIRouter(prefix="/api/v1/trades", tags=["trades"])


class TradePlayerPayload(BaseModel):
    player_id: _uuid.UUID


class ProposeTradeRequest(BaseModel):
    league_id: _uuid.UUID
    from_team_id: _uuid.UUID
    to_team_id: _uuid.UUID
    offered_players: List[TradePlayerPayload]
    requested_players: List[TradePlayerPayload]
    message: Optional[str] = Field(None, max_length=500)
    expiration_hours: Optional[int] = Field(
        None, description="Custom expiration window in hours"
    )

    @validator("offered_players", "requested_players")
    def ensure_not_empty(cls, value: List[TradePlayerPayload]) -> List[TradePlayerPayload]:
        if not value:
            raise ValueError("At least one player must be included")
        return value


class RespondToTradeRequest(BaseModel):
    action: str = Field(..., description="accept or reject")
    rejection_reason: Optional[str] = Field(None, max_length=500)

    @validator("action")
    def validate_action(cls, value: str) -> str:
        action = value.lower()
        if action not in {"accept", "reject"}:
            raise ValueError("Action must be 'accept' or 'reject'")
        return action


class TradeResponse(BaseModel):
    trade_id: _uuid.UUID
    league_id: _uuid.UUID
    offering_team_id: _uuid.UUID
    receiving_team_id: _uuid.UUID
    status: str
    offered_players: List[str]
    requested_players: List[str]
    message: Optional[str]
    rejection_reason: Optional[str]
    expires_at: Optional[datetime]
    processed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class TradeListResponse(BaseModel):
    items: List[TradeResponse]


class TradeEvaluationResponse(BaseModel):
    fairness_score: float
    offering_team_value: float
    receiving_team_value: float
    value_difference: float
    position_analysis: dict
    injury_risk_analysis: dict
    recommendation: str


def _serialize_trade(trade) -> TradeResponse:
    return TradeResponse(
        trade_id=_uuid.UUID(str(trade.trade_id)),
        league_id=_uuid.UUID(str(trade.league_id)),
        offering_team_id=_uuid.UUID(str(trade.offering_team_id)),
        receiving_team_id=_uuid.UUID(str(trade.receiving_team_id)),
        status=trade.status,
        offered_players=[str(pid) for pid in trade.offered_players or []],
        requested_players=[str(pid) for pid in trade.requested_players or []],
        message=getattr(trade, "trade_message", None),
        rejection_reason=getattr(trade, "rejection_reason", None),
        expires_at=trade.expires_at,
        processed_at=getattr(trade, "processed_at", None),
        created_at=trade.created_at,
        updated_at=trade.updated_at,
    )


def _serialize_evaluation(evaluation: TradeEvaluation) -> TradeEvaluationResponse:
    return TradeEvaluationResponse(
        fairness_score=evaluation.fairness_score,
        offering_team_value=evaluation.offering_team_value,
        receiving_team_value=evaluation.receiving_team_value,
        value_difference=evaluation.value_difference,
        position_analysis=evaluation.position_analysis,
        injury_risk_analysis=evaluation.injury_risk_analysis,
        recommendation=evaluation.recommendation,
    )


def _handle_trade_exception(exc: Exception) -> None:
    if isinstance(exc, TradeNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, (InvalidTradeError, PlayerNotFoundError)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, InsufficientPermissionsError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, TradeAlreadyProcessedError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, TradeExpiredError):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(exc))
    if isinstance(exc, LeagueNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Trading service error",
    )


@router.post("", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
def propose_trade(
    payload: ProposeTradeRequest,
    trading_service: TradingService = Depends(get_trading_service),
    current_user_id: _uuid.UUID = Depends(get_current_user_id),
) -> TradeResponse:
    offered = [str(player.player_id) for player in payload.offered_players]
    requested = [str(player.player_id) for player in payload.requested_players]

    try:
        trade = trading_service.propose_trade(
            league_id=str(payload.league_id),
            from_team_id=str(payload.from_team_id),
            to_team_id=str(payload.to_team_id),
            offered_players=offered,
            requested_players=requested,
            proposing_user_id=str(current_user_id),
            message=payload.message,
            expiration_hours=payload.expiration_hours,
        )
        return _serialize_trade(trade)
    except Exception as exc:  # noqa: BLE001
        _handle_trade_exception(exc)


@router.post("/{trade_id}/respond", response_model=TradeResponse)
def respond_to_trade(
    trade_id: _uuid.UUID,
    payload: RespondToTradeRequest,
    trading_service: TradingService = Depends(get_trading_service),
    current_user_id: _uuid.UUID = Depends(get_current_user_id),
) -> TradeResponse:
    try:
        trade = trading_service.respond_to_trade(
            trade_id=str(trade_id),
            responding_user_id=str(current_user_id),
            action=payload.action,
            rejection_reason=payload.rejection_reason,
        )
        return _serialize_trade(trade)
    except Exception as exc:  # noqa: BLE001
        _handle_trade_exception(exc)


@router.post("/{trade_id}/cancel", response_model=TradeResponse)
def cancel_trade(
    trade_id: _uuid.UUID,
    trading_service: TradingService = Depends(get_trading_service),
    current_user_id: _uuid.UUID = Depends(get_current_user_id),
) -> TradeResponse:
    try:
        trade = trading_service.cancel_trade(
            trade_id=str(trade_id), requesting_user_id=str(current_user_id)
        )
        return _serialize_trade(trade)
    except Exception as exc:  # noqa: BLE001
        _handle_trade_exception(exc)


@router.get("/{trade_id}", response_model=TradeResponse)
def get_trade(
    trade_id: _uuid.UUID,
    trading_service: TradingService = Depends(get_trading_service),
    current_user_id: _uuid.UUID = Depends(get_current_user_id),
) -> TradeResponse:
    try:
        trade = trading_service.get_trade(str(trade_id))
    except Exception as exc:  # noqa: BLE001
        _handle_trade_exception(exc)
        raise  # pragma: no cover - never reached

    try:
        ownership_count = trading_service.session.query(Team).filter(
            Team.team_id.in_([trade.offering_team_id, trade.receiving_team_id]),
            Team.user_id == uuid.UUID(str(current_user_id)),
        ).count()
    except Exception:  # pragma: no cover - defensive
        ownership_count = 0

    if ownership_count == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this trade",
        )

    return _serialize_trade(trade)


@router.get("", response_model=TradeListResponse)
def list_trades(
    league_id: _uuid.UUID = Query(...),
    team_id: Optional[_uuid.UUID] = Query(None),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    trading_service: TradingService = Depends(get_trading_service),
    current_user_id: _uuid.UUID = Depends(get_current_user_id),
) -> TradeListResponse:
    try:
        # Ensure user participates in league before listing
        is_eligible = trading_service.session.query(Team).filter(
            Team.league_id == uuid.UUID(str(league_id)),
            Team.user_id == uuid.UUID(str(current_user_id)),
        ).count() > 0
    except Exception:  # pragma: no cover - defensive fallback
        is_eligible = False

    if not is_eligible:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    try:
        trades = trading_service.list_league_trades(
            league_id=str(league_id),
            team_id=str(team_id) if team_id else None,
            status=status_filter,
            limit=limit,
            offset=offset,
        )
        return TradeListResponse(items=[_serialize_trade(trade) for trade in trades])
    except Exception as exc:  # noqa: BLE001
        _handle_trade_exception(exc)


@router.get("/{trade_id}/evaluation", response_model=TradeEvaluationResponse)
def evaluate_trade(
    trade_id: _uuid.UUID,
    trading_service: TradingService = Depends(get_trading_service),
    current_user_id: _uuid.UUID = Depends(get_current_user_id),
) -> TradeEvaluationResponse:
    try:
        evaluation = trading_service.evaluate_trade(str(trade_id))
        return _serialize_evaluation(evaluation)
    except Exception as exc:  # noqa: BLE001
        _handle_trade_exception(exc)
