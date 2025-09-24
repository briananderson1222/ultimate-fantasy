"""
ESPN API provider implementation for sports data integration.

Provides real ESPN API integration with:
- Player data from ESPN APIs
- Game schedules and scores
- Team information and rosters
- Injury reports and news
- Statistics and projections
- Rate limiting and error handling
- Data normalization to standard format
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    aiohttp = None
    AIOHTTP_AVAILABLE = False

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    httpx = None
    HTTPX_AVAILABLE = False

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging
    get_logger = logging.getLogger  # type: ignore[assignment]

logger = get_logger(__name__)


class ESPNProviderError(Exception):
    """ESPN API provider errors."""
    pass


class RateLimitError(ESPNProviderError):
    """Rate limit exceeded."""
    pass


class ESPNAPIProvider:
    """ESPN API provider for sports data."""

    def __init__(
        self,
        base_url: str = "https://site.api.espn.com/apis/site/v2/sports",
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_per_minute: int = 100,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_per_minute = rate_limit_per_minute

        # Rate limiting
        self.request_times: List[datetime] = []

        # Sport mappings
        self.sport_mappings = {
            "mlb": "baseball/mlb",
            "nfl": "football/nfl",
            "wnba": "basketball/wnba",
            "nba": "basketball/nba",
        }

    async def get_players(
        self,
        sport: str = "nfl",
        position: Optional[str] = None,
        team: Optional[str] = None,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get players data from ESPN API.

        Args:
            sport: Sport type (nfl, mlb, wnba, nba)
            position: Filter by position
            team: Filter by team
            active_only: Only active players

        Returns:
            List of player dictionaries
        """
        await self._check_rate_limit()

        sport_path = self.sport_mappings.get(sport.lower(), "football/nfl")

        if team:
            # Get team roster
            return await self._get_team_roster(sport_path, team, position, active_only)
        else:
            # Get all players (requires multiple team requests)
            return await self._get_all_players(sport_path, position, active_only)

    async def get_player_stats(
        self,
        player_id: str,
        season: str,
        week: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get player statistics from ESPN.

        Args:
            player_id: ESPN player ID
            season: Season year
            week: Specific week (None for season stats)

        Returns:
            Player stats dictionary or None
        """
        await self._check_rate_limit()

        try:
            # ESPN player stats endpoint
            url = f"{self.base_url}/athletes/{player_id}/statistics"
            params = {"season": season}
            if week:
                params["week"] = str(week)

            data = await self._make_request(url, params)

            if not data or "statistics" not in data:
                return None

            # Normalize stats format
            return self._normalize_player_stats(data["statistics"], player_id, season, week)

        except Exception as e:
            logger.warning(f"Failed to get player stats for {player_id}: {e}")
            return None

    async def get_player_projections(
        self,
        player_id: str,
        week: int,
        season: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get player projections (ESPN doesn't provide projections directly).

        Args:
            player_id: ESPN player ID
            week: Week number
            season: Season year

        Returns:
            Projected stats or None
        """
        # ESPN doesn't provide projections in their public API
        # This would need to be calculated based on historical performance
        logger.debug(f"ESPN projections not available for player {player_id}")
        return None

    async def get_injury_report(
        self,
        player_id: Optional[str] = None,
        team: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get injury reports from ESPN.

        Args:
            player_id: Specific player ID
            team: Team to get injuries for

        Returns:
            List of injury reports
        """
        await self._check_rate_limit()

        injuries = []

        if player_id:
            # Get specific player's injury status
            injury = await self._get_player_injury_status(player_id)
            if injury:
                injuries.append(injury)
        elif team:
            # Get team injury report
            team_injuries = await self._get_team_injury_report(team)
            injuries.extend(team_injuries)
        else:
            # Get league-wide injuries (limited scope)
            logger.warning("League-wide injury reports not supported")

        return injuries

    async def get_teams(self, sport: str = "nfl") -> List[Dict[str, Any]]:
        """
        Get teams data from ESPN.

        Args:
            sport: Sport type

        Returns:
            List of team dictionaries
        """
        await self._check_rate_limit()

        sport_path = self.sport_mappings.get(sport.lower(), "football/nfl")
        url = f"{self.base_url}/{sport_path}/teams"

        try:
            data = await self._make_request(url)

            if not data or "sports" not in data:
                return []

            teams = []
            for sport_data in data["sports"]:
                for league in sport_data.get("leagues", []):
                    for team_data in league.get("teams", []):
                        team = team_data.get("team", {})
                        teams.append(self._normalize_team_data(team))

            return teams

        except Exception as e:
            logger.error(f"Failed to get teams for {sport}: {e}")
            return []

    async def get_schedule(
        self,
        season: str,
        week: Optional[int] = None,
        team: Optional[str] = None,
        sport: str = "nfl",
    ) -> List[Dict[str, Any]]:
        """
        Get schedule data from ESPN.

        Args:
            season: Season year
            week: Specific week
            team: Specific team
            sport: Sport type

        Returns:
            List of game dictionaries
        """
        await self._check_rate_limit()

        sport_path = self.sport_mappings.get(sport.lower(), "football/nfl")

        if week:
            url = f"{self.base_url}/{sport_path}/scoreboard"
            params = {"seasontype": "2", "week": str(week)}
        else:
            url = f"{self.base_url}/{sport_path}/scoreboard"
            params = {"seasontype": "2"}

        try:
            data = await self._make_request(url, params)

            if not data or "events" not in data:
                return []

            games = []
            for event in data["events"]:
                game = self._normalize_game_data(event)

                # Filter by team if specified
                if team and not self._game_involves_team(game, team):
                    continue

                games.append(game)

            return games

        except Exception as e:
            logger.error(f"Failed to get schedule: {e}")
            return []

    async def get_scores(
        self,
        sport: str = "nfl",
        date: Optional[date] = None,
        live_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get live scores and game data from ESPN.

        Args:
            sport: Sport type
            date: Specific date (defaults to today)
            live_only: Only in-progress games

        Returns:
            List of game scores
        """
        await self._check_rate_limit()

        sport_path = self.sport_mappings.get(sport.lower(), "football/nfl")
        url = f"{self.base_url}/{sport_path}/scoreboard"

        params = {}
        if date:
            params["dates"] = date.strftime("%Y%m%d")

        try:
            data = await self._make_request(url, params)

            if not data or "events" not in data:
                return []

            games = []
            for event in data["events"]:
                game = self._normalize_game_data(event, include_scores=True)

                # Filter live games if requested
                if live_only and game.get("status") != "in_progress":
                    continue

                games.append(game)

            return games

        except Exception as e:
            logger.error(f"Failed to get scores: {e}")
            return []

    # Private helper methods

    async def _check_rate_limit(self):
        """Check and enforce rate limiting."""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)

        # Remove old requests
        self.request_times = [t for t in self.request_times if t > cutoff]

        if len(self.request_times) >= self.rate_limit_per_minute:
            wait_time = 60 - (now - self.request_times[0]).total_seconds()
            if wait_time > 0:
                logger.warning(f"Rate limit hit, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)

        self.request_times.append(now)

    async def _make_request(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to ESPN API with retries.

        Args:
            url: Request URL
            params: Query parameters

        Returns:
            Response data

        Raises:
            ESPNProviderError: On request failure
        """
        if not AIOHTTP_AVAILABLE and not HTTPX_AVAILABLE:
            raise ESPNProviderError("No HTTP client available (aiohttp or httpx required)")

        headers = {
            "User-Agent": "Ultimate Fantasy Platform/1.0",
            "Accept": "application/json",
        }

        for attempt in range(self.max_retries):
            try:
                if AIOHTTP_AVAILABLE:
                    return await self._make_aiohttp_request(url, params, headers)
                elif HTTPX_AVAILABLE:
                    return await self._make_httpx_request(url, params, headers)

            except aiohttp.ClientError if AIOHTTP_AVAILABLE else Exception as e:
                if attempt == self.max_retries - 1:
                    raise ESPNProviderError(f"Request failed after {self.max_retries} attempts: {e}")

                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)

        raise ESPNProviderError("Request failed after all retries")

    async def _make_aiohttp_request(
        self,
        url: str,
        params: Optional[Dict[str, str]],
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Make request using aiohttp."""
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif response.status == 404:
                    return {}

                response.raise_for_status()
                return await response.json()

    async def _make_httpx_request(
        self,
        url: str,
        params: Optional[Dict[str, str]],
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Make request using httpx."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            elif response.status_code == 404:
                return {}

            response.raise_for_status()
            return response.json()

    async def _get_team_roster(
        self,
        sport_path: str,
        team: str,
        position: Optional[str],
        active_only: bool
    ) -> List[Dict[str, Any]]:
        """Get roster for specific team."""
        url = f"{self.base_url}/{sport_path}/teams/{team}/roster"

        try:
            data = await self._make_request(url)

            if not data or "athletes" not in data:
                return []

            players = []
            for athlete_data in data["athletes"]:
                athlete = athlete_data.get("athlete", {})
                player = self._normalize_player_data(athlete, team)

                # Apply filters
                if position and player.get("position") != position:
                    continue
                if active_only and not player.get("active", True):
                    continue

                players.append(player)

            return players

        except Exception as e:
            logger.warning(f"Failed to get roster for team {team}: {e}")
            return []

    async def _get_all_players(
        self,
        sport_path: str,
        position: Optional[str],
        active_only: bool
    ) -> List[Dict[str, Any]]:
        """Get all players by fetching all team rosters."""
        # First get all teams
        teams = await self.get_teams(sport_path.split('/')[1])

        all_players = []

        # Fetch roster for each team
        for team in teams:
            team_id = team.get("abbreviation") or team.get("team_id")
            if team_id:
                roster = await self._get_team_roster(sport_path, team_id, position, active_only)
                all_players.extend(roster)

                # Small delay to avoid overwhelming API
                await asyncio.sleep(0.1)

        return all_players

    async def _get_player_injury_status(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Get injury status for specific player."""
        try:
            url = f"{self.base_url}/athletes/{player_id}"
            data = await self._make_request(url)

            if not data or "athlete" not in data:
                return None

            athlete = data["athlete"]
            injury_status = athlete.get("injury", {})

            if not injury_status:
                return None

            return {
                "player_id": player_id,
                "player_name": athlete.get("displayName", ""),
                "injury_status": injury_status.get("status", "healthy").lower(),
                "injury_description": injury_status.get("details"),
                "expected_return": None,  # ESPN doesn't provide return dates
                "last_updated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.warning(f"Failed to get injury status for player {player_id}: {e}")
            return None

    async def _get_team_injury_report(self, team: str) -> List[Dict[str, Any]]:
        """Get injury report for team."""
        # ESPN doesn't have a dedicated injury report endpoint
        # Would need to check each player individually
        logger.debug(f"Team injury reports not directly available from ESPN for {team}")
        return []

    def _normalize_player_data(self, athlete: Dict[str, Any], team_id: str = "") -> Dict[str, Any]:
        """Normalize ESPN athlete data to standard format."""
        position_data = athlete.get("position", {})

        return {
            "player_id": str(athlete.get("id", "")),
            "external_id": str(athlete.get("id", "")),
            "name": athlete.get("displayName", ""),
            "position": position_data.get("abbreviation", ""),
            "team_id": team_id or athlete.get("team", {}).get("abbreviation", ""),
            "sport": self._extract_sport_from_athlete(athlete),
            "status": "active",  # ESPN doesn't clearly indicate inactive status
            "injury_status": self._extract_injury_status(athlete),
            "jersey_number": athlete.get("jersey", ""),
            "height": athlete.get("height"),
            "weight": athlete.get("weight"),
            "age": athlete.get("age"),
            "experience": athlete.get("experience", {}).get("years"),
        }

    def _normalize_team_data(self, team: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize ESPN team data to standard format."""
        return {
            "team_id": team.get("abbreviation", ""),
            "name": team.get("displayName", ""),
            "city": team.get("location", ""),
            "abbreviation": team.get("abbreviation", ""),
            "conference": team.get("groups", {}).get("parent", {}).get("name"),
            "division": team.get("groups", {}).get("name"),
            "logo_url": team.get("logos", [{}])[0].get("href") if team.get("logos") else None,
            "colors": [color.get("hex") for color in team.get("colors", []) if color.get("hex")],
        }

    def _normalize_game_data(self, event: Dict[str, Any], include_scores: bool = False) -> Dict[str, Any]:
        """Normalize ESPN event data to standard game format."""
        competition = event.get("competitions", [{}])[0]
        competitors = competition.get("competitors", [])

        # Find home and away teams
        home_team = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away_team = next((c for c in competitors if c.get("homeAway") == "away"), {})

        status = event.get("status", {})

        game_data = {
            "game_id": str(event.get("id", "")),
            "sport": self._extract_sport_from_event(event),
            "home_team": home_team.get("team", {}).get("abbreviation", ""),
            "away_team": away_team.get("team", {}).get("abbreviation", ""),
            "scheduled_at": event.get("date", ""),
            "status": self._normalize_game_status(status.get("type", {}).get("name", "")),
            "week": competition.get("week", {}).get("number"),
            "season": event.get("season", {}).get("year"),
        }

        if include_scores:
            game_data.update({
                "home_score": int(home_team.get("score", 0)),
                "away_score": int(away_team.get("score", 0)),
                "period": status.get("period"),
                "time_remaining": status.get("displayClock"),
                "is_final": status.get("type", {}).get("completed", False),
            })

        return game_data

    def _normalize_player_stats(
        self,
        stats: Dict[str, Any],
        player_id: str,
        season: str,
        week: Optional[int]
    ) -> Dict[str, Any]:
        """Normalize ESPN player statistics."""
        return {
            "player_id": player_id,
            "external_id": player_id,
            "season": season,
            "week": week,
            "games_played": stats.get("gamesPlayed", 0),
            "stats": self._extract_relevant_stats(stats),
            "fantasy_points": self._calculate_fantasy_points(stats),
            "updated_at": datetime.utcnow().isoformat(),
        }

    def _extract_sport_from_athlete(self, athlete: Dict[str, Any]) -> str:
        """Extract sport from athlete data."""
        # ESPN athlete data doesn't always include sport directly
        return "nfl"  # Default, would need sport context

    def _extract_sport_from_event(self, event: Dict[str, Any]) -> str:
        """Extract sport from event data."""
        # ESPN event data includes league info
        league = event.get("league", {})
        abbreviation = league.get("abbreviation", "").lower()

        sport_mapping = {
            "nfl": "nfl",
            "mlb": "mlb",
            "wnba": "wnba",
            "nba": "nba",
        }

        return sport_mapping.get(abbreviation, "nfl")

    def _extract_injury_status(self, athlete: Dict[str, Any]) -> str:
        """Extract injury status from athlete data."""
        injury = athlete.get("injury", {})
        if not injury:
            return "healthy"

        status = injury.get("status", "").lower()

        # Map ESPN injury statuses to our format
        status_mapping = {
            "out": "out",
            "questionable": "questionable",
            "doubtful": "doubtful",
            "probable": "questionable",  # Map probable to questionable
            "": "healthy",
        }

        return status_mapping.get(status, "healthy")

    def _normalize_game_status(self, espn_status: str) -> str:
        """Normalize ESPN game status."""
        status_mapping = {
            "STATUS_SCHEDULED": "scheduled",
            "STATUS_IN_PROGRESS": "in_progress",
            "STATUS_FINAL": "final",
            "STATUS_POSTPONED": "postponed",
            "STATUS_CANCELED": "cancelled",
            "STATUS_SUSPENDED": "suspended",
        }

        return status_mapping.get(espn_status, "scheduled")

    def _game_involves_team(self, game: Dict[str, Any], team: str) -> bool:
        """Check if game involves specific team."""
        return game.get("home_team") == team or game.get("away_team") == team

    def _extract_relevant_stats(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant fantasy statistics."""
        # This would map ESPN stat names to our standard names
        # ESPN stats structure varies by sport
        return {
            "passing_yards": stats.get("passingYards", 0),
            "passing_tds": stats.get("passingTouchdowns", 0),
            "interceptions": stats.get("interceptions", 0),
            "rushing_yards": stats.get("rushingYards", 0),
            "rushing_tds": stats.get("rushingTouchdowns", 0),
            "receiving_yards": stats.get("receivingYards", 0),
            "receiving_tds": stats.get("receivingTouchdowns", 0),
            "receptions": stats.get("receptions", 0),
        }

    def _calculate_fantasy_points(self, stats: Dict[str, Any]) -> float:
        """Calculate fantasy points from stats (simplified scoring)."""
        points = 0.0

        # Standard fantasy scoring
        points += stats.get("passingYards", 0) * 0.04  # 1 pt per 25 yards
        points += stats.get("passingTouchdowns", 0) * 4
        points -= stats.get("interceptions", 0) * 2

        points += stats.get("rushingYards", 0) * 0.1  # 1 pt per 10 yards
        points += stats.get("rushingTouchdowns", 0) * 6

        points += stats.get("receivingYards", 0) * 0.1
        points += stats.get("receivingTouchdowns", 0) * 6
        points += stats.get("receptions", 0) * 1  # PPR

        return round(points, 2)


# Factory function
def create_espn_provider(**kwargs) -> ESPNAPIProvider:
    """Create ESPN API provider instance."""
    return ESPNAPIProvider(**kwargs)