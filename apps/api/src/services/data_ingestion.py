"""
Sports Data Ingestion Scheduler for Ultimate Fantasy Platform
Handles scheduled jobs for player stats updates, external API polling, and data synchronization
"""

import asyncio
import logging
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Set, Any, Callable
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict

import redis.asyncio as redis
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..infrastructure.database.session_factory import get_db_session
from .sports_data_service import SportsDataService, DataProvider
from .event_publisher import EventPublisher, EventType
from ..models.player import Player, SportType
from ..models.league import League, LeagueStatus
from ..models.score import Score
from ..domains.shared.exceptions import (
    ProviderError, ValidationError, RateLimitExceededError
)


logger = logging.getLogger(__name__)


class IngestionJobType(Enum):
    """Types of data ingestion jobs"""
    PLAYER_STATS_UPDATE = "player_stats_update"
    INJURY_STATUS_UPDATE = "injury_status_update"
    ROSTER_UPDATES = "roster_updates"
    GAME_SCHEDULE_SYNC = "game_schedule_sync"
    LIVE_SCORES_UPDATE = "live_scores_update"
    SEASON_STATS_SYNC = "season_stats_sync"
    PLAYER_NEWS_UPDATE = "player_news_update"
    TEAM_STANDINGS_UPDATE = "team_standings_update"


class JobPriority(Enum):
    """Job priority levels"""
    CRITICAL = 1  # Live games, draft-time updates
    HIGH = 2      # Daily stats, injury updates
    MEDIUM = 3    # Weekly aggregations
    LOW = 4       # Historical data, cleanup


@dataclass
class IngestionJob:
    """Data ingestion job definition"""
    job_id: str
    job_type: IngestionJobType
    sport: SportType
    priority: JobPriority
    schedule_cron: str  # Cron expression for scheduling
    timeout_seconds: int
    retry_count: int
    retry_delay_seconds: int
    enabled: bool
    metadata: Dict[str, Any]

    # Runtime fields
    last_run: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    next_run: Optional[datetime] = None


