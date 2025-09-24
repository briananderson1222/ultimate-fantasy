"""
The Athletic API integration.

Provides concrete implementation of SportsDataProvider protocol for The Athletic API.
Handles The Athletic-specific data formats, endpoints, and authentication.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from domains.sports.services.sports_data_service import (
    SportsDataProvider,
    PlayerStats,
    PlayerProjection,
    InjuryReport,
    SportsDataServiceError
)
from .api_client import SportsAPIClient, APIConfig, RateLimitConfig, APIError
from .data_normalizer import normalize_player_data, normalize_game_data, normalize_stats_data

logger = logging.getLogger(__name__)


class AthleticSportsProvider(SportsDataProvider):
    """
    The Athletic API provider implementation.

    Provides access to The Athletic's premium sports data including:
    - In-depth player analysis and statistics
    - Advanced metrics and projections
    - Detailed injury reports and analysis
    - Expert commentary and insights
    """

    def __init__(self, api_key: str):
        """Initialize The Athletic provider."""
        if not api_key:
            raise ValueError("The Athletic API key is required")

        self.config = APIConfig(
            base_url="https://api.theathletic.com/v1",
            api_key=api_key,
            timeout=30,
            max_retries=3,
            retry_delay=2.0,
            rate_limit=RateLimitConfig(
                requests_per_minute=60,
                burst_limit=10,
                window_size=60
            ),
            headers={
                "Accept": "application/json",
                "User-Agent": "Ultimate Fantasy Platform/1.0",
                "X-API-Version": "v1"
            }
        )
        self.client: Optional[SportsAPIClient] = None

    async def _get_client(self) -> SportsAPIClient:
        """Get or create API client."""
        if self.client is None:
            self.client = SportsAPIClient(self.config)
            await self.client._create_session()
        return self.client

    def _get_sport_id(self, sport: str) -> str:
        """Get The Athletic sport identifier."""
        sport_mappings = {
            "NFL": "nfl",
            "NBA": "nba",
            "MLB": "mlb",
            "NHL": "nhl",
            "WNBA": "wnba",
            "MLS": "mls"
        }
        return sport_mappings.get(sport.upper(), "nfl")

    async def get_players(
        self,
        sport: str = "NFL",
        position: Optional[str] = None,
        team: Optional[str] = None,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get players data from The Athletic API.

        Args:
            sport: Sport type (NFL, NBA, etc.)
            position: Filter by position
            team: Filter by team
            active_only: Only active players

        Returns:
            List of player dictionaries
        """
        try:
            client = await self._get_client()
            sport_id = self._get_sport_id(sport)

            endpoint = f"sports/{sport_id}/players"
            params = {
                "limit": 1000,
                "active": active_only
            }

            if position:
                params["position"] = position
            if team:
                params["team"] = team

            response = await client.get(endpoint, params=params)

            players = []
            for player_data in response.get("data", []):
                normalized_player = self._normalize_athletic_player(player_data, sport)
                players.append(normalized_player)

            return players

        except Exception as e:
            logger.error(f"Failed to get players from The Athletic: {e}")
            raise SportsDataServiceError(f"The Athletic API error: {e}")

    def _normalize_athletic_player(self, player_data: Dict[str, Any], sport: str) -> Dict[str, Any]:
        """Normalize The Athletic player data to standard format."""
        return {
            "player_id": str(player_data.get("id", "")),
            "external_id": str(player_data.get("id", "")),
            "name": player_data.get("display_name", ""),
            "position": player_data.get("position", ""),
            "team": player_data.get("team", {}).get("abbreviation", ""),
            "sport": sport,
            "status": "active" if player_data.get("active", True) else "inactive",
            "injury_status": player_data.get("injury_status", "healthy"),
            "height": player_data.get("height"),
            "weight": player_data.get("weight"),
            "age": player_data.get("age"),
            "experience": player_data.get("years_pro"),
            "jersey_number": player_data.get("jersey_number"),
            "draft_year": player_data.get("draft_year"),
            "draft_round": player_data.get("draft_round"),
            "draft_pick": player_data.get("draft_pick"),
            "salary": player_data.get("salary"),
            "contract_years": player_data.get("contract_years"),
            "headshot_url": player_data.get("headshot_url"),
            "athletic_url": player_data.get("athletic_url"),
            "fantasy_rating": player_data.get("fantasy_rating"),
            "analyst_notes": player_data.get("analyst_notes")
        }

    async def get_player_stats(
        self,
        player_id: str,
        season: str,
        week: Optional[int] = None
    ) -> Optional[PlayerStats]:
        """
        Get player statistics from The Athletic.

        Args:
            player_id: The Athletic player ID
            season: Season year
            week: Optional week number

        Returns:
            PlayerStats object or None
        """
        try:
            client = await self._get_client()

            endpoint = f"players/{player_id}/stats"
            params = {"season": season}
            if week:
                params["week"] = week

            response = await client.get(endpoint, params=params)

            if "data" not in response:
                return None

            stats_data = response["data"]
            player_info = stats_data.get("player", {})

            # The Athletic provides advanced metrics
            advanced_stats = stats_data.get("advanced_metrics", {})
            basic_stats = stats_data.get("traditional_stats", {})

            # Combine traditional and advanced stats
            combined_stats = {**basic_stats, **advanced_stats}

            # Normalize based on position
            normalized_stats = normalize_stats_data(
                combined_stats,
                player_info.get("position", "")
            )

            return PlayerStats(
                player_id=player_id,
                external_id=player_id,
                season=season,
                week=week,
                games_played=stats_data.get("games_played", 0),
                stats=normalized_stats,
                fantasy_points=stats_data.get("fantasy_points", 0.0),
                position=player_info.get("position", ""),
                team=player_info.get("team", {}).get("abbreviation", "")
            )

        except Exception as e:
            logger.error(f"Failed to get player stats from The Athletic: {e}")
            return None

    async def get_player_projections(
        self,
        player_id: str,
        week: int,
        season: str
    ) -> Optional[PlayerProjection]:
        """
        Get player projections from The Athletic.

        The Athletic provides expert projections and analysis.
        """
        try:
            client = await self._get_client()

            endpoint = f"players/{player_id}/projections"
            params = {
                "season": season,
                "week": week
            }

            response = await client.get(endpoint, params=params)

            if "data" not in response:
                return None

            projection_data = response["data"]

            return PlayerProjection(
                player_id=player_id,
                week=week,
                season=season,
                projected_stats=projection_data.get("projected_stats", {}),
                projected_fantasy_points=projection_data.get("projected_fantasy_points", 0.0),
                confidence=projection_data.get("confidence_score", 0.8),
                last_updated=datetime.fromisoformat(
                    projection_data.get("last_updated", datetime.utcnow().isoformat())
                )
            )

        except Exception as e:
            logger.error(f"Failed to get player projections from The Athletic: {e}")
            return None

    async def get_injury_report(
        self,
        player_id: Optional[str] = None,
        team: Optional[str] = None
    ) -> List[InjuryReport]:
        """
        Get comprehensive injury reports from The Athletic.

        Args:
            player_id: Optional specific player
            team: Optional team filter

        Returns:
            List of detailed injury reports
        """
        try:
            client = await self._get_client()
            injuries = []

            if player_id:
                endpoint = f"players/{player_id}/injury-status"
                response = await client.get(endpoint)

                if "data" in response:
                    injury_data = response["data"]
                    injuries.append(self._normalize_athletic_injury(injury_data, player_id))

            else:
                endpoint = "injuries"
                params = {"active": True}
                if team:
                    params["team"] = team

                response = await client.get(endpoint, params=params)

                for injury_data in response.get("data", []):
                    injuries.append(
                        self._normalize_athletic_injury(
                            injury_data,
                            injury_data.get("player_id")
                        )
                    )

            return injuries

        except Exception as e:
            logger.error(f"Failed to get injury reports from The Athletic: {e}")
            return []

    def _normalize_athletic_injury(self, injury_data: Dict[str, Any], player_id: str) -> InjuryReport:
        """Normalize The Athletic injury data."""
        status_mapping = {
            "healthy": "healthy",
            "questionable": "questionable",
            "doubtful": "doubtful",
            "out": "out",
            "ir": "ir",
            "suspended": "out"
        }

        status = injury_data.get("status", "healthy").lower()
        normalized_status = status_mapping.get(status, "healthy")

        # The Athletic provides detailed injury analysis
        severity_score = injury_data.get("severity_score", 5)
        if severity_score <= 3:
            severity = "low"
        elif severity_score <= 7:
            severity = "medium"
        else:
            severity = "high"

        return_date = None
        if injury_data.get("expected_return_date"):
            return_date = datetime.fromisoformat(injury_data["expected_return_date"])

        return InjuryReport(
            player_id=player_id,
            status=normalized_status,
            description=injury_data.get("description"),
            return_date=return_date,
            severity=severity,
            last_updated=datetime.fromisoformat(
                injury_data.get("last_updated", datetime.utcnow().isoformat())
            )
        )

    async def get_teams(self, sport: str = "NFL") -> List[Dict[str, Any]]:
        """
        Get teams data from The Athletic.

        Args:
            sport: Sport type

        Returns:
            List of team dictionaries
        """
        try:
            client = await self._get_client()
            sport_id = self._get_sport_id(sport)

            endpoint = f"sports/{sport_id}/teams"
            response = await client.get(endpoint)

            teams = []
            for team_data in response.get("data", []):
                teams.append(self._normalize_athletic_team(team_data, sport))

            return teams

        except Exception as e:
            logger.error(f"Failed to get teams from The Athletic: {e}")
            raise SportsDataServiceError(f"The Athletic teams API error: {e}")

    def _normalize_athletic_team(self, team_data: Dict[str, Any], sport: str) -> Dict[str, Any]:
        """Normalize The Athletic team data."""
        return {
            "team_id": team_data.get("abbreviation", ""),
            "name": team_data.get("display_name", ""),
            "city": team_data.get("city", ""),
            "abbreviation": team_data.get("abbreviation", ""),
            "conference": team_data.get("conference", ""),
            "division": team_data.get("division", ""),
            "sport": sport,
            "logo_url": team_data.get("logo_url"),
            "primary_color": team_data.get("primary_color"),
            "secondary_color": team_data.get("secondary_color"),
            "founded": team_data.get("founded_year"),
            "stadium": team_data.get("stadium", {}).get("name"),
            "stadium_capacity": team_data.get("stadium", {}).get("capacity"),
            "head_coach": team_data.get("head_coach", {}).get("name"),
            "general_manager": team_data.get("general_manager", {}).get("name"),
            "owner": team_data.get("owner", {}).get("name"),
            "market_value": team_data.get("market_value"),
            "payroll": team_data.get("payroll")
        }

    async def get_schedule(
        self,
        season: str,
        week: Optional[int] = None,
        team: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get schedule data from The Athletic.

        Args:
            season: Season year
            week: Optional week number
            team: Optional team filter

        Returns:
            List of game dictionaries
        """
        try:
            client = await self._get_client()

            endpoint = "schedule"
            params = {"season": season}
            if week:
                params["week"] = week
            if team:
                params["team"] = team

            response = await client.get(endpoint, params=params)

            games = []
            for game_data in response.get("data", []):
                normalized_game = normalize_game_data(game_data)

                # Add The Athletic specific data
                normalized_game.update({
                    "betting_line": game_data.get("betting_line"),
                    "over_under": game_data.get("over_under"),
                    "weather": game_data.get("weather"),
                    "attendance": game_data.get("attendance"),
                    "tv_coverage": game_data.get("tv_coverage"),
                    "analyst_preview": game_data.get("analyst_preview"),
                    "key_matchups": game_data.get("key_matchups", [])
                })

                games.append(normalized_game)

            return games

        except Exception as e:
            logger.error(f"Failed to get schedule from The Athletic: {e}")
            return []

    async def get_advanced_metrics(self, player_id: str, metric_types: List[str]) -> Dict[str, Any]:
        """
        Get advanced player metrics from The Athletic.

        Args:
            player_id: Player ID
            metric_types: List of metric types to retrieve

        Returns:
            Dictionary of advanced metrics
        """
        try:
            client = await self._get_client()

            endpoint = f"players/{player_id}/advanced-metrics"
            params = {"metrics": ",".join(metric_types)}

            response = await client.get(endpoint, params=params)

            return response.get("data", {})

        except Exception as e:
            logger.error(f"Failed to get advanced metrics: {e}")
            return {}

    async def get_expert_analysis(self, player_id: str) -> Dict[str, Any]:
        """
        Get expert analysis and commentary for a player.

        Args:
            player_id: Player ID

        Returns:
            Expert analysis data
        """
        try:
            client = await self._get_client()

            endpoint = f"players/{player_id}/analysis"
            response = await client.get(endpoint)

            return {
                "outlook": response.get("data", {}).get("season_outlook"),
                "strengths": response.get("data", {}).get("strengths", []),
                "weaknesses": response.get("data", {}).get("weaknesses", []),
                "fantasy_analysis": response.get("data", {}).get("fantasy_analysis"),
                "analyst_rating": response.get("data", {}).get("analyst_rating"),
                "last_updated": response.get("data", {}).get("last_updated")
            }

        except Exception as e:
            logger.error(f"Failed to get expert analysis: {e}")
            return {}

    async def close(self):
        """Close API client."""
        if self.client:
            await self.client._close_session()
            self.client = None