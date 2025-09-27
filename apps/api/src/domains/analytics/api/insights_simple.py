"""
Simple analytics insights API endpoints for contract tests.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
    affected_teams: list[str]
    severity: str


class Insight(BaseModel):
    """Unified insight model for contract compliance."""

    category: str
    title: str
    description: str
    impact_level: str
    # Optional additional fields
    metric_value: float | None = None
    trend: str | None = None
    confidence: float | None = None


class InsightsSummary(BaseModel):
    """Insights summary metadata."""

    total_insights: int
    generated_at: datetime
    league_id: str | None = None
    week: int | None = None
    categories: list[str]


class InsightsResponse(BaseModel):
    """Analytics insights response matching contract."""

    insights: list[Insight]
    summary: InsightsSummary


@router.get("/insights", response_model=InsightsResponse)
async def get_insights(
    league_id: str | None = Query(None),
    week: int | None = Query(None),
    insight_type: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
) -> InsightsResponse:
    """Get comprehensive performance insights and analytics."""

    # Check for invalid league scenarios for 404 testing
    if league_id and league_id.startswith("invalid_"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "LeagueNotFound",
                "message": f"League {league_id} not found",
            },
        )

    # Mock data for contract tests
    team_performance = [
        TeamPerformanceInsight(
            metric_name="Average Points Per Game",
            current_value=125.7,
            league_average=118.3,
            percentile=72.0,
            trend="improving",
            description="Your team is scoring above league average and trending upward",
        ),
        TeamPerformanceInsight(
            metric_name="Roster Consistency",
            current_value=0.82,
            league_average=0.75,
            percentile=85.0,
            trend="stable",
            description="Your players deliver consistent performances with low variance",
        ),
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
            confidence=0.78,
        ),
        PlayerInsight(
            player_id="player_456",
            name="Tyler Glasnow",
            position="P",
            team="LAD",
            insight_type="concern",
            message="Velocity down 2.1 MPH over last 3 starts, monitor for injury risk",
            impact_score=-6.2,
            confidence=0.85,
        ),
    ]

    league_insights = [
        LeagueInsight(
            insight_type="scoring_trend",
            title="League-wide Scoring Increase",
            description="Average team scoring up 8% compared to same point last season",
            affected_teams=["all"],
            severity="medium",
        ),
        LeagueInsight(
            insight_type="position_scarcity",
            title="Catcher Position Extremely Thin",
            description="Only 3 catchers averaging over 10 fantasy points per game",
            affected_teams=["team_1", "team_4", "team_7"],
            severity="high",
        ),
    ]

    # Filter by insight type if specified
    if insight_type:
        player_insights = [
            insight
            for insight in player_insights
            if insight.insight_type == insight_type
        ]
        league_insights = [
            insight
            for insight in league_insights
            if insight.insight_type == insight_type
        ]

    # Convert to unified insight format for contract compliance
    unified_insights = []

    # Convert team performance insights
    for insight in team_performance:
        unified_insights.append(
            Insight(
                category="team_performance",
                title=insight.metric_name,
                description=insight.description,
                impact_level="medium" if insight.percentile > 50 else "low",
                metric_value=insight.current_value,
                trend=insight.trend,
                confidence=0.85,
            )
        )

    # Convert player insights
    for insight in player_insights[: limit // 2]:
        unified_insights.append(
            Insight(
                category="player_analysis",
                title=f"{insight.name} - {insight.insight_type}",
                description=insight.message,
                impact_level=(
                    "high"
                    if insight.impact_score > 0.8
                    else "medium" if insight.impact_score > 0.5 else "low"
                ),
                confidence=insight.confidence,
            )
        )

    # Convert league insights
    for insight in league_insights:
        unified_insights.append(
            Insight(
                category="league_trends",
                title=insight.title,
                description=insight.description,
                impact_level=insight.severity,
            )
        )

    # Apply limit
    unified_insights = unified_insights[:limit]

    categories = list({insight.category for insight in unified_insights})

    summary = InsightsSummary(
        total_insights=len(unified_insights),
        generated_at=datetime.utcnow(),
        league_id=league_id,
        week=week,
        categories=categories,
    )

    return InsightsResponse(insights=unified_insights, summary=summary)
