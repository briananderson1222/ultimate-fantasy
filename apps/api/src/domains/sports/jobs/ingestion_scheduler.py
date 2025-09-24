"""
Sports data ingestion scheduler for automated data collection and updates.

Provides comprehensive job scheduling for:
- Player data synchronization
- Team roster updates
- Game schedule ingestion
- Live score collection
- Injury report updates
- Statistics synchronization
- Provider fallback and rotation
- Error handling and retry logic
- Performance monitoring
"""

import asyncio
from datetime import datetime, timedelta, time
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    schedule = None
    SCHEDULE_AVAILABLE = False

from sqlalchemy.orm import Session

from domains.shared.enums import DataProvider, SportType
from domains.sports.models.player import Player
from domains.sports.providers.espn_provider import ESPNAPIProvider
from domains.sports.services.data_normalizer import get_data_normalizer
from domains.sports.services.sports_data_service import get_sports_data_service

try:
    from infrastructure.database.session_factory import get_session_factory
except ImportError:
    get_session_factory = None  # type: ignore[misc,assignment]

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging
    get_logger = logging.getLogger  # type: ignore[assignment]

try:
    from infrastructure.cache.redis_pool import get_redis_pool
except ImportError:
    get_redis_pool = None  # type: ignore[misc,assignment]

logger = get_logger(__name__)


class IngestionJobError(Exception):
    """Ingestion job errors."""
    pass


class IngestionJob:
    """Individual ingestion job definition."""

    def __init__(
        self,
        job_id: str,
        name: str,
        sport: str,
        job_type: str,
        schedule_expression: str,
        enabled: bool = True,
        max_retries: int = 3,
        timeout_minutes: int = 30,
        providers: Optional[List[str]] = None,
    ):
        self.job_id = job_id
        self.name = name
        self.sport = sport
        self.job_type = job_type
        self.schedule_expression = schedule_expression
        self.enabled = enabled
        self.max_retries = max_retries
        self.timeout_minutes = timeout_minutes
        self.providers = providers or ["espn", "mock"]

        # Runtime state
        self.last_run: Optional[datetime] = None
        self.last_success: Optional[datetime] = None
        self.consecutive_failures = 0
        self.total_runs = 0
        self.total_successes = 0


