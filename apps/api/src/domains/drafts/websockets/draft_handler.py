"""
Real-time draft updates handler for WebSocket connections.

Provides comprehensive draft event handling including:
- Real-time draft pick notifications
- Timer countdown broadcasts
- Draft status updates and synchronization
- User authentication and authorization
- Draft room management and access control
- Event filtering and personalization
- Error handling and connection recovery
- Integration with draft timer and evaluation systems
"""

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging

    get_logger = logging.getLogger  # type: ignore[assignment]

from domains.teams.models.team import Team

from domains.drafts.services.draft_timer import get_draft_timer_service
from domains.leagues.models.league import League
from domains.sports.services.sports_data_service import get_sports_data_service
from infrastructure.events.redis_pubsub import (
    Event,
    EventFilter,
    EventType,
    get_event_system,
)
from infrastructure.websockets.connection_manager import (
    MessageType,
    RoomType,
    get_connection_manager,
)

logger = get_logger(__name__)


class DraftWebSocketError(Exception):
    """Draft WebSocket handler errors."""


class DraftWebSocketHandler:
    """Handles real-time draft updates via WebSocket."""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.connection_manager = get_connection_manager()
        self.event_system = get_event_system()
        self.draft_timer_service = get_draft_timer_service()

        # Active draft rooms
        self.active_draft_rooms: dict[str, dict[str, Any]] = {}

        # Event subscription
        self.subscription_id: str | None = None

    async def initialize(self):
        """Initialize the draft handler."""
        try:
            # Register message handlers
            self.connection_manager.register_message_handler(
                MessageType.DRAFT_PICK, self._handle_draft_pick_message
            )
            self.connection_manager.register_message_handler(
                MessageType.DRAFT_STATUS, self._handle_draft_status_request
            )

            # Subscribe to draft events
            draft_filter = EventFilter(
                event_types=[
                    EventType.DRAFT_STARTED,
                    EventType.DRAFT_PICK_MADE,
                    EventType.DRAFT_TIMER_UPDATE,
                    EventType.DRAFT_COMPLETED,
                    EventType.DRAFT_PAUSED,
                    EventType.DRAFT_RESUMED,
                ]
            )

            self.subscription_id = await self.event_system.subscribe(
                handler=self._handle_draft_event,
                event_filter=draft_filter,
                subscription_id="draft_websocket_handler",
            )

            logger.info("Draft WebSocket handler initialized")

        except Exception as e:
            logger.error(f"Failed to initialize draft handler: {e}")
            raise DraftWebSocketError(f"Failed to initialize: {e}")

    async def shutdown(self):
        """Shutdown the draft handler."""
        try:
            if self.subscription_id:
                await self.event_system.unsubscribe(self.subscription_id)

            logger.info("Draft WebSocket handler shutdown")

        except Exception as e:
            logger.error(f"Error shutting down draft handler: {e}")

    async def join_draft_room(
        self, connection_id: str, league_id: str, user_id: str
    ) -> dict[str, Any]:
        """
        Join a user to a draft room.

        Args:
            connection_id: WebSocket connection ID
            league_id: League/draft ID to join
            user_id: User ID joining

        Returns:
            Dict containing join result and draft status
        """
        try:
            # Validate user can join this draft
            access_result = await self._validate_draft_access(league_id, user_id)
            if not access_result["allowed"]:
                return {
                    "success": False,
                    "error": access_result["reason"],
                }

            # Create room if it doesn't exist
            room_id = f"draft_{league_id}"
            await self.connection_manager.create_room(
                room_id=room_id,
                room_type=RoomType.DRAFT,
                metadata={
                    "league_id": league_id,
                    "draft_type": "snake",
                    "created_at": datetime.utcnow().isoformat(),
                },
            )

            # Join the room
            join_success = await self.connection_manager.join_room(
                connection_id, room_id
            )
            if not join_success:
                return {
                    "success": False,
                    "error": "Failed to join draft room",
                }

            # Track draft room activity
            if room_id not in self.active_draft_rooms:
                self.active_draft_rooms[room_id] = {
                    "league_id": league_id,
                    "participants": set(),
                    "created_at": datetime.utcnow(),
                    "last_activity": datetime.utcnow(),
                }

            self.active_draft_rooms[room_id]["participants"].add(user_id)
            self.active_draft_rooms[room_id]["last_activity"] = datetime.utcnow()

            # Get current draft status
            draft_status = await self._get_draft_status(league_id)

            # Send initial draft state
            await self.connection_manager.send_message(
                connection_id=connection_id,
                message_type=MessageType.DRAFT_STATUS,
                data={
                    "action": "joined",
                    "room_id": room_id,
                    "draft_status": draft_status,
                    "user_info": access_result["user_info"],
                },
                room_id=room_id,
            )

            # Notify other participants
            await self.connection_manager.broadcast_to_room(
                room_id=room_id,
                message_type=MessageType.DRAFT_STATUS,
                data={
                    "action": "user_joined",
                    "user_id": user_id,
                    "user_name": access_result["user_info"]["team_name"],
                    "participant_count": len(
                        self.active_draft_rooms[room_id]["participants"]
                    ),
                },
                exclude_connections={connection_id},
            )

            logger.info(
                "User joined draft room",
                extra={
                    "user_id": user_id,
                    "league_id": league_id,
                    "room_id": room_id,
                    "connection_id": connection_id,
                },
            )

            return {
                "success": True,
                "room_id": room_id,
                "draft_status": draft_status,
                "user_info": access_result["user_info"],
            }

        except Exception as e:
            logger.error(f"Failed to join draft room: {e}")
            return {
                "success": False,
                "error": f"Failed to join draft room: {e}",
            }

    async def leave_draft_room(self, connection_id: str, room_id: str, user_id: str):
        """
        Remove user from draft room.

        Args:
            connection_id: WebSocket connection ID
            room_id: Draft room ID to leave
            user_id: User ID leaving
        """
        try:
            # Leave the room
            await self.connection_manager.leave_room(connection_id, room_id)

            # Update room tracking
            if room_id in self.active_draft_rooms:
                self.active_draft_rooms[room_id]["participants"].discard(user_id)
                self.active_draft_rooms[room_id]["last_activity"] = datetime.utcnow()

                # Notify remaining participants
                await self.connection_manager.broadcast_to_room(
                    room_id=room_id,
                    message_type=MessageType.DRAFT_STATUS,
                    data={
                        "action": "user_left",
                        "user_id": user_id,
                        "participant_count": len(
                            self.active_draft_rooms[room_id]["participants"]
                        ),
                    },
                )

                # Clean up empty rooms
                if not self.active_draft_rooms[room_id]["participants"]:
                    del self.active_draft_rooms[room_id]

            logger.info(f"User left draft room: {user_id} from {room_id}")

        except Exception as e:
            logger.error(f"Error leaving draft room: {e}")

    # Event handlers

    async def _handle_draft_event(self, event: Event):
        """Handle draft events from the event system."""
        try:
            league_id = event.data.get("league_id") or event.data.get("draft_id")
            if not league_id:
                return

            room_id = f"draft_{league_id}"

            # Convert event to WebSocket message
            if event.event_type == EventType.DRAFT_STARTED:
                await self._broadcast_draft_started(room_id, event.data)

            elif event.event_type == EventType.DRAFT_PICK_MADE:
                await self._broadcast_pick_made(room_id, event.data)

            elif event.event_type == EventType.DRAFT_TIMER_UPDATE:
                await self._broadcast_timer_update(room_id, event.data)

            elif event.event_type == EventType.DRAFT_COMPLETED:
                await self._broadcast_draft_completed(room_id, event.data)

            elif event.event_type in [EventType.DRAFT_PAUSED, EventType.DRAFT_RESUMED]:
                await self._broadcast_draft_status_change(
                    room_id, event.event_type, event.data
                )

        except Exception as e:
            logger.error(f"Error handling draft event: {e}")

    async def _handle_draft_pick_message(
        self, connection_id: str, data: dict[str, Any], room_id: str
    ):
        """Handle draft pick submission from WebSocket."""
        try:
            # This would typically validate and forward to the draft service
            # The actual pick logic is handled by the draft API endpoints

            await self.connection_manager.send_message(
                connection_id=connection_id,
                message_type=MessageType.ERROR,
                data={
                    "message": "Draft picks must be submitted via API endpoints",
                    "redirect": f"/api/v1/draft/{data.get('league_id')}/pick",
                },
            )

        except Exception as e:
            logger.error(f"Error handling draft pick message: {e}")

    async def _handle_draft_status_request(
        self, connection_id: str, data: dict[str, Any], room_id: str
    ):
        """Handle request for current draft status."""
        try:
            league_id = data.get("league_id")
            if not league_id:
                await self.connection_manager.send_message(
                    connection_id=connection_id,
                    message_type=MessageType.ERROR,
                    data={"message": "league_id required"},
                )
                return

            # Get current draft status
            draft_status = await self._get_draft_status(league_id)

            await self.connection_manager.send_message(
                connection_id=connection_id,
                message_type=MessageType.DRAFT_STATUS,
                data={
                    "action": "status_update",
                    "draft_status": draft_status,
                },
                room_id=room_id,
            )

        except Exception as e:
            logger.error(f"Error handling draft status request: {e}")

    # Broadcast methods

    async def _broadcast_draft_started(self, room_id: str, data: dict[str, Any]):
        """Broadcast draft started event."""
        await self.connection_manager.broadcast_to_room(
            room_id=room_id,
            message_type=MessageType.DRAFT_STATUS,
            data={
                "action": "draft_started",
                "draft_order": data.get("draft_order", []),
                "current_pick": data.get("current_pick"),
                "timer_settings": data.get("timer_settings", {}),
                "started_at": data.get("started_at"),
            },
        )

    async def _broadcast_pick_made(self, room_id: str, data: dict[str, Any]):
        """Broadcast pick made event."""
        # Enhance pick data with player details
        enhanced_data = await self._enhance_pick_data(data)

        await self.connection_manager.broadcast_to_room(
            room_id=room_id,
            message_type=MessageType.DRAFT_PICK,
            data={
                "action": "pick_made",
                **enhanced_data,
            },
        )

    async def _broadcast_timer_update(self, room_id: str, data: dict[str, Any]):
        """Broadcast timer update event."""
        await self.connection_manager.broadcast_to_room(
            room_id=room_id,
            message_type=MessageType.DRAFT_TIMER,
            data={
                "action": "timer_update",
                "time_remaining": data.get("time_remaining"),
                "current_pick": data.get("current_pick"),
                "is_paused": data.get("is_paused", False),
                "warning_threshold": data.get("warning_threshold"),
            },
        )

    async def _broadcast_draft_completed(self, room_id: str, data: dict[str, Any]):
        """Broadcast draft completion event."""
        await self.connection_manager.broadcast_to_room(
            room_id=room_id,
            message_type=MessageType.DRAFT_STATUS,
            data={
                "action": "draft_completed",
                "total_picks": data.get("total_picks"),
                "completed_at": data.get("completed_at"),
                "final_results": data.get("final_results", {}),
            },
        )

    async def _broadcast_draft_status_change(
        self, room_id: str, event_type: EventType, data: dict[str, Any]
    ):
        """Broadcast draft status change (pause/resume)."""
        action = (
            "draft_paused" if event_type == EventType.DRAFT_PAUSED else "draft_resumed"
        )

        await self.connection_manager.broadcast_to_room(
            room_id=room_id,
            message_type=MessageType.DRAFT_STATUS,
            data={
                "action": action,
                "time_remaining": data.get("time_remaining"),
                "current_pick": data.get("current_pick"),
                "reason": data.get("reason"),
            },
        )

    # Helper methods

    async def _validate_draft_access(
        self, league_id: str, user_id: str
    ) -> dict[str, Any]:
        """Validate if user can access the draft."""
        try:
            # Get league
            league = self.db.query(League).filter(League.league_id == league_id).first()

            if not league:
                return {
                    "allowed": False,
                    "reason": "League not found",
                }

            # Check if user is in this league
            user_team = (
                self.db.query(Team)
                .filter(Team.league_id == league_id, Team.owner_id == user_id)
                .first()
            )

            if not user_team:
                # Check if user is commissioner
                if league.commissioner_id != user_id:
                    return {
                        "allowed": False,
                        "reason": "User not in this league",
                    }
                else:
                    # Commissioner access
                    return {
                        "allowed": True,
                        "reason": "Commissioner access",
                        "user_info": {
                            "user_id": user_id,
                            "team_id": None,
                            "team_name": "Commissioner",
                            "role": "commissioner",
                        },
                    }

            return {
                "allowed": True,
                "reason": "League member",
                "user_info": {
                    "user_id": user_id,
                    "team_id": user_team.team_id,
                    "team_name": user_team.team_name,
                    "role": "team_owner",
                },
            }

        except Exception as e:
            logger.error(f"Error validating draft access: {e}")
            return {
                "allowed": False,
                "reason": f"Validation error: {e}",
            }

    async def _get_draft_status(self, league_id: str) -> dict[str, Any]:
        """Get comprehensive draft status."""
        try:
            # Get draft timer
            draft_timer = self.draft_timer_service.get_draft_timer(league_id)

            if not draft_timer:
                return {
                    "status": "not_started",
                    "message": "No active draft",
                }

            # Get timer status
            timer_status = draft_timer.get_timer_status()

            # Get draft order summary
            draft_order = draft_timer.draft_order
            order_summary = [
                {
                    "overall_pick": pick.overall_pick,
                    "round_number": pick.round_number,
                    "pick_in_round": pick.pick_in_round,
                    "team_id": pick.team_id,
                    "has_pick": pick.player_id is not None,
                    "is_current": pick.overall_pick
                    == (timer_status.get("current_pick", {}).get("overall_pick")),
                }
                for pick in draft_order.picks[:50]  # Limit for performance
            ]

            return {
                "status": timer_status["status"],
                "current_pick": timer_status.get("current_pick"),
                "time_remaining": timer_status.get("time_remaining"),
                "is_paused": timer_status.get("is_paused", False),
                "completed_picks": timer_status.get("completed_picks", 0),
                "total_picks": timer_status.get("total_picks", 0),
                "progress_percentage": round(
                    (
                        timer_status.get("completed_picks", 0)
                        / max(timer_status.get("total_picks", 1), 1)
                    )
                    * 100,
                    1,
                ),
                "draft_order_preview": order_summary,
                "teams": draft_order.teams,
                "settings": {
                    "total_rounds": draft_order.total_rounds,
                    "pick_time_seconds": draft_timer.pick_time_seconds,
                },
            }

        except Exception as e:
            logger.error(f"Error getting draft status: {e}")
            return {
                "status": "error",
                "message": f"Error getting draft status: {e}",
            }

    async def _enhance_pick_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Enhance pick data with player details."""
        try:
            player_id = data.get("player_id")
            if not player_id:
                return data

            # Get player details
            sports_service = await get_sports_data_service()
            player_data = await sports_service.get_player_details(player_id)

            if player_data:
                data["player_info"] = {
                    "name": player_data.get("name"),
                    "position": player_data.get("position"),
                    "team": player_data.get("team"),
                    "sport": player_data.get("sport"),
                    "stats": player_data.get("season_stats", {}),
                }

            return data

        except Exception as e:
            logger.error(f"Error enhancing pick data: {e}")
            return data

    def get_active_rooms_stats(self) -> dict[str, Any]:
        """Get statistics about active draft rooms."""
        return {
            "total_active_rooms": len(self.active_draft_rooms),
            "rooms": {
                room_id: {
                    "league_id": room_info["league_id"],
                    "participant_count": len(room_info["participants"]),
                    "created_at": room_info["created_at"].isoformat(),
                    "last_activity": room_info["last_activity"].isoformat(),
                }
                for room_id, room_info in self.active_draft_rooms.items()
            },
        }


# Global handler instance
_draft_handler: DraftWebSocketHandler | None = None


def get_draft_handler(db_session: Session) -> DraftWebSocketHandler:
    """Get or create draft WebSocket handler."""
    global _draft_handler
    if _draft_handler is None:
        _draft_handler = DraftWebSocketHandler(db_session)
    return _draft_handler


async def initialize_draft_handler(db_session: Session):
    """Initialize the draft WebSocket handler."""
    handler = get_draft_handler(db_session)
    await handler.initialize()
    return handler


async def shutdown_draft_handler():
    """Shutdown the draft WebSocket handler."""
    global _draft_handler
    if _draft_handler:
        await _draft_handler.shutdown()
        _draft_handler = None
