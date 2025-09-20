"""
Real-time Event Publisher for Ultimate Fantasy Platform
Handles event publishing and cross-service communication via Redis pub/sub
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Callable
from enum import Enum
from dataclasses import dataclass, asdict
from collections import defaultdict

import redis.asyncio as redis
from sqlalchemy.orm import Session

from ..infrastructure.database.session_factory import get_db_session
from ..api.websockets.connection_manager import ConnectionManager, Message, MessageType, ConnectionType
from ..domains.leagues.services.league_service import LeagueService
from ..domains.users.services.user_service import UserService


logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events that can be published"""
    # Draft events
    DRAFT_STARTED = "draft_started"
    DRAFT_PICK_MADE = "draft_pick_made"
    DRAFT_TIMER_UPDATE = "draft_timer_update"
    DRAFT_COMPLETED = "draft_completed"
    DRAFT_PAUSED = "draft_paused"
    DRAFT_RESUMED = "draft_resumed"

    # Score events
    PLAYER_SCORE_UPDATE = "player_score_update"
    LINEUP_SCORE_UPDATE = "lineup_score_update"
    GAME_STARTED = "game_started"
    GAME_FINAL = "game_final"
    LINEUP_LOCKED = "lineup_locked"

    # Trade events
    TRADE_PROPOSED = "trade_proposed"
    TRADE_ACCEPTED = "trade_accepted"
    TRADE_REJECTED = "trade_rejected"
    TRADE_COUNTERED = "trade_countered"
    TRADE_EXPIRED = "trade_expired"
    TRADE_CANCELLED = "trade_cancelled"

    # Waiver events
    WAIVER_CLAIM_SUBMITTED = "waiver_claim_submitted"
    WAIVER_CLAIMS_PROCESSED = "waiver_claims_processed"
    WAIVER_WON = "waiver_won"
    WAIVER_LOST = "waiver_lost"

    # League events
    LEAGUE_CREATED = "league_created"
    USER_JOINED_LEAGUE = "user_joined_league"
    USER_LEFT_LEAGUE = "user_left_league"
    LEAGUE_SETTINGS_UPDATED = "league_settings_updated"

    # Chat events
    CHAT_MESSAGE_SENT = "chat_message_sent"
    CHAT_MESSAGE_DELETED = "chat_message_deleted"
    CHAT_MESSAGE_EDITED = "chat_message_edited"

    # System events
    PLAYER_INJURY_UPDATE = "player_injury_update"
    PLAYER_TRADE_REAL = "player_trade_real"
    SEASON_STARTED = "season_started"
    SEASON_ENDED = "season_ended"

    # Notification events
    NOTIFICATION_CREATED = "notification_created"
    NOTIFICATION_READ = "notification_read"

    # Analytics events
    LINEUP_OPTIMIZED = "lineup_optimized"
    RECOMMENDATION_GENERATED = "recommendation_generated"


@dataclass
class Event:
    """Event data structure"""
    event_id: str
    event_type: EventType
    source_service: str
    league_id: Optional[str] = None
    user_id: Optional[str] = None
    target_users: Optional[List[str]] = None
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    correlation_id: Optional[str] = None
    priority: int = 5  # 1=highest, 10=lowest

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.correlation_id is None:
            self.correlation_id = str(uuid.uuid4())
        if self.data is None:
            self.data = {}
        if self.metadata is None:
            self.metadata = {}


class EventHandler:
    """Base class for event handlers"""

    def __init__(self, event_types: List[EventType]):
        self.event_types = event_types

    async def handle(self, event: Event) -> bool:
        """Handle an event. Return True if handled successfully."""
        raise NotImplementedError

    def can_handle(self, event_type: EventType) -> bool:
        """Check if this handler can process the event type"""
        return event_type in self.event_types


