"""
Contract tests for POST /api/v1/draft/{leagueId} endpoint.

These tests validate the API contract for draft initialization.
Tests must fail before implementation (TDD approach).
"""

import pytest
from fastapi.testclient import TestClient

from main import app


class TestDraftStartContract:
    """Contract tests for draft start endpoint."""

    # Removed setup_method - using authenticated_client fixture instead
    def test_start_draft_returns_201_with_draft_data(self, authenticated_client):
        """
        Contract Test: POST /api/v1/draft/{leagueId} returns 201 with draft details.

        This test will FAIL until the endpoint is implemented.
        """
        league_id = "league_123"
        draft_data = {"draft_type": "snake", "rounds": 16, "pick_time_limit": 120}

        response = authenticated_client.post(
            f"/api/v1/draft/{league_id}", json=draft_data
        )

        assert response.status_code == 201
        data = response.json()

        # Validate response structure
        assert "draft_id" in data
        assert "league_id" in data
        assert "status" in data
        assert "current_pick" in data
        assert data["league_id"] == league_id

    def test_start_draft_with_invalid_league_returns_404(self, authenticated_client):
        """
        Contract Test: POST /api/v1/draft/invalid_league returns 404.

        This test will FAIL until validation is implemented.
        """
        draft_data = {"draft_type": "snake", "rounds": 16, "pick_time_limit": 120}

        response = authenticated_client.post(
            "/api/v1/draft/invalid_league", json=draft_data
        )

        assert response.status_code == 404
        data = response.json()

        assert "error" in data["detail"]
        assert "league not found" in data["detail"]["message"].lower()