class IngestionScheduler:
    """Scheduler for sports data ingestion jobs."""

    def __init__(self, session: Optional[Session] = None):
        self.session = session
        self.jobs: Dict[str, IngestionJob] = {}
        self.running_jobs: Set[str] = set()
        self.shutdown_requested = False

        # Services
        self.normalizer = get_data_normalizer()
        self.providers = {
            "espn": ESPNAPIProvider(),
        }

        # Default job configurations
        self._setup_default_jobs()

    def _setup_default_jobs(self):
        """Setup default ingestion jobs for all sports."""

        # NFL Jobs
        self.register_job(IngestionJob(
            job_id="nfl_players_sync",
            name="NFL Players Synchronization",
            sport="nfl",
            job_type="players_sync",
            schedule_expression="daily_06:00",  # 6 AM daily
            timeout_minutes=60,
        ))

        self.register_job(IngestionJob(
            job_id="nfl_scores_live",
            name="NFL Live Scores",
            sport="nfl",
            job_type="scores_live",
            schedule_expression="every_5_minutes",  # During game days
            timeout_minutes=10,
        ))

        self.register_job(IngestionJob(
            job_id="nfl_schedule_sync",
            name="NFL Schedule Sync",
            sport="nfl",
            job_type="schedule_sync",
            schedule_expression="daily_03:00",  # 3 AM daily
            timeout_minutes=30,
        ))

        self.register_job(IngestionJob(
            job_id="nfl_injury_reports",
            name="NFL Injury Reports",
            sport="nfl",
            job_type="injury_reports",
            schedule_expression="every_30_minutes",  # Frequent updates during season
            timeout_minutes=15,
        ))

        # MLB Jobs
        self.register_job(IngestionJob(
            job_id="mlb_players_sync",
            name="MLB Players Synchronization",
            sport="mlb",
            job_type="players_sync",
            schedule_expression="daily_05:00",
            timeout_minutes=60,
        ))

        self.register_job(IngestionJob(
            job_id="mlb_scores_live",
            name="MLB Live Scores",
            sport="mlb",
            job_type="scores_live",
            schedule_expression="every_10_minutes",
            timeout_minutes=10,
        ))

        # WNBA Jobs
        self.register_job(IngestionJob(
            job_id="wnba_players_sync",
            name="WNBA Players Synchronization",
            sport="wnba",
            job_type="players_sync",
            schedule_expression="daily_07:00",
            timeout_minutes=30,
        ))

        self.register_job(IngestionJob(
            job_id="wnba_scores_live",
            name="WNBA Live Scores",
            sport="wnba",
            job_type="scores_live",
            schedule_expression="every_15_minutes",
            timeout_minutes=10,
        ))

    def register_job(self, job: IngestionJob) -> None:
        """Register a new ingestion job."""
        self.jobs[job.job_id] = job
        logger.info(f"Registered ingestion job: {job.name} ({job.job_id})")

    def unregister_job(self, job_id: str) -> bool:
        """Unregister an ingestion job."""
        if job_id in self.jobs:
            del self.jobs[job_id]
            logger.info(f"Unregistered ingestion job: {job_id}")
            return True
        return False

    def enable_job(self, job_id: str) -> bool:
        """Enable a job."""
        if job_id in self.jobs:
            self.jobs[job_id].enabled = True
            logger.info(f"Enabled job: {job_id}")
            return True
        return False

    def disable_job(self, job_id: str) -> bool:
        """Disable a job."""
        if job_id in self.jobs:
            self.jobs[job_id].enabled = False
            logger.info(f"Disabled job: {job_id}")
            return True
        return False

    async def start_scheduler(self) -> None:
        """Start the ingestion scheduler."""
        logger.info("Starting sports data ingestion scheduler")

        if not SCHEDULE_AVAILABLE:
            logger.warning("Schedule library not available, using simple timer-based scheduling")
            await self._start_simple_scheduler()
        else:
            await self._start_advanced_scheduler()

    async def _start_simple_scheduler(self) -> None:
        """Simple timer-based scheduler when advanced scheduling is unavailable."""
        while not self.shutdown_requested:
            current_time = datetime.utcnow()

            for job in self.jobs.values():
                if not job.enabled:
                    continue

                if self._should_run_job(job, current_time):
                    if job.job_id not in self.running_jobs:
                        asyncio.create_task(self._execute_job(job))

            # Check every minute
            await asyncio.sleep(60)

    async def _start_advanced_scheduler(self) -> None:
        """Advanced scheduler using the schedule library."""
        # Setup scheduled jobs
        for job in self.jobs.values():
            if not job.enabled:
                continue

            self._schedule_job(job)

        # Run scheduler loop
        while not self.shutdown_requested:
            schedule.run_pending()
            await asyncio.sleep(60)

    def _schedule_job(self, job: IngestionJob) -> None:
        """Schedule a job using the schedule library."""
        if not SCHEDULE_AVAILABLE:
            return

        def job_wrapper():
            if job.job_id not in self.running_jobs:
                asyncio.create_task(self._execute_job(job))

        # Parse schedule expression
        if job.schedule_expression.startswith("daily_"):
            time_str = job.schedule_expression.split("_")[1]
            schedule.every().day.at(time_str).do(job_wrapper)
        elif job.schedule_expression.startswith("every_"):
            interval_str = job.schedule_expression.split("_")[1]
            if "minutes" in interval_str:
                minutes = int(interval_str.replace("minutes", ""))
                schedule.every(minutes).minutes.do(job_wrapper)
            elif "hours" in interval_str:
                hours = int(interval_str.replace("hours", ""))
                schedule.every(hours).hours.do(job_wrapper)
        else:
            logger.warning(f"Unknown schedule expression: {job.schedule_expression}")

    def _should_run_job(self, job: IngestionJob, current_time: datetime) -> bool:
        """Determine if a job should run based on its schedule."""
        if not job.last_run:
            return True

        # Simple scheduling logic
        if job.schedule_expression.startswith("daily_"):
            # Run once per day at specified time
            time_str = job.schedule_expression.split("_")[1]
            target_time = datetime.strptime(time_str, "%H:%M").time()

            last_run_date = job.last_run.date()
            current_date = current_time.date()
            current_time_only = current_time.time()

            return (current_date > last_run_date and current_time_only >= target_time)

        elif job.schedule_expression.startswith("every_"):
            interval_str = job.schedule_expression.split("_")[1]

            if "minutes" in interval_str:
                minutes = int(interval_str.replace("minutes", ""))
                return current_time >= job.last_run + timedelta(minutes=minutes)
            elif "hours" in interval_str:
                hours = int(interval_str.replace("hours", ""))
                return current_time >= job.last_run + timedelta(hours=hours)

        return False

    async def _execute_job(self, job: IngestionJob) -> None:
        """Execute a single ingestion job."""
        if job.job_id in self.running_jobs:
            logger.warning(f"Job {job.job_id} is already running, skipping")
            return

        self.running_jobs.add(job.job_id)
        job.last_run = datetime.utcnow()
        job.total_runs += 1

        logger.info(f"Executing job: {job.name} ({job.job_id})")

        try:
            # Execute job with timeout
            await asyncio.wait_for(
                self._run_job_logic(job),
                timeout=job.timeout_minutes * 60
            )

            # Mark success
            job.last_success = datetime.utcnow()
            job.total_successes += 1
            job.consecutive_failures = 0

            logger.info(f"Job completed successfully: {job.name}")

        except asyncio.TimeoutError:
            logger.error(f"Job timed out: {job.name}")
            job.consecutive_failures += 1

        except Exception as e:
            logger.error(f"Job failed: {job.name} - {e}")
            job.consecutive_failures += 1

            # Disable job if too many consecutive failures
            if job.consecutive_failures >= job.max_retries:
                job.enabled = False
                logger.error(f"Disabled job due to consecutive failures: {job.name}")

        finally:
            self.running_jobs.discard(job.job_id)

    async def _run_job_logic(self, job: IngestionJob) -> None:
        """Execute the actual job logic based on job type."""
        if job.job_type == "players_sync":
            await self._sync_players(job)
        elif job.job_type == "scores_live":
            await self._update_live_scores(job)
        elif job.job_type == "schedule_sync":
            await self._sync_schedule(job)
        elif job.job_type == "injury_reports":
            await self._update_injury_reports(job)
        elif job.job_type == "team_rosters":
            await self._sync_team_rosters(job)
        else:
            raise IngestionJobError(f"Unknown job type: {job.job_type}")

    async def _sync_players(self, job: IngestionJob) -> None:
        """Synchronize player data."""
        logger.info(f"Syncing players for {job.sport}")

        # Get sports data service
        sports_service = await get_sports_data_service()

        # Fetch player data from providers
        players_data = await sports_service.get_players(
            sport=job.sport.upper(),
            active_only=True,
            use_cache=False  # Force fresh data
        )

        logger.info(f"Retrieved {len(players_data)} players for {job.sport}")

        # Normalize and store player data
        session_factory = get_session_factory()
        if session_factory:
            with session_factory.get_sync_session() as session:
                for player_data in players_data:
                    await self._upsert_player(session, player_data, job.sport)
                session.commit()

        logger.info(f"Player sync completed for {job.sport}")

    async def _update_live_scores(self, job: IngestionJob) -> None:
        """Update live game scores."""
        logger.info(f"Updating live scores for {job.sport}")

        # Get sports data service
        sports_service = await get_sports_data_service()

        # Fetch live scores
        scores_data = await sports_service.get_schedule(
            season="2024",  # Current season
            use_cache=False
        )

        # Filter for live/recent games
        live_games = [
            game for game in scores_data
            if game.get("status") in ["in_progress", "final"]
        ]

        logger.info(f"Found {len(live_games)} live/recent games for {job.sport}")

        # Process score updates
        for game in live_games:
            await self._process_game_scores(game, job.sport)

        logger.info(f"Live scores update completed for {job.sport}")

    async def _sync_schedule(self, job: IngestionJob) -> None:
        """Synchronize game schedule."""
        logger.info(f"Syncing schedule for {job.sport}")

        # Get sports data service
        sports_service = await get_sports_data_service()

        # Fetch schedule data
        schedule_data = await sports_service.get_schedule(
            season="2024",
            use_cache=False
        )

        logger.info(f"Retrieved {len(schedule_data)} games for {job.sport}")

        # Store schedule data
        # This would involve updating game records in the database
        # Implementation would depend on the specific game model

        logger.info(f"Schedule sync completed for {job.sport}")

    async def _update_injury_reports(self, job: IngestionJob) -> None:
        """Update injury reports."""
        logger.info(f"Updating injury reports for {job.sport}")

        # Get sports data service
        sports_service = await get_sports_data_service()

        # Fetch injury reports
        injury_reports = await sports_service.get_injury_report(use_cache=False)

        logger.info(f"Retrieved {len(injury_reports)} injury reports for {job.sport}")

        # Update player injury statuses
        session_factory = get_session_factory()
        if session_factory:
            with session_factory.get_sync_session() as session:
                for injury_report in injury_reports:
                    await self._update_player_injury_status(session, injury_report)
                session.commit()

        logger.info(f"Injury reports update completed for {job.sport}")

    async def _sync_team_rosters(self, job: IngestionJob) -> None:
        """Synchronize team rosters."""
        logger.info(f"Syncing team rosters for {job.sport}")

        # Get sports data service
        sports_service = await get_sports_data_service()

        # Fetch teams first
        teams_data = await sports_service.get_teams(sport=job.sport.upper())

        # For each team, fetch roster
        for team in teams_data:
            team_players = await sports_service.get_players(
                sport=job.sport.upper(),
                team=team.get("team_id"),
                use_cache=False
            )

            logger.info(f"Retrieved {len(team_players)} players for team {team.get('name')}")

            # Update team roster
            # This would involve updating team roster relationships
            # Implementation depends on the specific team model

        logger.info(f"Team rosters sync completed for {job.sport}")

    async def _upsert_player(self, session: Session, player_data: Dict[str, Any], sport: str) -> None:
        """Insert or update player record."""
        try:
            # Normalize the player data
            normalized_data = self.normalizer.normalize_player_data(
                player_data, "espn", sport
            )

            # Find existing player by external_id
            existing_player = session.query(Player).filter(
                Player.external_id == normalized_data["external_id"],
                Player.sport == sport.lower()
            ).first()

            if existing_player:
                # Update existing player
                for key, value in normalized_data.items():
                    if hasattr(existing_player, key):
                        setattr(existing_player, key, value)
                existing_player.updated_at = datetime.utcnow()
            else:
                # Create new player
                new_player = Player(**normalized_data)
                session.add(new_player)

        except Exception as e:
            logger.error(f"Failed to upsert player: {e}")

    async def _process_game_scores(self, game_data: Dict[str, Any], sport: str) -> None:
        """Process and store game score data."""
        try:
            # Normalize game data
            normalized_game = self.normalizer.normalize_game_data(
                game_data, "espn", sport
            )

            # Here you would update the game record in the database
            # and potentially trigger score update events
            logger.debug(f"Processed game score: {normalized_game.get('game_id')}")

        except Exception as e:
            logger.error(f"Failed to process game scores: {e}")

    async def _update_player_injury_status(
        self, session: Session, injury_report: Dict[str, Any]
    ) -> None:
        """Update player injury status from injury report."""
        try:
            player_id = injury_report.get("player_id")
            if not player_id:
                return

            player = session.query(Player).filter(
                Player.external_id == player_id
            ).first()

            if player:
                player.injury_status = injury_report.get("injury_status", "healthy")
                player.injury_description = injury_report.get("injury_description")
                player.updated_at = datetime.utcnow()

        except Exception as e:
            logger.error(f"Failed to update player injury status: {e}")

    async def stop_scheduler(self) -> None:
        """Stop the ingestion scheduler."""
        logger.info("Stopping sports data ingestion scheduler")
        self.shutdown_requested = True

        # Wait for running jobs to complete
        while self.running_jobs:
            logger.info(f"Waiting for {len(self.running_jobs)} jobs to complete")
            await asyncio.sleep(5)

        logger.info("Sports data ingestion scheduler stopped")

    def get_job_status(self, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Get status of jobs."""
        if job_id:
            if job_id in self.jobs:
                job = self.jobs[job_id]
                return {
                    "job_id": job.job_id,
                    "name": job.name,
                    "enabled": job.enabled,
                    "last_run": job.last_run.isoformat() if job.last_run else None,
                    "last_success": job.last_success.isoformat() if job.last_success else None,
                    "consecutive_failures": job.consecutive_failures,
                    "total_runs": job.total_runs,
                    "total_successes": job.total_successes,
                    "success_rate": job.total_successes / job.total_runs if job.total_runs > 0 else 0,
                    "currently_running": job.job_id in self.running_jobs,
                }
            else:
                return {"error": f"Job {job_id} not found"}
        else:
            # Return status for all jobs
            return {
                "total_jobs": len(self.jobs),
                "enabled_jobs": len([j for j in self.jobs.values() if j.enabled]),
                "running_jobs": len(self.running_jobs),
                "jobs": {
                    job_id: self.get_job_status(job_id)
                    for job_id in self.jobs.keys()
                }
            }

    async def trigger_job(self, job_id: str) -> bool:
        """Manually trigger a job execution."""
        if job_id not in self.jobs:
            return False

        job = self.jobs[job_id]
        if job.job_id in self.running_jobs:
            logger.warning(f"Job {job_id} is already running")
            return False

        # Execute job asynchronously
        asyncio.create_task(self._execute_job(job))
        return True


# Global scheduler instance
_ingestion_scheduler: Optional[IngestionScheduler] = None


def get_ingestion_scheduler(session: Optional[Session] = None) -> IngestionScheduler:
    """Get the global ingestion scheduler instance."""
    global _ingestion_scheduler
    if _ingestion_scheduler is None:
        _ingestion_scheduler = IngestionScheduler(session)
    return _ingestion_scheduler


def reset_ingestion_scheduler():
    """Reset the global scheduler (useful for testing)."""
    global _ingestion_scheduler
    _ingestion_scheduler = None