class WebSocketEventHandler(EventHandler):
    """Handles events by broadcasting to WebSocket connections"""

    def __init__(self, connection_manager: ConnectionManager):
        super().__init__([
            EventType.DRAFT_STARTED, EventType.DRAFT_PICK_MADE, EventType.DRAFT_TIMER_UPDATE,
            EventType.DRAFT_COMPLETED, EventType.DRAFT_PAUSED, EventType.DRAFT_RESUMED,
            EventType.PLAYER_SCORE_UPDATE, EventType.LINEUP_SCORE_UPDATE,
            EventType.GAME_STARTED, EventType.GAME_FINAL, EventType.LINEUP_LOCKED,
            EventType.TRADE_PROPOSED, EventType.TRADE_ACCEPTED, EventType.TRADE_REJECTED,
            EventType.TRADE_COUNTERED, EventType.TRADE_EXPIRED, EventType.TRADE_CANCELLED,
            EventType.WAIVER_WON, EventType.WAIVER_LOST, EventType.WAIVER_CLAIMS_PROCESSED,
            EventType.CHAT_MESSAGE_SENT, EventType.USER_JOINED_LEAGUE, EventType.USER_LEFT_LEAGUE,
            EventType.NOTIFICATION_CREATED
        ])
        self.connection_manager = connection_manager

    async def handle(self, event: Event) -> bool:
        """Convert event to WebSocket message and broadcast"""
        try:
            # Map event types to message types
            message_type_mapping = {
                EventType.DRAFT_STARTED: MessageType.DRAFT_STARTED,
                EventType.DRAFT_PICK_MADE: MessageType.DRAFT_PICK,
                EventType.DRAFT_TIMER_UPDATE: MessageType.DRAFT_TIMER,
                EventType.DRAFT_COMPLETED: MessageType.DRAFT_COMPLETED,
                EventType.PLAYER_SCORE_UPDATE: MessageType.SCORE_UPDATE,
                EventType.LINEUP_SCORE_UPDATE: MessageType.SCORE_UPDATE,
                EventType.GAME_STARTED: MessageType.GAME_STARTED,
                EventType.GAME_FINAL: MessageType.GAME_FINAL,
                EventType.LINEUP_LOCKED: MessageType.LINEUP_LOCKED,
                EventType.TRADE_PROPOSED: MessageType.TRADE_PROPOSED,
                EventType.TRADE_ACCEPTED: MessageType.TRADE_ACCEPTED,
                EventType.TRADE_REJECTED: MessageType.TRADE_REJECTED,
                EventType.TRADE_EXPIRED: MessageType.TRADE_EXPIRED,
                EventType.WAIVER_WON: MessageType.WAIVER_WON,
                EventType.WAIVER_LOST: MessageType.WAIVER_LOST,
                EventType.WAIVER_CLAIMS_PROCESSED: MessageType.WAIVER_PROCESSED,
                EventType.CHAT_MESSAGE_SENT: MessageType.CHAT_MESSAGE,
                EventType.USER_JOINED_LEAGUE: MessageType.USER_JOINED,
                EventType.USER_LEFT_LEAGUE: MessageType.USER_LEFT,
                EventType.NOTIFICATION_CREATED: MessageType.NOTIFICATION
            }

            message_type = message_type_mapping.get(event.event_type)
            if not message_type:
                logger.warning(f"No message type mapping for event: {event.event_type}")
                return False

            # Create WebSocket message
            message = Message(
                type=message_type,
                data=event.data,
                league_id=event.league_id,
                user_id=event.user_id,
                target_users=event.target_users,
                timestamp=event.timestamp,
                correlation_id=event.correlation_id
            )

            # Determine broadcast method based on event type
            if event.target_users:
                # Send to specific users
                for user_id in event.target_users:
                    await self.connection_manager.send_to_user(user_id, message)

            elif event.league_id:
                # Broadcast to league
                connection_types = self._get_connection_types_for_event(event.event_type)
                await self.connection_manager.broadcast_to_league(
                    event.league_id,
                    message,
                    connection_types=connection_types
                )

            elif event.user_id:
                # Send to specific user
                await self.connection_manager.send_to_user(event.user_id, message)

            else:
                # Global broadcast (rare)
                for conn_type in self._get_connection_types_for_event(event.event_type):
                    await self.connection_manager.broadcast_to_type(conn_type, message)

            return True

        except Exception as e:
            logger.error(f"Failed to handle WebSocket event {event.event_id}: {e}")
            return False

    def _get_connection_types_for_event(self, event_type: EventType) -> List[ConnectionType]:
        """Map event types to connection types"""
        mapping = {
            EventType.DRAFT_STARTED: [ConnectionType.DRAFT],
            EventType.DRAFT_PICK_MADE: [ConnectionType.DRAFT],
            EventType.DRAFT_TIMER_UPDATE: [ConnectionType.DRAFT],
            EventType.DRAFT_COMPLETED: [ConnectionType.DRAFT, ConnectionType.GENERAL],
            EventType.PLAYER_SCORE_UPDATE: [ConnectionType.SCORES],
            EventType.LINEUP_SCORE_UPDATE: [ConnectionType.SCORES, ConnectionType.GENERAL],
            EventType.GAME_STARTED: [ConnectionType.SCORES],
            EventType.GAME_FINAL: [ConnectionType.SCORES, ConnectionType.GENERAL],
            EventType.TRADE_PROPOSED: [ConnectionType.TRADES, ConnectionType.GENERAL],
            EventType.TRADE_ACCEPTED: [ConnectionType.TRADES, ConnectionType.GENERAL],
            EventType.TRADE_REJECTED: [ConnectionType.TRADES],
            EventType.WAIVER_WON: [ConnectionType.WAIVERS, ConnectionType.GENERAL],
            EventType.WAIVER_LOST: [ConnectionType.WAIVERS],
            EventType.CHAT_MESSAGE_SENT: [ConnectionType.CHAT],
            EventType.NOTIFICATION_CREATED: [ConnectionType.GENERAL]
        }
        return mapping.get(event_type, [ConnectionType.GENERAL])


