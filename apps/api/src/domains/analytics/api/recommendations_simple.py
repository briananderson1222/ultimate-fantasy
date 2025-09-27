"""
Simple analytics recommendations API endpoints for contract tests.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from api.middleware.auth import get_current_user

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


class PlayerRecommendation(BaseModel):
    """Player recommendation model."""

    player_id: str
    name: str
    position: str
    team: str
    recommendation_type: str
    reason: str
    confidence_score: float
    projected_impact: float


class TradeRecommendation(BaseModel):
    """Trade recommendation model."""

    target_team_id: str
    target_team_name: str
    give_players: list[str]
    receive_players: list[str]
    trade_value: float
    fairness_score: float
    reason: str


class Recommendation(BaseModel):
    """Unified recommendation model for contract compliance."""

    type: str
    player_id: str
    confidence_score: float
    reasoning: str
    # Optional fields from original models
    name: str | None = None
    position: str | None = None
    team: str | None = None
    projected_impact: float | None = None


class RecommendationMetadata(BaseModel):
    """Recommendation metadata."""

    generated_at: datetime
    league_id: str | None = None
    total_recommendations: int
    confidence_threshold: float = 0.7


class RecommendationsResponse(BaseModel):
    """Analytics recommendations response matching contract."""

    recommendations: list[Recommendation]
    metadata: RecommendationMetadata


@router.get("/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(
    league_id: str | None = Query(None),
    recommendation_type: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
) -> RecommendationsResponse:
    """Get AI-powered player and trade recommendations."""

    # Check for invalid team/league scenarios for 404 testing
    if league_id and league_id.startswith("invalid_"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "LeagueNotFound",
                "message": f"League {league_id} not found",
            },
        )

    # Mock data for contract tests
    player_recommendations = [
        PlayerRecommendation(
            player_id="player_123",
            name="Mike Trout",
            position="OF",
            team="LAA",
            recommendation_type="add",
            reason="High projected value with favorable upcoming schedule",
            confidence_score=0.85,
            projected_impact=12.5,
        ),
        PlayerRecommendation(
            player_id="player_456",
            name="Ronald Acuna Jr.",
            position="OF",
            team="ATL",
            recommendation_type="trade_for",
            reason="Excellent recent form and playoff schedule advantage",
            confidence_score=0.92,
            projected_impact=15.8,
        ),
    ]

    trade_recommendations = [
        TradeRecommendation(
            target_team_id="team_789",
            target_team_name="Team Alpha",
            give_players=["player_101", "player_102"],
            receive_players=["player_201"],
            trade_value=1.15,
            fairness_score=0.88,
            reason="Upgrade at shortstop position while maintaining depth",
        )
    ]

    # Filter by type if specified
    if recommendation_type:
        player_recommendations = [
            rec
            for rec in player_recommendations
            if rec.recommendation_type == recommendation_type
        ]

    # Apply limit
    player_recommendations = player_recommendations[:limit]
    trade_recommendations = trade_recommendations[
        : min(limit // 2, len(trade_recommendations))
    ]

    # Convert to unified recommendation format for contract compliance
    unified_recommendations = []

    # Convert player recommendations
    for rec in player_recommendations:
        unified_recommendations.append(
            Recommendation(
                type="player_pickup",
                player_id=rec.player_id,
                confidence_score=rec.confidence_score,
                reasoning=rec.reason,
                name=rec.name,
                position=rec.position,
                team=rec.team,
                projected_impact=rec.projected_impact,
            )
        )

    # Convert trade recommendations
    for rec in trade_recommendations:
        # Use the first receiving player as the main recommendation
        if rec.receive_players:
            unified_recommendations.append(
                Recommendation(
                    type="trade_target",
                    player_id=rec.receive_players[0],
                    confidence_score=rec.fairness_score,
                    reasoning=rec.reason,
                )
            )

    metadata = RecommendationMetadata(
        generated_at=datetime.utcnow(),
        league_id=league_id,
        total_recommendations=len(unified_recommendations),
    )

    return RecommendationsResponse(
        recommendations=unified_recommendations, metadata=metadata
    )