class DataIngestionScheduler:
    """Main scheduler for sports data ingestion"""

    def __init__(
        self,
        sports_data_service: SportsDataService,
        event_publisher: EventPublisher,
        redis_client: Optional[redis.Redis] = None
    ):
        """Initialize data ingestion scheduler"""
        self.sports_data_service = sports_data_service
        self.event_publisher = event_publisher
        self.redis_client = redis_client

        # Job management
        self.jobs: Dict[str, IngestionJob] = {}
        self.running_jobs: Dict[str, asyncio.Task] = {}
        self.job_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()

        # Scheduler control
        self.scheduler_task: Optional[asyncio.Task] = None
        self.worker_tasks: List[asyncio.Task] = []
        self.is_running = False
        self.max_workers = 5

        # Statistics
        self.jobs_completed = 0
        self.jobs_failed = 0
        self.total_records_processed = 0

        # Rate limiting
        self.provider_rate_limits: Dict[DataProvider, Dict[str, Any]] = defaultdict(dict)
        self.last_api_calls: Dict[DataProvider, List[datetime]] = defaultdict(list)

    async def start(self):
        """Start the data ingestion scheduler"""
        if self.is_running:
            logger.warning("Data ingestion scheduler already running")
            return

        logger.info("Starting data ingestion scheduler")
        self.is_running = True

        # Register default jobs
        self._register_default_jobs()

        # Start scheduler and worker tasks
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        self.worker_tasks = [
            asyncio.create_task(self._worker_loop(i))
            for i in range(self.max_workers)
        ]

        # Load job states from Redis if available
        if self.redis_client:
            await self._load_job_states()

    async def stop(self):
        """Stop the data ingestion scheduler"""
        if not self.is_running:
            return

        logger.info("Stopping data ingestion scheduler")
        self.is_running = False

        # Cancel scheduler task
        if self.scheduler_task:
            self.scheduler_task.cancel()

        # Cancel worker tasks
        for task in self.worker_tasks:
            task.cancel()

        # Cancel running jobs
        for job_id, task in self.running_jobs.items():
            logger.info(f"Cancelling running job: {job_id}")
            task.cancel()

        # Save job states to Redis
        if self.redis_client:
            await self._save_job_states()

    def register_job(self, job: IngestionJob):
        """Register a new ingestion job"""
        self.jobs[job.job_id] = job
        self._schedule_next_run(job)
        logger.info(f"Registered ingestion job: {job.job_id} ({job.job_type.value})")

    def enable_job(self, job_id: str, enabled: bool = True):
        """Enable or disable a job"""
        if job_id in self.jobs:
            self.jobs[job_id].enabled = enabled
            if enabled:
                self._schedule_next_run(self.jobs[job_id])
            logger.info(f"Job {job_id} {'enabled' if enabled else 'disabled'}")

    async def trigger_job(self, job_id: str, force: bool = False) -> bool:
        """Manually trigger a job execution"""
        job = self.jobs.get(job_id)
        if not job:
            logger.error(f"Job not found: {job_id}")
            return False

        if not force and job_id in self.running_jobs:
            logger.warning(f"Job already running: {job_id}")
            return False

        # Add to queue with high priority
        await self.job_queue.put((1, datetime.utcnow(), job))
        logger.info(f"Manually triggered job: {job_id}")
        return True

    async def get_job_status(self, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Get status of jobs"""
        if job_id:
            job = self.jobs.get(job_id)
            if not job:
                return {"error": "Job not found"}

            return {
                "job_id": job.job_id,
                "job_type": job.job_type.value,
                "sport": job.sport.value,
                "enabled": job.enabled,
                "last_run": job.last_run.isoformat() if job.last_run else None,
                "last_success": job.last_success.isoformat() if job.last_success else None,
                "last_error": job.last_error,
                "consecutive_failures": job.consecutive_failures,
                "next_run": job.next_run.isoformat() if job.next_run else None,
                "is_running": job_id in self.running_jobs
            }

        # Return all jobs status
        return {
            "scheduler_running": self.is_running,
            "jobs_completed": self.jobs_completed,
            "jobs_failed": self.jobs_failed,
            "records_processed": self.total_records_processed,
            "active_jobs": len(self.running_jobs),
            "queued_jobs": self.job_queue.qsize(),
            "jobs": [
                {
                    "job_id": job.job_id,
                    "job_type": job.job_type.value,
                    "sport": job.sport.value,
                    "enabled": job.enabled,
                    "last_run": job.last_run.isoformat() if job.last_run else None,
                    "next_run": job.next_run.isoformat() if job.next_run else None,
                    "consecutive_failures": job.consecutive_failures,
                    "is_running": job.job_id in self.running_jobs
                }
                for job in self.jobs.values()
            ]
        }

    # Private methods

    def _register_default_jobs(self):
        """Register default data ingestion jobs"""

        # Live scores during game times (every 2 minutes)
        self.register_job(IngestionJob(
            job_id="live_scores_mlb",
            job_type=IngestionJobType.LIVE_SCORES_UPDATE,
            sport=SportType.MLB,
            priority=JobPriority.CRITICAL,
            schedule_cron="*/2 * * * *",  # Every 2 minutes
            timeout_seconds=30,
            retry_count=3,
            retry_delay_seconds=10,
            enabled=True,
            metadata={"during_games_only": True}
        ))

        self.register_job(IngestionJob(
            job_id="live_scores_nfl",
            job_type=IngestionJobType.LIVE_SCORES_UPDATE,
            sport=SportType.NFL,
            priority=JobPriority.CRITICAL,
            schedule_cron="*/1 * * * *",  # Every minute during games
            timeout_seconds=30,
            retry_count=3,
            retry_delay_seconds=10,
            enabled=True,
            metadata={"during_games_only": True}
        ))

        # Daily player stats updates (every 15 minutes)
        for sport in [SportType.MLB, SportType.NFL, SportType.NBA]:
            self.register_job(IngestionJob(
                job_id=f"player_stats_{sport.value}",
                job_type=IngestionJobType.PLAYER_STATS_UPDATE,
                sport=sport,
                priority=JobPriority.HIGH,
                schedule_cron="*/15 * * * *",  # Every 15 minutes
                timeout_seconds=300,
                retry_count=2,
                retry_delay_seconds=60,
                enabled=True,
                metadata={}
            ))

        # Injury status updates (every 30 minutes)
        for sport in [SportType.MLB, SportType.NFL, SportType.NBA]:
            self.register_job(IngestionJob(
                job_id=f"injury_updates_{sport.value}",
                job_type=IngestionJobType.INJURY_STATUS_UPDATE,
                sport=sport,
                priority=JobPriority.HIGH,
                schedule_cron="*/30 * * * *",  # Every 30 minutes
                timeout_seconds=120,
                retry_count=2,
                retry_delay_seconds=60,
                enabled=True,
                metadata={}
            ))

        # Game schedule sync (daily at 6 AM)
        for sport in [SportType.MLB, SportType.NFL, SportType.NBA]:
            self.register_job(IngestionJob(
                job_id=f"schedule_sync_{sport.value}",
                job_type=IngestionJobType.GAME_SCHEDULE_SYNC,
                sport=sport,
                priority=JobPriority.MEDIUM,
                schedule_cron="0 6 * * *",  # Daily at 6 AM
                timeout_seconds=600,
                retry_count=1,
                retry_delay_seconds=300,
                enabled=True,
                metadata={}
            ))

        # Season stats sync (daily at 3 AM)
        for sport in [SportType.MLB, SportType.NFL, SportType.NBA]:
            self.register_job(IngestionJob(
                job_id=f"season_stats_{sport.value}",
                job_type=IngestionJobType.SEASON_STATS_SYNC,
                sport=sport,
                priority=JobPriority.MEDIUM,
                schedule_cron="0 3 * * *",  # Daily at 3 AM
                timeout_seconds=1800,
                retry_count=1,
                retry_delay_seconds=600,
                enabled=True,
                metadata={}
            ))

        # Player news updates (every 2 hours)
        for sport in [SportType.MLB, SportType.NFL, SportType.NBA]:
            self.register_job(IngestionJob(
                job_id=f"news_updates_{sport.value}",
                job_type=IngestionJobType.PLAYER_NEWS_UPDATE,
                sport=sport,
                priority=JobPriority.LOW,
                schedule_cron="0 */2 * * *",  # Every 2 hours
                timeout_seconds=300,
                retry_count=1,
                retry_delay_seconds=120,
                enabled=True,
                metadata={}
            ))

    async def _scheduler_loop(self):
        """Main scheduler loop that queues jobs for execution"""
        while self.is_running:
            try:
                now = datetime.utcnow()

                # Check all jobs for scheduling
                for job in self.jobs.values():
                    if not job.enabled:
                        continue

                    if job.next_run and now >= job.next_run:
                        # Add job to queue with priority
                        priority = job.priority.value
                        await self.job_queue.put((priority, now, job))

                        # Schedule next run
                        self._schedule_next_run(job)

                # Sleep for 30 seconds before next check
                await asyncio.sleep(30)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)

    async def _worker_loop(self, worker_id: int):
        """Worker loop that processes jobs from the queue"""
        logger.info(f"Started ingestion worker {worker_id}")

        while self.is_running:
            try:
                # Get job from queue with timeout
                priority, queued_at, job = await asyncio.wait_for(
                    self.job_queue.get(),
                    timeout=5.0
                )

                # Skip if job is already running
                if job.job_id in self.running_jobs:
                    continue

                # Execute job
                task = asyncio.create_task(self._execute_job(job))
                self.running_jobs[job.job_id] = task

                try:
                    await task
                finally:
                    self.running_jobs.pop(job.job_id, None)

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in worker {worker_id}: {e}")

        logger.info(f"Stopped ingestion worker {worker_id}")

    async def _execute_job(self, job: IngestionJob):
        """Execute a single ingestion job"""
        start_time = datetime.utcnow()
        job.last_run = start_time

        logger.info(f"Executing job: {job.job_id} ({job.job_type.value})")

        try:
            # Check rate limits
            if not await self._check_rate_limit(job):
                logger.warning(f"Rate limit exceeded for job: {job.job_id}")
                return

            # Execute based on job type
            records_processed = 0

            if job.job_type == IngestionJobType.LIVE_SCORES_UPDATE:
                records_processed = await self._update_live_scores(job)
            elif job.job_type == IngestionJobType.PLAYER_STATS_UPDATE:
                records_processed = await self._update_player_stats(job)
            elif job.job_type == IngestionJobType.INJURY_STATUS_UPDATE:
                records_processed = await self._update_injury_status(job)
            elif job.job_type == IngestionJobType.GAME_SCHEDULE_SYNC:
                records_processed = await self._sync_game_schedule(job)
            elif job.job_type == IngestionJobType.SEASON_STATS_SYNC:
                records_processed = await self._sync_season_stats(job)
            elif job.job_type == IngestionJobType.PLAYER_NEWS_UPDATE:
                records_processed = await self._update_player_news(job)
            else:
                logger.warning(f"Unknown job type: {job.job_type}")
                return

            # Job completed successfully
            job.last_success = datetime.utcnow()
            job.consecutive_failures = 0
            job.last_error = None

            self.jobs_completed += 1
            self.total_records_processed += records_processed

            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Job completed: {job.job_id} ({records_processed} records, {execution_time:.2f}s)")

            # Publish success event
            await self.event_publisher.publish_event(
                event_type=EventType.SEASON_STARTED,  # Generic system event
                source_service="data_ingestion",
                data={
                    "job_id": job.job_id,
                    "job_type": job.job_type.value,
                    "sport": job.sport.value,
                    "records_processed": records_processed,
                    "execution_time_seconds": execution_time
                }
            )

        except asyncio.TimeoutError:
            error_msg = f"Job timeout after {job.timeout_seconds} seconds"
            await self._handle_job_error(job, error_msg)

        except (ProviderError, ValidationError, RateLimitExceededError) as e:
            await self._handle_job_error(job, str(e))

        except Exception as e:
            await self._handle_job_error(job, f"Unexpected error: {str(e)}")

    async def _update_live_scores(self, job: IngestionJob) -> int:
        """Update live scores for active games"""
        records_processed = 0

        # Check if there are active games for this sport
        if job.metadata.get("during_games_only"):
            active_games = await self.sports_data_service.get_active_games(job.sport)
            if not active_games:
                logger.debug(f"No active games for {job.sport.value}, skipping live scores update")
                return 0

        # Get live scores
        scores_data = await self.sports_data_service.get_live_scores(
            sport=job.sport,
            live_only=True
        )

        with get_db_session() as db:
            for score_data in scores_data:
                # Update player score
                player_id = score_data["player_id"]
                game_date = score_data["game_date"]
                stats = score_data["stats"]
                fantasy_points = score_data["fantasy_points"]

                # Find active leagues using this player
                active_leagues = db.query(League).filter(
                    and_(
                        League.sport == job.sport.value,
                        League.status == LeagueStatus.ACTIVE
                    )
                ).all()

                for league in active_leagues:
                    # Calculate fantasy points for this league's scoring rules
                    league_points = self._calculate_fantasy_points(
                        stats, league.scoring_rules, job.sport
                    )

                    # Update or create score record
                    score = db.query(Score).filter(
                        and_(
                            Score.player_id == player_id,
                            Score.league_id == str(league.league_id),
                            Score.game_day == game_date
                        )
                    ).first()

                    if score:
                        score.stats = stats
                        score.points = league_points
                        score.updated_at = datetime.utcnow()
                    else:
                        score = Score(
                            player_id=player_id,
                            league_id=str(league.league_id),
                            game_day=game_date,
                            stats=stats,
                            points=league_points,
                            is_final=False
                        )
                        db.add(score)

                    records_processed += 1

                    # Publish score update event
                    await self.event_publisher.publish_score_update(
                        league_id=str(league.league_id),
                        player_id=player_id,
                        player_name=score_data.get("player_name", "Unknown"),
                        points=league_points,
                        stats=stats,
                        is_final=score_data.get("is_final", False)
                    )

            db.commit()

        return records_processed

    async def _update_player_stats(self, job: IngestionJob) -> int:
        """Update player statistics"""
        records_processed = 0

        with get_db_session() as db:
            # Get players that need stats updates
            players = db.query(Player).filter(
                and_(
                    Player.sport == job.sport.value,
                    or_(
                        Player.updated_at < datetime.utcnow() - timedelta(hours=6),
                        Player.season_stats.is_(None)
                    )
                )
            ).limit(100).all()  # Limit to avoid overwhelming the API

            for player in players:
                try:
                    # Get updated stats from external API
                    player_data = await self.sports_data_service.get_player_data(
                        external_id=player.external_id,
                        sport=job.sport
                    )

                    if player_data:
                        # Update player stats
                        player.season_stats = player_data.get("season_stats", {})
                        player.game_stats = player_data.get("game_stats", {})
                        player.projections = player_data.get("projections", {})
                        player.updated_at = datetime.utcnow()

                        records_processed += 1

                        # Check for injury status changes
                        new_injury_status = player_data.get("injury_status", "healthy")
                        if player.injury_status != new_injury_status:
                            old_status = player.injury_status
                            player.injury_status = new_injury_status
                            player.injury_description = player_data.get("injury_description")

                            # Publish injury update event
                            await self.event_publisher.publish_event(
                                event_type=EventType.PLAYER_INJURY_UPDATE,
                                source_service="data_ingestion",
                                data={
                                    "player_id": str(player.player_id),
                                    "player_name": player.name,
                                    "old_status": old_status,
                                    "new_status": new_injury_status,
                                    "injury_description": player.injury_description
                                }
                            )

                except Exception as e:
                    logger.error(f"Failed to update player {player.player_id}: {e}")
                    continue

            db.commit()

        return records_processed

    async def _update_injury_status(self, job: IngestionJob) -> int:
        """Update player injury statuses"""
        records_processed = 0

        # Get injury report from external API
        injury_data = await self.sports_data_service.get_injury_report(sport=job.sport)

        with get_db_session() as db:
            for injury_info in injury_data:
                external_id = injury_info["external_id"]

                player = db.query(Player).filter(
                    and_(
                        Player.external_id == external_id,
                        Player.sport == job.sport.value
                    )
                ).first()

                if player:
                    old_status = player.injury_status
                    new_status = injury_info["injury_status"]

                    if old_status != new_status:
                        player.injury_status = new_status
                        player.injury_description = injury_info.get("injury_description")
                        player.updated_at = datetime.utcnow()

                        records_processed += 1

                        # Publish injury update event
                        await self.event_publisher.publish_event(
                            event_type=EventType.PLAYER_INJURY_UPDATE,
                            source_service="data_ingestion",
                            data={
                                "player_id": str(player.player_id),
                                "player_name": player.name,
                                "old_status": old_status,
                                "new_status": new_status,
                                "injury_description": player.injury_description
                            }
                        )

            db.commit()

        return records_processed

    async def _sync_game_schedule(self, job: IngestionJob) -> int:
        """Sync game schedule data"""
        records_processed = 0

        # Get schedule from external API
        schedule_data = await self.sports_data_service.get_schedule(
            sport=job.sport,
            start_date=datetime.utcnow().date(),
            end_date=(datetime.utcnow() + timedelta(days=30)).date()
        )

        # Note: This would typically update a Game/Schedule model
        # For now, we'll just count the records
        records_processed = len(schedule_data)

        logger.info(f"Synced {records_processed} games for {job.sport.value}")
        return records_processed

    async def _sync_season_stats(self, job: IngestionJob) -> int:
        """Sync season statistics"""
        records_processed = 0

        with get_db_session() as db:
            # Get all players for this sport
            players = db.query(Player).filter(
                Player.sport == job.sport.value
            ).all()

            for player in players:
                try:
                    # Get season stats from external API
                    season_stats = await self.sports_data_service.get_player_season_stats(
                        external_id=player.external_id,
                        sport=job.sport,
                        season="2025"
                    )

                    if season_stats:
                        player.season_stats = season_stats
                        player.updated_at = datetime.utcnow()
                        records_processed += 1

                except Exception as e:
                    logger.error(f"Failed to sync season stats for player {player.player_id}: {e}")
                    continue

            db.commit()

        return records_processed

    async def _update_player_news(self, job: IngestionJob) -> int:
        """Update player news and updates"""
        records_processed = 0

        # Get recent news from external API
        news_data = await self.sports_data_service.get_recent_news(
            sport=job.sport,
            days_back=1
        )

        # Note: This would typically create PlayerNews records
        # For now, we'll just count the records
        records_processed = len(news_data)

        logger.info(f"Updated {records_processed} news items for {job.sport.value}")
        return records_processed

    async def _handle_job_error(self, job: IngestionJob, error_message: str):
        """Handle job execution error"""
        job.last_error = error_message
        job.consecutive_failures += 1
        self.jobs_failed += 1

        logger.error(f"Job failed: {job.job_id} - {error_message}")

        # Implement exponential backoff for retries
        if job.consecutive_failures <= job.retry_count:
            delay = job.retry_delay_seconds * (2 ** (job.consecutive_failures - 1))
            job.next_run = datetime.utcnow() + timedelta(seconds=delay)
            logger.info(f"Retrying job {job.job_id} in {delay} seconds")
        else:
            # Disable job after max retries
            job.enabled = False
            logger.error(f"Job {job.job_id} disabled after {job.consecutive_failures} consecutive failures")

    def _schedule_next_run(self, job: IngestionJob):
        """Schedule the next run for a job based on its cron expression"""
        # Simple cron parsing - in production, use a proper cron library
        now = datetime.utcnow()

        # For demonstration, use simple intervals based on common patterns
        if job.schedule_cron == "*/1 * * * *":  # Every minute
            job.next_run = now + timedelta(minutes=1)
        elif job.schedule_cron == "*/2 * * * *":  # Every 2 minutes
            job.next_run = now + timedelta(minutes=2)
        elif job.schedule_cron == "*/15 * * * *":  # Every 15 minutes
            job.next_run = now + timedelta(minutes=15)
        elif job.schedule_cron == "*/30 * * * *":  # Every 30 minutes
            job.next_run = now + timedelta(minutes=30)
        elif job.schedule_cron == "0 */2 * * *":  # Every 2 hours
            job.next_run = now + timedelta(hours=2)
        elif job.schedule_cron == "0 3 * * *":  # Daily at 3 AM
            next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            job.next_run = next_run
        elif job.schedule_cron == "0 6 * * *":  # Daily at 6 AM
            next_run = now.replace(hour=6, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            job.next_run = next_run
        else:
            # Default to hourly
            job.next_run = now + timedelta(hours=1)

        logger.debug(f"Scheduled next run for {job.job_id}: {job.next_run}")

    async def _check_rate_limit(self, job: IngestionJob) -> bool:
        """Check if job execution would exceed rate limits"""
        # Simple rate limiting - allow up to 60 requests per minute per provider
        provider = DataProvider.ESPN  # Default provider
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)

        # Clean old calls
        self.last_api_calls[provider] = [
            call_time for call_time in self.last_api_calls[provider]
            if call_time > minute_ago
        ]

        # Check limit
        if len(self.last_api_calls[provider]) >= 60:
            return False

        # Record this call
        self.last_api_calls[provider].append(now)
        return True

    def _calculate_fantasy_points(
        self,
        stats: Dict[str, Any],
        scoring_rules: Dict[str, float],
        sport: SportType
    ) -> float:
        """Calculate fantasy points based on stats and scoring rules"""
        points = 0.0

        for stat_name, value in stats.items():
            if stat_name in scoring_rules:
                points += value * scoring_rules[stat_name]

        return round(points, 2)

    async def _load_job_states(self):
        """Load job states from Redis"""
        if not self.redis_client:
            return

        try:
            for job_id in self.jobs:
                state_key = f"job_state:{job_id}"
                state_data = await self.redis_client.get(state_key)

                if state_data:
                    state = json.loads(state_data)
                    job = self.jobs[job_id]

                    job.last_run = datetime.fromisoformat(state["last_run"]) if state.get("last_run") else None
                    job.last_success = datetime.fromisoformat(state["last_success"]) if state.get("last_success") else None
                    job.last_error = state.get("last_error")
                    job.consecutive_failures = state.get("consecutive_failures", 0)

        except Exception as e:
            logger.error(f"Failed to load job states from Redis: {e}")

    async def _save_job_states(self):
        """Save job states to Redis"""
        if not self.redis_client:
            return

        try:
            for job_id, job in self.jobs.items():
                state_key = f"job_state:{job_id}"
                state_data = {
                    "last_run": job.last_run.isoformat() if job.last_run else None,
                    "last_success": job.last_success.isoformat() if job.last_success else None,
                    "last_error": job.last_error,
                    "consecutive_failures": job.consecutive_failures
                }

                await self.redis_client.set(
                    state_key,
                    json.dumps(state_data),
                    ex=86400 * 7  # Expire after 7 days
                )

        except Exception as e:
            logger.error(f"Failed to save job states to Redis: {e}")


# Global data ingestion scheduler instance
data_ingestion_scheduler = DataIngestionScheduler(
    sports_data_service=SportsDataService(),
    event_publisher=None  # Will be set during startup
)