class DatabaseEventHandler(EventHandler):
    """Handles events by storing them in the database"""

    def __init__(self):
        super().__init__([
            EventType.DRAFT_PICK_MADE, EventType.TRADE_ACCEPTED, EventType.TRADE_REJECTED,
            EventType.WAIVER_WON, EventType.WAIVER_LOST, EventType.CHAT_MESSAGE_SENT,
            EventType.LEAGUE_CREATED, EventType.USER_JOINED_LEAGUE, EventType.USER_LEFT_LEAGUE
        ])

    async def handle(self, event: Event) -> bool:
        """Store event in database for audit trail"""
        try:
            # Note: This would typically use an EventLog model
            # For now, we'll just log the event
            logger.info(f"Database event: {event.event_type} - {event.event_id}")

            # Example: Store in event_log table
            # with get_db_session() as db:
            #     event_log = EventLog(
            #         event_id=event.event_id,
            #         event_type=event.event_type.value,
            #         source_service=event.source_service,
            #         league_id=event.league_id,
            #         user_id=event.user_id,
            #         data=event.data,
            #         timestamp=event.timestamp
            #     )
            #     db.add(event_log)
            #     db.commit()

            return True

        except Exception as e:
            logger.error(f"Failed to store event {event.event_id}: {e}")
            return False


class NotificationEventHandler(EventHandler):
    """Handles events by creating user notifications"""

    def __init__(self):
        super().__init__([
            EventType.TRADE_PROPOSED, EventType.TRADE_ACCEPTED, EventType.TRADE_REJECTED,
            EventType.WAIVER_WON, EventType.WAIVER_LOST, EventType.DRAFT_STARTED,
            EventType.PLAYER_INJURY_UPDATE, EventType.LINEUP_LOCKED
        ])

    async def handle(self, event: Event) -> bool:
        """Create user notifications based on events"""
        try:
            # Create notification based on event type
            notification_data = self._create_notification_data(event)
            if not notification_data:
                return True

            # Note: This would typically use the NotificationService
            logger.info(f"Creating notification for event {event.event_id}: {notification_data}")

            # Example: Create notification
            # notification_service = NotificationService()
            # await notification_service.create_notification(
            #     user_id=event.user_id or notification_data['user_id'],
            #     league_id=event.league_id,
            #     type=notification_data['type'],
            #     title=notification_data['title'],
            #     message=notification_data['message'],
            #     data=notification_data.get('data', {})
            # )

            return True

        except Exception as e:
            logger.error(f"Failed to create notification for event {event.event_id}: {e}")
            return False

    def _create_notification_data(self, event: Event) -> Optional[Dict[str, Any]]:
        """Create notification data based on event"""
        notification_templates = {
            EventType.TRADE_PROPOSED: {
                "type": "trade_offer",
                "title": "Trade Proposal Received",
                "message": f"You have received a trade proposal from {event.data.get('proposer_name', 'another user')}"
            },
            EventType.TRADE_ACCEPTED: {
                "type": "trade_accepted",
                "title": "Trade Accepted",
                "message": "Your trade proposal has been accepted!"
            },
            EventType.WAIVER_WON: {
                "type": "waiver_success",
                "title": "Waiver Claim Successful",
                "message": f"You successfully claimed {event.data.get('player_name', 'a player')} from waivers"
            },
            EventType.WAIVER_LOST: {
                "type": "waiver_failed",
                "title": "Waiver Claim Failed",
                "message": f"Your waiver claim for {event.data.get('player_name', 'a player')} was unsuccessful"
            },
            EventType.DRAFT_STARTED: {
                "type": "draft_starting",
                "title": "Draft Starting Soon",
                "message": "Your league draft is about to begin!"
            },
            EventType.PLAYER_INJURY_UPDATE: {
                "type": "injury_update",
                "title": "Player Injury Update",
                "message": f"{event.data.get('player_name', 'A player')} injury status has been updated"
            }
        }

        template = notification_templates.get(event.event_type)
        if template:
            return {**template, "data": event.data}

        return None


