"""
Contract tests for GET /api/v1/sports/players endpoint.

These tests validate the API contract against the sports-data-api.yaml specification.
Tests must fail before implementation (TDD approach).
"""

import pytest
import httpx
from fastapi.testclient import TestClient

from main import app


class TestSportsPlayersGetContract:
    """Contract tests for player search endpoint."""

    # Removed setup_method - using authenticated_client fixture instead
    def test_get_players_without_filters_returns_200(self, authenticated_client):
        """
        Contract Test: GET /api/v1/sports/players returns 200 with player list.

        This test will FAIL until the endpoint is implemented.
        """
        response = authenticated_client.get("/api/v1/sports/players")

        assert response.status_code == 200
        data = response.json()

        # Validate response structure matches contract
        assert "players" in data
        assert "pagination" in data
        assert "total" in data
        assert isinstance(data["players"], list)

    def test_get_players_with_search_query_returns_filtered_results(self, authenticated_client):
        """
        Contract Test: GET /api/v1/sports/players?search=query returns filtered results.

        This test will FAIL until search functionality is implemented.
        """
        response = authenticated_client.get("/api/v1/sports/players?search=mahomes")

        assert response.status_code == 200
        data = response.json()

        assert "players" in data
        assert isinstance(data["players"], list)

        # Should have at least some results for a valid search
        if data["players"]:
            player = data["players"][0]
            assert "player_id" in player
            assert "name" in player
            assert "position" in player
            assert "team" in player

    def test_get_players_with_position_filter_returns_filtered_results(self, authenticated_client):
        """
        Contract Test: GET /api/v1/sports/players?position=QB returns QBs only.

        This test will FAIL until position filtering is implemented.
        """
        response = authenticated_client.get("/api/v1/sports/players?position=QB")

        assert response.status_code == 200
        data = response.json()

        assert "players" in data

        # All returned players should be QBs
        for player in data["players"]:
            assert player["position"] == "QB"

    def test_get_players_with_team_filter_returns_filtered_results(self, authenticated_client):
        """
        Contract Test: GET /api/v1/sports/players?team=KC returns Chiefs players only.

        This test will FAIL until team filtering is implemented.
        """
        response = authenticated_client.get("/api/v1/sports/players?team=KC")

        assert response.status_code == 200
        data = response.json()

        assert "players" in data

        # All returned players should be from KC
        for player in data["players"]:
            assert player["team"] == "KC"

    def test_get_players_with_pagination_returns_correct_structure(self, authenticated_client):
        """
        Contract Test: GET /api/v1/sports/players?page=1&limit=10 returns paginated results.

        This test will FAIL until pagination is implemented.
        """
        response = authenticated_client.get("/api/v1/sports/players?page=1&limit=10")

        assert response.status_code == 200
        data = response.json()

        assert "players" in data
        assert "pagination" in data
        assert "total" in data

        pagination = data["pagination"]
        assert "page" in pagination
        assert "limit" in pagination
        assert "total_pages" in pagination
        assert pagination["page"] == 1
        assert pagination["limit"] == 10

        # Should not return more than requested limit
        assert len(data["players"]) <= 10

    def test_get_players_with_invalid_position_returns_400(self, authenticated_client):
        """
        Contract Test: GET /api/v1/sports/players?position=INVALID returns 400.

        This test will FAIL until validation is implemented.
        """
        response = authenticated_client.get("/api/v1/sports/players?position=INVALID")

        assert response.status_code == 400
        data = response.json()

        assert "error" in data
        assert "message" in data

    def test_get_players_with_invalid_pagination_returns_400(self, authenticated_client):
        """
        Contract Test: GET /api/v1/sports/players?page=0 returns 400.

        This test will FAIL until validation is implemented.
        """
        response = authenticated_client.get("/api/v1/sports/players?page=0")

        assert response.status_code == 400
        data = response.json()

        assert "error" in data

    def test_get_players_response_includes_required_fields(self, authenticated_client):
        """
        Contract Test: Response includes all required fields per API specification.

        This test will FAIL until proper response model is implemented.
        """
        response = authenticated_client.get("/api/v1/sports/players?limit=1")

        assert response.status_code == 200
        data = response.json()

        if data["players"]:
            player = data["players"][0]

            # Required fields per contract
            required_fields = [
                "player_id",
                "external_id",
                "name",
                "position",
                "team",
                "sport",
                "status",
                "injury_status",
            ]

            for field in required_fields:
                assert field in player, f"Missing required field: {field}"

    def test_get_players_with_stats_includes_stats_data(self, authenticated_client):
        """
        Contract Test: GET /api/v1/sports/players?include_stats=true includes statistics.

        This test will FAIL until stats inclusion is implemented.
        """
        response = authenticated_client.get("/api/v1/sports/players?include_stats=true&limit=1")

        assert response.status_code == 200
        data = response.json()

        if data["players"]:
            player = data["players"][0]
            assert "season_stats" in player
            assert "game_stats" in player

    def test_get_players_supports_cors_headers(self, authenticated_client):
        """
        Contract Test: Endpoint returns proper CORS headers.

        This test will FAIL until CORS is properly configured.
        """
        # Preflight request
        response = authenticated_client.options("/api/v1/sports/players")

        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers

    def test_get_players_includes_response_time_header(self, authenticated_client):
        """
        Contract Test: Response includes performance monitoring headers.

        This test will FAIL until performance headers are implemented.
        """
        response = authenticated_client.get("/api/v1/sports/players?limit=5")

        assert response.status_code == 200

        # Should include response time for monitoring
        assert (
            "X-Response-Time" in response.headers
            or "X-Process-Time" in response.headers
        )

    def test_get_players_rate_limiting_headers(self, authenticated_client):
        """
        Contract Test: Response includes rate limiting headers.

        This test will FAIL until rate limiting is implemented.
        """
        response = authenticated_client.get("/api/v1/sports/players")

        assert response.status_code == 200

        # Rate limiting headers
        expected_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ]

        # At least one rate limiting header should be present
        rate_limit_headers = [h for h in expected_headers if h in response.headers]
        assert len(rate_limit_headers) > 0, "No rate limiting headers found"

    def test_get_players_without_auth_returns_401(self, unauthenticated_client):
        """
        Contract Test: GET /api/v1/sports/players without auth returns 401.

        This test validates that authentication is properly required.
        """
        response = unauthenticated_client.get("/api/v1/sports/players")

        assert response.status_code == 401
        data = response.json()

        assert "detail" in data
        assert "authentication" in data["detail"].lower()

    def test_get_players_with_invalid_token_returns_401(self, invalid_auth_client):
        """
        Contract Test: GET /api/v1/sports/players with invalid token returns 401.

        This test validates that token validation is working.
        """
        response = invalid_auth_client.get("/api/v1/sports/players")

        assert response.status_code == 401
