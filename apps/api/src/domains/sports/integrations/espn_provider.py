"""
ESPN Sports API integration.

Provides concrete implementation of SportsDataProvider protocol for ESPN API.
Handles ESPN-specific data formats, endpoints, and authentication.
"""

import logging
from datetime import datetime
from typing import Any

from domains.sports.services.sports_data_service import (
    InjuryReport,
    PlayerProjection,
    PlayerStats,
    SportsDataProvider,
    SportsDataServiceError,
)

from .api_client import APIConfig, APIError, RateLimitConfig, SportsAPIClient
from .data_normalizer import (
    normalize_game_data,
    normalize_stats_data,
)

logger = logging.getLogger(__name__)


class ESPNSportsProvider(SportsDataProvider):
    """
    ESPN Sports API provider implementation.

    Provides access to ESPN's comprehensive sports data including:
    - Player information and statistics
    - Team rosters and schedules
    - Live scores and game data
    - Injury reports
    """

    def __init__(self, api_key: str | None = None):
        """Initialize ESPN provider."""
        self.config = APIConfig(
            base_url="https://site.api.espn.com/apis/site/v2/sports",
            api_key=api_key,
            timeout=30,
            max_retries=3,
            retry_delay=1.0,
            rate_limit=RateLimitConfig(
                requests_per_minute=100, burst_limit=20, window_size=60
            ),
            headers={
                "Accept": "application/json",
                "User-Agent": "Ultimate Fantasy Platform/1.0",
            },
        )
        self.client: SportsAPIClient | None = None

    async def _get_client(self) -> SportsAPIClient:
        """Get or create API client."""
        if self.client is None:
            self.client = SportsAPIClient(self.config)
            await self.client._create_session()
        return self.client

    def _get_sport_endpoint(self, sport: str) -> str:
        """Get ESPN sport endpoint."""
        sport_mappings = {
            "NFL": "football/nfl",
            "NBA": "basketball/nba",
            "MLB": "baseball/mlb",
            "NHL": "hockey/nhl",
            "WNBA": "basketball/wnba",
            "MLS": "soccer/usa.1",
        }
        return sport_mappings.get(sport.upper(), "football/nfl")

    async def get_players(
        self,
        sport: str = "NFL",
        position: str | None = None,
        team: str | None = None,
        active_only: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Get players data from ESPN API.

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
            sport_endpoint = self._get_sport_endpoint(sport)

            # ESPN doesn't have a direct players endpoint, so we get team rosters
            if team:
                teams = [team]
            else:
                # Get all teams first
                teams_data = await self.get_teams(sport)
                teams = [team_data["abbreviation"] for team_data in teams_data]

            all_players = []

            for team_abbr in teams:
                try:
                    # Get team roster
                    endpoint = f"{sport_endpoint}/teams/{team_abbr}/roster"
                    response = await client.get(endpoint)

                    if "team" in response and "athletes" in response["team"]:
                        athletes = response["team"]["athletes"]

                        for athlete_group in athletes:
                            items = athlete_group.get("items", [])

                            for athlete in items:
                                player_data = self._normalize_espn_player(
                                    athlete, team_abbr, sport
                                )

                                # Apply filters
                                if position and player_data.get("position") != position:
                                    continue

                                if active_only and not player_data.get("active", True):
                                    continue

                                all_players.append(player_data)

                except APIError as e:
                    logger.warning(f"Failed to get roster for team {team_abbr}: {e}")
                    continue

            return all_players

        except Exception as e:
            logger.error(f"Failed to get players from ESPN: {e}")
            raise SportsDataServiceError(f"ESPN API error: {e}")

    def _normalize_espn_player(
        self, athlete: dict[str, Any], team: str, sport: str
    ) -> dict[str, Any]:
        """Normalize ESPN athlete data to standard format."""
        return {
            "player_id": str(athlete.get("id", "")),
            "external_id": str(athlete.get("id", "")),
            "name": athlete.get("displayName", ""),
            "position": athlete.get("position", {}).get("abbreviation", ""),
            "team": team,
            "sport": sport,
            "status": "active",
            "injury_status": "healthy",  # ESPN injury data requires separate call
            "height": athlete.get("height"),
            "weight": athlete.get("weight"),
            "age": athlete.get("age"),
            "experience": athlete.get("experience"),
            "jersey_number": athlete.get("jersey"),
            "headshot_url": athlete.get("headshot", {}).get("href"),
            "espn_url": (
                athlete.get("links", [{}])[0].get("href")
                if athlete.get("links")
                else None
            ),
        }

    async def get_player_stats(
        self, player_id: str, season: str, week: int | None = None
    ) -> PlayerStats | None:
        """
        Get player statistics from ESPN.

        Args:
            player_id: ESPN player ID
            season: Season year
            week: Optional week number

        Returns:
            PlayerStats object or None
        """
        try:
            client = await self._get_client()

            # ESPN player stats endpoint
            endpoint = f"football/nfl/athletes/{player_id}/statistics"
            params = {"season": season}
            if week:
                params["week"] = week

            response = await client.get(endpoint, params=params)

            if "statistics" not in response:
                return None

            stats_data = response["statistics"]

            # Find the player basic info
            player_info = response.get("athlete", {})

            # Normalize statistics based on sport/position
            normalized_stats = normalize_stats_data(
                stats_data, player_info.get("position", {}).get("abbreviation", "")
            )

            return PlayerStats(
                player_id=player_id,
                external_id=player_id,
                season=season,
                week=week,
                games_played=stats_data.get("splits", {})
                .get("categories", [{}])[0]
                .get("stats", [{}])[0]
                .get("value", 0),
                stats=normalized_stats,
                fantasy_points=self._calculate_fantasy_points(
                    normalized_stats,
                    player_info.get("position", {}).get("abbreviation", ""),
                ),
                position=player_info.get("position", {}).get("abbreviation", ""),
                team=player_info.get("team", {}).get("abbreviation", ""),
            )

        except Exception as e:
            logger.error(f"Failed to get player stats from ESPN: {e}")
            return None

    def _calculate_fantasy_points(self, stats: dict[str, Any], position: str) -> float:
        """Calculate fantasy points based on stats and position."""
        if not stats:
            return 0.0

        points = 0.0

        if position == "QB":
            points += stats.get("passing_yards", 0) * 0.04  # 1 pt per 25 yards
            points += stats.get("passing_touchdowns", 0) * 4  # 4 pts per TD
            points -= stats.get("interceptions", 0) * 2  # -2 pts per INT
            points += stats.get("rushing_yards", 0) * 0.1  # 1 pt per 10 yards
            points += stats.get("rushing_touchdowns", 0) * 6  # 6 pts per TD

        elif position in ["RB", "WR", "TE"]:
            points += stats.get("rushing_yards", 0) * 0.1  # 1 pt per 10 yards
            points += stats.get("rushing_touchdowns", 0) * 6  # 6 pts per TD
            points += stats.get("receiving_yards", 0) * 0.1  # 1 pt per 10 yards
            points += stats.get("receiving_touchdowns", 0) * 6  # 6 pts per TD
            points += stats.get("receptions", 0) * 1  # 1 pt per reception (PPR)

        elif position == "K":
            points += stats.get("field_goals_made", 0) * 3  # 3 pts per FG
            points += stats.get("extra_points_made", 0) * 1  # 1 pt per XP

        elif position == "DEF":
            points += stats.get("defensive_touchdowns", 0) * 6
            points += stats.get("interceptions", 0) * 2
            points += stats.get("fumble_recoveries", 0) * 2
            points += stats.get("sacks", 0) * 1
            points += stats.get("safeties", 0) * 2

        return round(points, 2)

    async def get_player_projections(
        self, player_id: str, week: int, season: str
    ) -> PlayerProjection | None:
        """
        Get player projections from ESPN.

        ESPN doesn't provide direct projections API, so we'll calculate
        based on recent performance and league averages.
        """
        try:
            # Get recent stats to base projections on
            recent_stats = await self.get_player_stats(player_id, season)
            if not recent_stats:
                return None

            # Simple projection based on season averages
            games_played = max(recent_stats.games_played, 1)
            projected_stats = {}

            for stat, value in recent_stats.stats.items():
                if isinstance(value, (int, float)):
                    # Project weekly average
                    projected_stats[stat] = round(value / games_played, 2)

            projected_fantasy_points = self._calculate_fantasy_points(
                projected_stats, recent_stats.position
            )

            return PlayerProjection(
                player_id=player_id,
                week=week,
                season=season,
                projected_stats=projected_stats,
                projected_fantasy_points=projected_fantasy_points,
                confidence=0.75,  # Medium confidence for ESPN projections
                last_updated=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Failed to get player projections: {e}")
            return None

    async def get_injury_report(
        self, player_id: str | None = None, team: str | None = None
    ) -> list[InjuryReport]:
        """
        Get injury reports from ESPN.

        Args:
            player_id: Optional specific player
            team: Optional team filter

        Returns:
            List of injury reports
        """
        try:
            client = await self._get_client()
            injuries = []

            if player_id:
                # Get specific player injury info
                endpoint = f"football/nfl/athletes/{player_id}"
                response = await client.get(endpoint)

                athlete = response.get("athlete", {})
                if "injuries" in athlete:
                    for injury in athlete["injuries"]:
                        injuries.append(self._normalize_espn_injury(injury, player_id))

            else:
                # Get league-wide injury report
                endpoint = "football/nfl/news"
                params = {"limit": 50}
                if team:
                    params["team"] = team

                response = await client.get(endpoint, params=params)

                # Parse news for injury-related content
                for article in response.get("articles", []):
                    if any(
                        keyword in article.get("headline", "").lower()
                        for keyword in [
                            "injury",
                            "injured",
                            "out",
                            "questionable",
                            "doubtful",
                        ]
                    ):
                        # This is a simplified approach - in practice, you'd need
                        # more sophisticated parsing or a dedicated injury endpoint
                        pass

            return injuries

        except Exception as e:
            logger.error(f"Failed to get injury reports from ESPN: {e}")
            return []

    def _normalize_espn_injury(
        self, injury_data: dict[str, Any], player_id: str
    ) -> InjuryReport:
        """Normalize ESPN injury data."""
        status_mapping = {
            "OUT": "out",
            "QUESTIONABLE": "questionable",
            "DOUBTFUL": "doubtful",
            "PROBABLE": "questionable",
            "HEALTHY": "healthy",
        }

        status = injury_data.get("status", "HEALTHY").upper()
        normalized_status = status_mapping.get(status, "healthy")

        return InjuryReport(
            player_id=player_id,
            status=normalized_status,
            description=injury_data.get("description"),
            return_date=None,  # ESPN doesn't always provide return dates
            severity=(
                "medium"
                if normalized_status in ["questionable", "doubtful"]
                else "high" if normalized_status == "out" else "low"
            ),
            last_updated=datetime.utcnow(),
        )

    async def get_teams(self, sport: str = "NFL") -> list[dict[str, Any]]:
        """
        Get teams data from ESPN.

        Args:
            sport: Sport type

        Returns:
            List of team dictionaries
        """
        try:
            client = await self._get_client()
            sport_endpoint = self._get_sport_endpoint(sport)

            endpoint = f"{sport_endpoint}/teams"
            response = await client.get(endpoint)

            teams = []
            if "sports" in response:
                for sport_data in response["sports"]:
                    for league in sport_data.get("leagues", []):
                        for team in league.get("teams", []):
                            teams.append(self._normalize_espn_team(team["team"]))

            return teams

        except Exception as e:
            logger.error(f"Failed to get teams from ESPN: {e}")
            raise SportsDataServiceError(f"ESPN teams API error: {e}")

    def _normalize_espn_team(self, team_data: dict[str, Any]) -> dict[str, Any]:
        """Normalize ESPN team data."""
        return {
            "team_id": team_data.get("abbreviation", ""),
            "name": team_data.get("displayName", ""),
            "city": team_data.get("location", ""),
            "abbreviation": team_data.get("abbreviation", ""),
            "conference": None,  # Would need additional API call
            "division": None,  # Would need additional API call
            "sport": "NFL",  # Assume NFL for now
            "logo_url": (
                team_data.get("logos", [{}])[0].get("href")
                if team_data.get("logos")
                else None
            ),
            "color": team_data.get("color"),
            "alternate_color": team_data.get("alternateColor"),
        }

    async def get_schedule(
        self, season: str, week: int | None = None, team: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Get schedule data from ESPN.

        Args:
            season: Season year
            week: Optional week number
            team: Optional team filter

        Returns:
            List of game dictionaries
        """
        try:
            client = await self._get_client()

            # ESPN scoreboard endpoint
            endpoint = "football/nfl/scoreboard"
            params = {"seasontype": "2", "season": season}  # Regular season

            if week:
                params["week"] = week

            response = await client.get(endpoint, params=params)

            games = []
            for event in response.get("events", []):
                game_data = normalize_game_data(event)

                # Apply team filter if specified
                if team and not any(
                    comp.get("team", {}).get("abbreviation") == team
                    for comp in event.get("competitions", [{}])[0].get(
                        "competitors", []
                    )
                ):
                    continue

                games.append(game_data)

            return games

        except Exception as e:
            logger.error(f"Failed to get schedule from ESPN: {e}")
            return []

    async def close(self):
        """Close API client."""
        if self.client:
            await self.client._close_session()
            self.client = None