class EventPublisher:
    """Main event publisher class"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize event publisher with optional Redis client"""
        self.redis_client = redis_client
        self.redis_channel = "fantasy_events"

        # Event handlers
        self.handlers: Dict[EventType, List[EventHandler]] = defaultdict(list)
        self.global_handlers: List[EventHandler] = []

        # Event queue for reliability
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.processing_task: Optional[asyncio.Task] = None

        # Statistics
        self.events_published = 0
        self.events_processed = 0
        self.events_failed = 0

    async def start(self, connection_manager: ConnectionManager):
        """Start the event publisher"""
        logger.info("Starting event publisher")

        # Register default handlers
        self.register_handler(WebSocketEventHandler(connection_manager))
        self.register_handler(DatabaseEventHandler())
        self.register_handler(NotificationEventHandler())

        # Start event processing task
        self.processing_task = asyncio.create_task(self._process_events())

        # Subscribe to Redis if available
        if self.redis_client:
            asyncio.create_task(self._redis_subscriber())

    async def stop(self):
        """Stop the event publisher"""
        logger.info("Stopping event publisher")

        if self.processing_task:
            self.processing_task.cancel()

        # Process remaining events
        while not self.event_queue.empty():
            try:
                event = self.event_queue.get_nowait()
                await self._handle_event(event)
            except asyncio.QueueEmpty:
                break

    def register_handler(self, handler: EventHandler):
        """Register an event handler"""
        if handler.event_types:
            for event_type in handler.event_types:
                self.handlers[event_type].append(handler)
        else:
            # Global handler (handles all events)
            self.global_handlers.append(handler)

        logger.info(f"Registered event handler: {handler.__class__.__name__}")

    async def publish_event(
        self,
        event_type: EventType,
        source_service: str,
        league_id: Optional[str] = None,
        user_id: Optional[str] = None,
        target_users: Optional[List[str]] = None,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        priority: int = 5
    ) -> str:
        """
        Publish an event

        Args:
            event_type: Type of event
            source_service: Service that generated the event
            league_id: Optional league ID
            user_id: Optional user ID
            target_users: Optional list of target user IDs
            data: Event data
            metadata: Additional metadata
            correlation_id: Optional correlation ID for tracing
            priority: Event priority (1=highest, 10=lowest)

        Returns:
            Event ID
        """
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            source_service=source_service,
            league_id=league_id,
            user_id=user_id,
            target_users=target_users,
            data=data,
            metadata=metadata,
            correlation_id=correlation_id,
            priority=priority
        )

        # Add to local queue
        await self.event_queue.put(event)
        self.events_published += 1

        # Publish to Redis for other instances
        if self.redis_client:
            await self._publish_to_redis(event)

        logger.debug(f"Published event: {event.event_type} - {event.event_id}")
        return event.event_id

    async def get_stats(self) -> Dict[str, Any]:
        """Get event publisher statistics"""
        return {
            "events_published": self.events_published,
            "events_processed": self.events_processed,
            "events_failed": self.events_failed,
            "queue_size": self.event_queue.qsize(),
            "handlers_registered": sum(len(handlers) for handlers in self.handlers.values()) + len(self.global_handlers)
        }

    # Event publishing convenience methods

    async def publish_draft_pick(
        self,
        league_id: str,
        pick_number: int,
        team_id: str,
        player_id: str,
        player_name: str,
        correlation_id: Optional[str] = None
    ) -> str:
        """Publish draft pick event"""
        return await self.publish_event(
            event_type=EventType.DRAFT_PICK_MADE,
            source_service="draft_service",
            league_id=league_id,
            data={
                "pick_number": pick_number,
                "team_id": team_id,
                "player_id": player_id,
                "player_name": player_name
            },
            correlation_id=correlation_id,
            priority=1
        )

    async def publish_score_update(
        self,
        league_id: str,
        player_id: str,
        player_name: str,
        points: float,
        stats: Dict[str, Any],
        is_final: bool = False
    ) -> str:
        """Publish player score update event"""
        return await self.publish_event(
            event_type=EventType.PLAYER_SCORE_UPDATE,
            source_service="scoring_service",
            league_id=league_id,
            data={
                "player_id": player_id,
                "player_name": player_name,
                "points": points,
                "stats": stats,
                "is_final": is_final
            },
            priority=2
        )

    async def publish_trade_proposal(
        self,
        league_id: str,
        trade_id: str,
        proposer_id: str,
        receiver_id: str,
        proposer_name: str,
        proposed_players: List[str],
        requested_players: List[str]
    ) -> str:
        """Publish trade proposal event"""
        return await self.publish_event(
            event_type=EventType.TRADE_PROPOSED,
            source_service="trade_service",
            league_id=league_id,
            target_users=[receiver_id],
            data={
                "trade_id": trade_id,
                "proposer_id": proposer_id,
                "proposer_name": proposer_name,
                "proposed_players": proposed_players,
                "requested_players": requested_players
            },
            priority=3
        )

    async def publish_waiver_result(
        self,
        league_id: str,
        team_id: str,
        user_id: str,
        player_id: str,
        player_name: str,
        won: bool,
        bid_amount: Optional[int] = None
    ) -> str:
        """Publish waiver claim result event"""
        event_type = EventType.WAIVER_WON if won else EventType.WAIVER_LOST

        return await self.publish_event(
            event_type=event_type,
            source_service="waiver_service",
            league_id=league_id,
            user_id=user_id,
            data={
                "team_id": team_id,
                "player_id": player_id,
                "player_name": player_name,
                "bid_amount": bid_amount,
                "won": won
            },
            priority=3
        )

    async def publish_chat_message(
        self,
        league_id: str,
        user_id: str,
        username: str,
        message_content: str,
        message_id: Optional[str] = None
    ) -> str:
        """Publish chat message event"""
        return await self.publish_event(
            event_type=EventType.CHAT_MESSAGE_SENT,
            source_service="chat_service",
            league_id=league_id,
            user_id=user_id,
            data={
                "message_id": message_id or str(uuid.uuid4()),
                "username": username,
                "content": message_content,
                "timestamp": datetime.utcnow().isoformat()
            },
            priority=4
        )

    # Private methods

    async def _process_events(self):
        """Background task to process events from queue"""
        while True:
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                await self._handle_event(event)

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing events: {e}")

    async def _handle_event(self, event: Event):
        """Handle a single event with all registered handlers"""
        try:
            handlers_to_run = []

            # Get specific handlers for this event type
            if event.event_type in self.handlers:
                handlers_to_run.extend(self.handlers[event.event_type])

            # Add global handlers
            handlers_to_run.extend(self.global_handlers)

            if not handlers_to_run:
                logger.warning(f"No handlers registered for event type: {event.event_type}")
                return

            # Run handlers concurrently
            tasks = [handler.handle(event) for handler in handlers_to_run]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Count successes and failures
            successes = sum(1 for result in results if result is True)
            failures = len(results) - successes

            if failures > 0:
                logger.warning(f"Event {event.event_id}: {successes} succeeded, {failures} failed")
                self.events_failed += failures
            else:
                logger.debug(f"Event {event.event_id} handled successfully by {successes} handlers")

            self.events_processed += 1

        except Exception as e:
            logger.error(f"Failed to handle event {event.event_id}: {e}")
            self.events_failed += 1

    async def _publish_to_redis(self, event: Event):
        """Publish event to Redis for other instances"""
        if not self.redis_client:
            return

        try:
            redis_message = json.dumps(asdict(event), default=str)
            await self.redis_client.publish(self.redis_channel, redis_message)

        except Exception as e:
            logger.error(f"Failed to publish event to Redis: {e}")

    async def _redis_subscriber(self):
        """Subscribe to Redis events from other instances"""
        if not self.redis_client:
            return

        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(self.redis_channel)

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        event_data = json.loads(message["data"])

                        # Reconstruct event object
                        event = Event(
                            event_id=event_data["event_id"],
                            event_type=EventType(event_data["event_type"]),
                            source_service=event_data["source_service"],
                            league_id=event_data.get("league_id"),
                            user_id=event_data.get("user_id"),
                            target_users=event_data.get("target_users"),
                            data=event_data.get("data"),
                            metadata=event_data.get("metadata"),
                            timestamp=datetime.fromisoformat(event_data["timestamp"]),
                            correlation_id=event_data.get("correlation_id"),
                            priority=event_data.get("priority", 5)
                        )

                        # Add to local processing queue
                        await self.event_queue.put(event)

                    except Exception as e:
                        logger.error(f"Error processing Redis event: {e}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Redis subscriber error: {e}")


# Global event publisher instance
event_publisher = EventPublisher()