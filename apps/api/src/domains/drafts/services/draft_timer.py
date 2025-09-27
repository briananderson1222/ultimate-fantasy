"""
Draft timer service with WebSocket broadcasts for real-time draft management.

Provides comprehensive draft timing functionality including:
- Real-time countdown timers for draft picks
- WebSocket broadcasts to all draft participants
- Auto-pick handling when timers expire
- Pick deadline management and notifications
- Draft pause/resume capabilities
- Timer synchronization across clients
- Integration with snake draft algorithm
"""

import asyncio
import json
from datetime import datetime, timedelta
from enum import Enum

from fastapi import WebSocket

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging

    get_logger = logging.getLogger  # type: ignore[assignment]

import contextlib

from domains.drafts.algorithms.snake_draft import (
    DraftOrder,
    DraftPick,
    get_snake_draft_algorithm,
)

logger = get_logger(__name__)


class TimerState(Enum):
    """Draft timer states."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"


class DraftTimerError(Exception):
    """Draft timer service errors."""


class WebSocketManager:
    """Manages WebSocket connections for draft rooms."""

    def __init__(self):
        self.connections: dict[str, set[WebSocket]] = {}
        self.user_connections: dict[str, dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, draft_id: str, user_id: str):
        """Connect a user to a draft room."""
        await websocket.accept()

        if draft_id not in self.connections:
            self.connections[draft_id] = set()
            self.user_connections[draft_id] = {}

        self.connections[draft_id].add(websocket)
        self.user_connections[draft_id][user_id] = websocket

        logger.info(f"User {user_id} connected to draft {draft_id}")

    def disconnect(self, websocket: WebSocket, draft_id: str, user_id: str):
        """Disconnect a user from a draft room."""
        if draft_id in self.connections:
            self.connections[draft_id].discard(websocket)
            if user_id in self.user_connections.get(draft_id, {}):
                del self.user_connections[draft_id][user_id]

        logger.info(f"User {user_id} disconnected from draft {draft_id}")

    async def broadcast_to_draft(self, draft_id: str, message: dict):
        """Broadcast message to all users in a draft."""
        if draft_id not in self.connections:
            return

        message_str = json.dumps(message)
        disconnected = set()

        for websocket in self.connections[draft_id]:
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.warning(f"Failed to send message to websocket: {e}")
                disconnected.add(websocket)

        # Clean up disconnected websockets
        for websocket in disconnected:
            self.connections[draft_id].discard(websocket)

    async def send_to_user(self, draft_id: str, user_id: str, message: dict):
        """Send message to a specific user."""
        if (
            draft_id in self.user_connections
            and user_id in self.user_connections[draft_id]
        ):

            websocket = self.user_connections[draft_id][user_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send message to user {user_id}: {e}")
                self.user_connections[draft_id].pop(user_id, None)


class DraftTimer:
    """Draft timer for managing pick countdowns and auto-picks."""

    def __init__(
        self,
        draft_id: str,
        draft_order: DraftOrder,
        pick_time_seconds: int = 90,
        websocket_manager: WebSocketManager | None = None,
    ):
        self.draft_id = draft_id
        self.draft_order = draft_order
        self.pick_time_seconds = pick_time_seconds
        self.websocket_manager = websocket_manager or WebSocketManager()

        # Timer state
        self.current_pick: DraftPick | None = None
        self.pick_start_time: datetime | None = None
        self.timer_task: asyncio.Task | None = None
        self.is_paused = False
        self.pause_time_remaining: int | None = None

        # Completed picks tracking
        self.completed_picks: set[int] = set()

        # Callbacks
        self.on_pick_timeout_callback = None
        self.on_pick_warning_callback = None

        # Snake draft algorithm
        self.snake_algorithm = get_snake_draft_algorithm()

        logger.info(f"Draft timer initialized for draft {draft_id}")

    async def start_draft(self):
        """Start the draft and begin timer for first pick."""
        try:
            # Get first pick
            first_pick = self.snake_algorithm.get_current_pick(
                self.draft_order, list(self.completed_picks)
            )

            if not first_pick:
                raise DraftTimerError("No picks available to start draft")

            await self._start_pick_timer(first_pick)

            # Broadcast draft started
            await self._broadcast_draft_status(
                "draft_started",
                {
                    "draft_id": self.draft_id,
                    "current_pick": self._serialize_pick(first_pick),
                    "pick_time_seconds": self.pick_time_seconds,
                },
            )

            logger.info(
                f"Draft {self.draft_id} started with pick {first_pick.overall_pick}"
            )

        except Exception as e:
            logger.error(f"Failed to start draft {self.draft_id}: {e}")
            raise DraftTimerError(f"Failed to start draft: {e}")

    async def make_pick(self, overall_pick: int, team_id: str, player_id: str) -> bool:
        """
        Process a manual pick and advance to next pick.

        Returns:
            True if pick was successful, False otherwise
        """
        try:
            # Validate pick
            if not self.snake_algorithm.validate_pick(
                self.draft_order, overall_pick, team_id, list(self.completed_picks)
            ):
                logger.warning(f"Invalid pick: {overall_pick} by team {team_id}")
                return False

            # Stop current timer
            await self._stop_timer()

            # Record the pick
            self.completed_picks.add(overall_pick)

            # Update pick with player and timestamp
            pick = next(
                p for p in self.draft_order.picks if p.overall_pick == overall_pick
            )
            pick.player_id = player_id
            pick.pick_time = datetime.utcnow()
            pick.is_autopick = False

            # Broadcast pick made
            await self._broadcast_draft_status(
                "pick_made",
                {
                    "pick": self._serialize_pick(pick),
                    "player_id": player_id,
                    "team_id": team_id,
                },
            )

            # Start timer for next pick
            await self._advance_to_next_pick()

            logger.info(
                f"Pick {overall_pick} made by team {team_id} for player {player_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to process pick {overall_pick}: {e}")
            return False

    async def pause_draft(self) -> bool:
        """Pause the current draft timer."""
        try:
            if not self.current_pick or self.is_paused:
                return False

            # Calculate remaining time
            if self.pick_start_time:
                elapsed = (datetime.utcnow() - self.pick_start_time).total_seconds()
                self.pause_time_remaining = max(
                    0, self.pick_time_seconds - int(elapsed)
                )
            else:
                self.pause_time_remaining = self.pick_time_seconds

            # Stop timer
            await self._stop_timer()
            self.is_paused = True

            # Broadcast pause
            await self._broadcast_draft_status(
                "draft_paused",
                {
                    "time_remaining": self.pause_time_remaining,
                    "current_pick": self._serialize_pick(self.current_pick),
                },
            )

            logger.info(
                f"Draft {self.draft_id} paused with {self.pause_time_remaining}s remaining"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to pause draft {self.draft_id}: {e}")
            return False

    async def resume_draft(self) -> bool:
        """Resume the paused draft timer."""
        try:
            if not self.is_paused or not self.current_pick:
                return False

            # Resume with remaining time
            resume_time = self.pause_time_remaining or self.pick_time_seconds
            await self._start_pick_timer(self.current_pick, resume_time)

            self.is_paused = False
            self.pause_time_remaining = None

            # Broadcast resume
            await self._broadcast_draft_status(
                "draft_resumed",
                {
                    "current_pick": self._serialize_pick(self.current_pick),
                    "time_remaining": resume_time,
                },
            )

            logger.info(f"Draft {self.draft_id} resumed with {resume_time}s remaining")
            return True

        except Exception as e:
            logger.error(f"Failed to resume draft {self.draft_id}: {e}")
            return False

    def get_timer_status(self) -> dict:
        """Get current timer status."""
        if not self.current_pick:
            return {
                "status": "not_started",
                "current_pick": None,
                "time_remaining": 0,
                "is_paused": False,
            }

        time_remaining = 0
        if self.is_paused:
            time_remaining = self.pause_time_remaining or 0
        elif self.pick_start_time:
            time_remaining = self.snake_algorithm.get_time_remaining(
                self.pick_start_time, self.pick_time_seconds
            )

        return {
            "status": "in_progress" if not self.is_paused else "paused",
            "current_pick": self._serialize_pick(self.current_pick),
            "time_remaining": time_remaining,
            "is_paused": self.is_paused,
            "completed_picks": len(self.completed_picks),
            "total_picks": len(self.draft_order.picks),
        }

    def set_callbacks(
        self,
        on_timeout=None,
        on_warning=None,
    ):
        """Set callback functions for timer events."""
        self.on_pick_timeout_callback = on_timeout
        self.on_pick_warning_callback = on_warning

    # Private methods

    async def _start_pick_timer(self, pick: DraftPick, time_seconds: int | None = None):
        """Start countdown timer for a pick."""
        self.current_pick = pick
        self.pick_start_time = datetime.utcnow()
        pick_time = time_seconds or self.pick_time_seconds

        # Start timer task
        self.timer_task = asyncio.create_task(self._run_pick_timer(pick, pick_time))

        # Broadcast timer started
        await self._broadcast_draft_status(
            "pick_timer_started",
            {
                "current_pick": self._serialize_pick(pick),
                "time_remaining": pick_time,
                "pick_deadline": (
                    self.pick_start_time + timedelta(seconds=pick_time)
                ).isoformat(),
            },
        )

    async def _run_pick_timer(self, pick: DraftPick, time_seconds: int):
        """Run the countdown timer for a pick."""
        try:
            # Send periodic updates
            warning_sent = False

            for remaining in range(time_seconds, 0, -1):
                # Check if timer was cancelled
                if self.timer_task and self.timer_task.cancelled():
                    return

                # Send warning at 30 seconds
                if remaining == 30 and not warning_sent:
                    await self._broadcast_draft_status(
                        "pick_warning",
                        {
                            "current_pick": self._serialize_pick(pick),
                            "time_remaining": remaining,
                        },
                    )
                    if self.on_pick_warning_callback:
                        await self.on_pick_warning_callback(pick, remaining)
                    warning_sent = True

                # Send countdown updates every 10 seconds or last 10 seconds
                if remaining % 10 == 0 or remaining <= 10:
                    await self._broadcast_draft_status(
                        "pick_countdown",
                        {
                            "current_pick": self._serialize_pick(pick),
                            "time_remaining": remaining,
                        },
                    )

                await asyncio.sleep(1)

            # Timer expired - trigger auto-pick
            await self._handle_pick_timeout(pick)

        except asyncio.CancelledError:
            logger.info(f"Timer cancelled for pick {pick.overall_pick}")
        except Exception as e:
            logger.error(f"Timer error for pick {pick.overall_pick}: {e}")

    async def _handle_pick_timeout(self, pick: DraftPick):
        """Handle when a pick timer expires."""
        try:
            # Mark as auto-pick
            pick.player_id = "AUTO_PICK_PLACEHOLDER"  # To be filled by auto-pick logic
            pick.pick_time = datetime.utcnow()
            pick.is_autopick = True

            self.completed_picks.add(pick.overall_pick)

            # Broadcast timeout
            await self._broadcast_draft_status(
                "pick_timeout",
                {
                    "pick": self._serialize_pick(pick),
                    "auto_pick": True,
                },
            )

            # Call timeout callback
            if self.on_pick_timeout_callback:
                await self.on_pick_timeout_callback(pick)

            # Advance to next pick
            await self._advance_to_next_pick()

            logger.info(f"Pick {pick.overall_pick} timed out for team {pick.team_id}")

        except Exception as e:
            logger.error(f"Failed to handle timeout for pick {pick.overall_pick}: {e}")

    async def _advance_to_next_pick(self):
        """Advance to the next pick in the draft."""
        try:
            # Get next pick
            next_pick = self.snake_algorithm.get_current_pick(
                self.draft_order, list(self.completed_picks)
            )

            if next_pick:
                # Start timer for next pick
                await self._start_pick_timer(next_pick)
                logger.info(
                    f"Advanced to pick {next_pick.overall_pick} for team {next_pick.team_id}"
                )
            else:
                # Draft is complete
                await self._handle_draft_complete()

        except Exception as e:
            logger.error(f"Failed to advance to next pick: {e}")

    async def _handle_draft_complete(self):
        """Handle draft completion."""
        self.current_pick = None
        self.pick_start_time = None

        await self._broadcast_draft_status(
            "draft_complete",
            {
                "total_picks": len(self.completed_picks),
                "completed_at": datetime.utcnow().isoformat(),
            },
        )

        logger.info(
            f"Draft {self.draft_id} completed with {len(self.completed_picks)} picks"
        )

    async def _stop_timer(self):
        """Stop the current timer task."""
        if self.timer_task and not self.timer_task.cancelled():
            self.timer_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.timer_task
            self.timer_task = None

    async def _broadcast_draft_status(self, event_type: str, data: dict):
        """Broadcast draft status update to all connected clients."""
        if not self.websocket_manager:
            return

        message = {
            "type": event_type,
            "draft_id": self.draft_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }

        await self.websocket_manager.broadcast_to_draft(self.draft_id, message)

    def _serialize_pick(self, pick: DraftPick) -> dict:
        """Serialize a draft pick for JSON transmission."""
        return {
            "overall_pick": pick.overall_pick,
            "round_number": pick.round_number,
            "pick_in_round": pick.pick_in_round,
            "team_id": pick.team_id,
            "player_id": pick.player_id,
            "pick_time": pick.pick_time.isoformat() if pick.pick_time else None,
            "is_autopick": pick.is_autopick,
            "is_keeper": pick.is_keeper,
            "original_team_id": pick.original_team_id,
        }


class DraftTimerService:
    """Service for managing multiple draft timers."""

    def __init__(self):
        self.active_drafts: dict[str, DraftTimer] = {}
        self.websocket_manager = WebSocketManager()

    async def create_draft_timer(
        self,
        draft_id: str,
        draft_order: DraftOrder,
        pick_time_seconds: int = 90,
    ) -> DraftTimer:
        """Create and configure a new draft timer."""
        if draft_id in self.active_drafts:
            raise DraftTimerError(f"Draft timer already exists for {draft_id}")

        timer = DraftTimer(
            draft_id=draft_id,
            draft_order=draft_order,
            pick_time_seconds=pick_time_seconds,
            websocket_manager=self.websocket_manager,
        )

        self.active_drafts[draft_id] = timer

        logger.info(f"Created draft timer for {draft_id}")
        return timer

    def get_draft_timer(self, draft_id: str) -> DraftTimer | None:
        """Get existing draft timer."""
        return self.active_drafts.get(draft_id)

    async def remove_draft_timer(self, draft_id: str) -> bool:
        """Remove and cleanup draft timer."""
        if draft_id not in self.active_drafts:
            return False

        timer = self.active_drafts[draft_id]
        await timer._stop_timer()
        del self.active_drafts[draft_id]

        logger.info(f"Removed draft timer for {draft_id}")
        return True

    async def connect_user_to_draft(
        self,
        websocket: WebSocket,
        draft_id: str,
        user_id: str,
    ):
        """Connect a user to draft WebSocket room."""
        await self.websocket_manager.connect(websocket, draft_id, user_id)

    def disconnect_user_from_draft(
        self,
        websocket: WebSocket,
        draft_id: str,
        user_id: str,
    ):
        """Disconnect user from draft WebSocket room."""
        self.websocket_manager.disconnect(websocket, draft_id, user_id)

    def get_active_draft_count(self) -> int:
        """Get number of active drafts."""
        return len(self.active_drafts)

    def list_active_drafts(self) -> list[str]:
        """List all active draft IDs."""
        return list(self.active_drafts.keys())


# Global service instance
_draft_timer_service: DraftTimerService | None = None


def get_draft_timer_service() -> DraftTimerService:
    """Get the global draft timer service instance."""
    global _draft_timer_service
    if _draft_timer_service is None:
        _draft_timer_service = DraftTimerService()
    return _draft_timer_service


def reset_draft_timer_service():
    """Reset the global service (useful for testing)."""
    global _draft_timer_service
    _draft_timer_service = None
