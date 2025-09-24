"""
Simple analytics insights API endpoints for contract tests.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from api.middleware.auth import get_current_user


router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


class TeamPerformanceInsight(BaseModel):
    """Team performance insight model."""
    metric_name: str
    current_value: float
    league_average: float
    percentile: float
    trend: str
    description: str


class PlayerInsight(BaseModel):
    """Player insight model."""
    player_id: str
    name: str
    position: str
    team: str
    insight_type: str
    message: str
    impact_score: float
    confidence: float


class LeagueInsight(BaseModel):
    """League-wide insight model."""
    insight_type: str
    title: str
    description: str
    affected_teams: List[str]
    severity: str


class InsightsResponse(BaseModel):
    """Analytics insights response."""
    team_performance: List[TeamPerformanceInsight]
    player_insights: List[PlayerInsight]
    league_insights: List[LeagueInsight]
    generated_at: datetime
    league_id: Optional[str] = None
    week: Optional[int] = None


@router.get("/insights", response_model=InsightsResponse)
async def get_insights(
    league_id: Optional[str] = Query(None),
    week: Optional[int] = Query(None),
    insight_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
) -> InsightsResponse:
    """Get comprehensive performance insights and analytics."""

    # Mock data for contract tests
    team_performance = [
        TeamPerformanceInsight(
            metric_name="Average Points Per Game",
            current_value=125.7,
            league_average=118.3,
            percentile=72.0,
            trend="improving",
            description="Your team is scoring above league average and trending upward"
        ),
        TeamPerformanceInsight(
            metric_name="Roster Consistency",
            current_value=0.82,
            league_average=0.75,
            percentile=85.0,
            trend="stable",
            description="Your players deliver consistent performances with low variance"
        )
    ]

    player_insights = [
        PlayerInsight(
            player_id="player_123",
            name="Mike Trout",
            position="OF",
            team="LAA",
            insight_type="breakout",
            message="Showing signs of return to elite form with 15% increase in hard contact rate",
            impact_score=8.5,
            confidence=0.78
        ),
        PlayerInsight(
            player_id="player_456",
            name="Tyler Glasnow",
            position="P",
            team="LAD",
            insight_type="concern",
            message="Velocity down 2.1 MPH over last 3 starts, monitor for injury risk",
            impact_score=-6.2,
            confidence=0.85
        )
    ]

    league_insights = [
        LeagueInsight(
            insight_type="scoring_trend",
            title="League-wide Scoring Increase",
            description="Average team scoring up 8% compared to same point last season",
            affected_teams=["all"],
            severity="medium"
        ),
        LeagueInsight(
            insight_type="position_scarcity",
            title="Catcher Position Extremely Thin",
            description="Only 3 catchers averaging over 10 fantasy points per game",
            affected_teams=["team_1", "team_4", "team_7"],
            severity="high"
        )
    ]

    # Filter by insight type if specified
    if insight_type:
        player_insights = [
            insight for insight in player_insights
            if insight.insight_type == insight_type
        ]
        league_insights = [
            insight for insight in league_insights
            if insight.insight_type == insight_type
        ]

    return InsightsResponse(
        team_performance=team_performance,
        player_insights=player_insights[:limit//2],
        league_insights=league_insights,
        generated_at=datetime.utcnow(),
        league_id=league_id,
        week=week
    )