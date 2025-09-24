"""
Contract tests for GET /api/v1/analytics/insights endpoint.

These tests validate the API contract for analytics insights.
Tests must fail before implementation (TDD approach).
"""

import pytest
from fastapi.testclient import TestClient

from main import app


class TestAnalyticsInsightsContract:
    """Contract tests for analytics insights endpoint."""

    # Removed setup_method - using authenticated_client fixture instead
    def test_get_insights_returns_200_with_insights(self, authenticated_client):
        """
        Contract Test: GET /api/v1/analytics/insights returns 200 with insights.

        This test will FAIL until the endpoint is implemented.
        """
        response = authenticated_client.get("/api/v1/analytics/insights?league_id=league_123")

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "insights" in data
        assert "summary" in data
        assert isinstance(data["insights"], list)

        if data["insights"]:
            insight = data["insights"][0]
            assert "category" in insight
            assert "title" in insight
            assert "description" in insight
            assert "impact_level" in insight

    def test_get_insights_with_invalid_league_returns_404(self, authenticated_client):
        """
        Contract Test: GET insights with invalid league returns 404.

        This test will FAIL until validation is implemented.
        """
        response = authenticated_client.get(
            "/api/v1/analytics/insights?league_id=invalid_league"
        )

        assert response.status_code == 404
        data = response.json()

        assert "error" in data
        assert "league not found" in data["message"].lower()

    def test_get_insights_includes_different_categories(self, authenticated_client):
        """
        Contract Test: Insights include different analytical categories.

        This test will FAIL until analytics engine is implemented.
        """
        response = authenticated_client.get("/api/v1/analytics/insights?league_id=league_123")

        assert response.status_code == 200
        data = response.json()

        categories = [insight["category"] for insight in data["insights"]]
        expected_categories = [
            "performance",
            "trends",
            "matchup_analysis",
            "roster_balance",
        ]

        # Should have insights from multiple categories
        assert len(set(categories)) >= 2

    def test_get_insights_includes_impact_levels(self, authenticated_client):
        """
        Contract Test: Insights include impact level ratings.

        This test will FAIL until impact analysis is implemented.
        """
        response = authenticated_client.get("/api/v1/analytics/insights?league_id=league_123")

        assert response.status_code == 200
        data = response.json()

        for insight in data["insights"]:
            assert "impact_level" in insight
            assert insight["impact_level"] in ["low", "medium", "high", "critical"]
