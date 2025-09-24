"""
Redis pub/sub event system for cross-service real-time communication.

Provides comprehensive event distribution including:
- Publish/subscribe pattern for decoupled messaging
- Event routing and filtering capabilities
- Reliable delivery with retry mechanisms
- Event serialization and deserialization
- Performance monitoring and metrics
- Dead letter queue for failed events
- Multi-instance scaling support
- Integration with WebSocket connection manager
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum
from dataclasses import dataclass, asdict
from uuid import uuid4

import redis.asyncio as redis
from redis.asyncio import Redis

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging
    get_logger = logging.getLogger  # type: ignore[assignment]

logger = get_logger(__name__)


class EventSystemError(Exception):
    """Redis pub/sub event system errors."""
    pass


class EventType(Enum):
    """Types of events that can be published."""
    # Draft events
    DRAFT_STARTED = "draft.started"
    DRAFT_PICK_MADE = "draft.pick_made"
    DRAFT_TIMER_UPDATE = "draft.timer_update"
    DRAFT_COMPLETED = "draft.completed"
    DRAFT_PAUSED = "draft.paused"
    DRAFT_RESUMED = "draft.resumed"

    # Trade events
    TRADE_PROPOSED = "trade.proposed"
    TRADE_ACCEPTED = "trade.accepted"
    TRADE_REJECTED = "trade.rejected"
    TRADE_EXECUTED = "trade.executed"
    TRADE_VETOED = "trade.vetoed"

    # Score events
    SCORE_UPDATED = "score.updated"
    GAME_STARTED = "game.started"
    GAME_COMPLETED = "game.completed"
    PLAYER_STATS_UPDATED = "player.stats_updated"

    # League events
    LEAGUE_UPDATED = "league.updated"
    ROSTER_CHANGED = "roster.changed"
    WAIVER_PROCESSED = "waiver.processed"

    # User events
    USER_NOTIFICATION = "user.notification"
    USER_ACTIVITY = "user.activity"

    # System events
    SYSTEM_MAINTENANCE = "system.maintenance"
    SYSTEM_ALERT = "system.alert"


@dataclass
class Event:
    """Event data structure."""

    event_id: str
    event_type: EventType
    source: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: datetime
    ttl_seconds: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class EventFilter:
    """Filter for event subscriptions."""

    event_types: Optional[List[EventType]] = None
    source_patterns: Optional[List[str]] = None
    data_filters: Optional[Dict[str, Any]] = None
    exclude_sources: Optional[List[str]] = None


@dataclass
class SubscriptionInfo:
    """Information about an event subscription."""

    subscription_id: str
    handler: Callable
    filter: EventFilter
    created_at: datetime
    last_processed: Optional[datetime]
    total_processed: int
    error_count: int


class RedisEventSystem:
    """Redis-based pub/sub event system."""

    def __init__(self,
                 redis_url: str = "redis://localhost:6379/0",
                 channel_prefix: str = "fantasy_events",
                 dead_letter_ttl: int = 86400):  # 24 hours

        self.redis_url = redis_url
        self.channel_prefix = channel_prefix
        self.dead_letter_ttl = dead_letter_ttl

        # Redis connections
        self.redis_client: Optional[Redis] = None
        self.redis_subscriber: Optional[Redis] = None

        # Subscriptions
        self.subscriptions: Dict[str, SubscriptionInfo] = {}
        self.subscription_tasks: Dict[str, asyncio.Task] = {}

        # State
        self.is_running = False
        self.subscriber_task: Optional[asyncio.Task] = None

        # Statistics
        self.stats = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0,
            "dead_letter_events": 0,
            "active_subscriptions": 0,
        }

    async def start(self):
        """Start the event system."""
        try:
            # Initialize Redis connections
            self.redis_client = redis.from_url(self.redis_url)
            self.redis_subscriber = redis.from_url(self.redis_url)

            # Test connections
            await self.redis_client.ping()
            await self.redis_subscriber.ping()

            self.is_running = True

            # Start subscriber task
            self.subscriber_task = asyncio.create_task(self._subscriber_loop())

            logger.info(f"Redis event system started (prefix: {self.channel_prefix})")

        except Exception as e:
            logger.error(f"Failed to start Redis event system: {e}")
            raise EventSystemError(f"Failed to start event system: {e}")

    async def stop(self):
        """Stop the event system."""
        try:
            self.is_running = False

            # Cancel subscriber task
            if self.subscriber_task:
                self.subscriber_task.cancel()
                try:
                    await self.subscriber_task
                except asyncio.CancelledError:
                    pass

            # Cancel subscription tasks
            for task in self.subscription_tasks.values():
                task.cancel()

            for task in self.subscription_tasks.values():
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Close Redis connections
            if self.redis_client:
                await self.redis_client.close()
            if self.redis_subscriber:
                await self.redis_subscriber.close()

            logger.info("Redis event system stopped")

        except Exception as e:
            logger.error(f"Error stopping Redis event system: {e}")

    async def publish_event(self,
                           event_type: EventType,
                           data: Dict[str, Any],
                           source: str = "api",
                           metadata: Optional[Dict[str, Any]] = None,
                           ttl_seconds: Optional[int] = None) -> str:
        """
        Publish an event to the system.

        Args:
            event_type: Type of event
            data: Event data payload
            source: Source identifier
            metadata: Optional metadata
            ttl_seconds: Optional time-to-live

        Returns:
            str: Event ID
        """
        try:
            if not self.is_running or not self.redis_client:
                raise EventSystemError("Event system not running")

            # Create event
            event = Event(
                event_id=str(uuid4()),
                event_type=event_type,
                source=source,
                data=data,
                metadata=metadata or {},
                timestamp=datetime.utcnow(),
                ttl_seconds=ttl_seconds,
                retry_count=0,
            )

            # Serialize event
            event_data = self._serialize_event(event)

            # Publish to main channel
            main_channel = f"{self.channel_prefix}:all"
            await self.redis_client.publish(main_channel, event_data)

            # Publish to type-specific channel
            type_channel = f"{self.channel_prefix}:{event_type.value}"
            await self.redis_client.publish(type_channel, event_data)

            # Store event for replay if TTL specified
            if ttl_seconds:
                event_key = f"{self.channel_prefix}:events:{event.event_id}"
                await self.redis_client.setex(event_key, ttl_seconds, event_data)

            # Update statistics
            self.stats["events_published"] += 1

            logger.debug(
                f"Event published",
                extra={
                    "event_id": event.event_id,
                    "event_type": event_type.value,
                    "source": source,
                }
            )

            return event.event_id

        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            raise EventSystemError(f"Failed to publish event: {e}")

    async def subscribe(self,
                       handler: Callable,
                       event_filter: Optional[EventFilter] = None,
                       subscription_id: Optional[str] = None) -> str:
        """
        Subscribe to events with optional filtering.

        Args:
            handler: Async function to handle events
            event_filter: Optional filter for events
            subscription_id: Optional custom subscription ID

        Returns:
            str: Subscription ID
        """
        try:
            subscription_id = subscription_id or str(uuid4())

            if subscription_id in self.subscriptions:
                raise EventSystemError(f"Subscription {subscription_id} already exists")

            # Create subscription info
            subscription_info = SubscriptionInfo(
                subscription_id=subscription_id,
                handler=handler,
                filter=event_filter or EventFilter(),
                created_at=datetime.utcnow(),
                last_processed=None,
                total_processed=0,
                error_count=0,
            )

            self.subscriptions[subscription_id] = subscription_info
            self.stats["active_subscriptions"] = len(self.subscriptions)

            logger.info(f"Event subscription created: {subscription_id}")

            return subscription_id

        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            raise EventSystemError(f"Failed to create subscription: {e}")

    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Remove an event subscription.

        Args:
            subscription_id: Subscription to remove

        Returns:
            bool: True if subscription was removed
        """
        try:
            if subscription_id not in self.subscriptions:
                return False

            # Cancel subscription task if running
            if subscription_id in self.subscription_tasks:
                task = self.subscription_tasks[subscription_id]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del self.subscription_tasks[subscription_id]

            # Remove subscription
            del self.subscriptions[subscription_id]
            self.stats["active_subscriptions"] = len(self.subscriptions)

            logger.info(f"Event subscription removed: {subscription_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove subscription {subscription_id}: {e}")
            return False

    async def get_event_history(self,
                               event_type: Optional[EventType] = None,
                               source: Optional[str] = None,
                               since: Optional[datetime] = None,
                               limit: int = 100) -> List[Event]:
        """
        Get historical events (only available for events with TTL).

        Args:
            event_type: Optional event type filter
            source: Optional source filter
            since: Optional time filter
            limit: Maximum number of events

        Returns:
            List[Event]: Historical events
        """
        try:
            if not self.redis_client:
                return []

            # Get all stored events
            pattern = f"{self.channel_prefix}:events:*"
            event_keys = await self.redis_client.keys(pattern)

            events = []
            for key in event_keys[:limit]:  # Limit to prevent memory issues
                try:
                    event_data = await self.redis_client.get(key)
                    if event_data:
                        event = self._deserialize_event(event_data)

                        # Apply filters
                        if event_type and event.event_type != event_type:
                            continue
                        if source and event.source != source:
                            continue
                        if since and event.timestamp < since:
                            continue

                        events.append(event)

                except Exception as e:
                    logger.warning(f"Failed to deserialize event from {key}: {e}")
                    continue

            # Sort by timestamp (newest first)
            events.sort(key=lambda e: e.timestamp, reverse=True)

            return events[:limit]

        except Exception as e:
            logger.error(f"Failed to get event history: {e}")
            return []

    async def replay_events(self,
                           subscription_id: str,
                           since: Optional[datetime] = None) -> int:
        """
        Replay historical events to a subscription.

        Args:
            subscription_id: Target subscription
            since: Optional time filter

        Returns:
            int: Number of events replayed
        """
        try:
            subscription = self.subscriptions.get(subscription_id)
            if not subscription:
                raise EventSystemError(f"Subscription {subscription_id} not found")

            # Get historical events
            events = await self.get_event_history(since=since)

            replayed = 0
            for event in events:
                try:
                    if self._should_process_event(event, subscription.filter):
                        await subscription.handler(event)
                        replayed += 1
                except Exception as e:
                    logger.error(f"Error replaying event {event.event_id}: {e}")

            logger.info(f"Replayed {replayed} events to subscription {subscription_id}")
            return replayed

        except Exception as e:
            logger.error(f"Failed to replay events: {e}")
            return 0

    # Private methods

    async def _subscriber_loop(self):
        """Main subscriber loop."""
        try:
            pubsub = self.redis_subscriber.pubsub()

            # Subscribe to all events channel
            main_channel = f"{self.channel_prefix}:all"
            await pubsub.subscribe(main_channel)

            logger.info(f"Subscribed to Redis channel: {main_channel}")

            async for message in pubsub.listen():
                if not self.is_running:
                    break

                if message["type"] == "message":
                    try:
                        event_data = message["data"]
                        event = self._deserialize_event(event_data)
                        await self._process_event(event)
                    except Exception as e:
                        logger.error(f"Error processing event: {e}")

        except asyncio.CancelledError:
            logger.info("Subscriber loop cancelled")
        except Exception as e:
            logger.error(f"Subscriber loop error: {e}")

    async def _process_event(self, event: Event):
        """Process an event for all matching subscriptions."""
        try:
            # Check if event is expired
            if event.ttl_seconds:
                age = (datetime.utcnow() - event.timestamp).total_seconds()
                if age > event.ttl_seconds:
                    logger.debug(f"Event {event.event_id} expired, skipping")
                    return

            # Process for each subscription
            for subscription_id, subscription in self.subscriptions.items():
                try:
                    if self._should_process_event(event, subscription.filter):
                        # Process in background task
                        task = asyncio.create_task(
                            self._handle_event_for_subscription(event, subscription)
                        )
                        # Don't wait for completion to avoid blocking other subscriptions

                except Exception as e:
                    logger.error(f"Error processing event for subscription {subscription_id}: {e}")

            self.stats["events_processed"] += 1

        except Exception as e:
            logger.error(f"Error processing event {event.event_id}: {e}")

    async def _handle_event_for_subscription(self, event: Event, subscription: SubscriptionInfo):
        """Handle an event for a specific subscription."""
        try:
            await subscription.handler(event)

            # Update subscription stats
            subscription.last_processed = datetime.utcnow()
            subscription.total_processed += 1

        except Exception as e:
            logger.error(f"Event handler error for subscription {subscription.subscription_id}: {e}")
            subscription.error_count += 1
            self.stats["events_failed"] += 1

            # Send to dead letter queue if too many failures
            if event.retry_count >= event.max_retries:
                await self._send_to_dead_letter_queue(event, str(e))
            else:
                # Retry with exponential backoff
                retry_delay = 2 ** event.retry_count
                event.retry_count += 1

                await asyncio.sleep(retry_delay)
                await self._handle_event_for_subscription(event, subscription)

    def _should_process_event(self, event: Event, event_filter: EventFilter) -> bool:
        """Check if an event matches a subscription filter."""
        try:
            # Check event types
            if (event_filter.event_types and
                event.event_type not in event_filter.event_types):
                return False

            # Check source patterns
            if event_filter.source_patterns:
                match = False
                for pattern in event_filter.source_patterns:
                    if pattern in event.source:
                        match = True
                        break
                if not match:
                    return False

            # Check excluded sources
            if (event_filter.exclude_sources and
                event.source in event_filter.exclude_sources):
                return False

            # Check data filters
            if event_filter.data_filters:
                for key, expected_value in event_filter.data_filters.items():
                    if key not in event.data or event.data[key] != expected_value:
                        return False

            return True

        except Exception as e:
            logger.error(f"Error checking event filter: {e}")
            return False

    def _serialize_event(self, event: Event) -> str:
        """Serialize an event to JSON."""
        try:
            event_dict = asdict(event)
            event_dict["event_type"] = event.event_type.value
            event_dict["timestamp"] = event.timestamp.isoformat()
            return json.dumps(event_dict)
        except Exception as e:
            logger.error(f"Failed to serialize event: {e}")
            raise EventSystemError(f"Failed to serialize event: {e}")

    def _deserialize_event(self, event_data: Union[str, bytes]) -> Event:
        """Deserialize an event from JSON."""
        try:
            if isinstance(event_data, bytes):
                event_data = event_data.decode('utf-8')

            event_dict = json.loads(event_data)

            # Convert timestamp back to datetime
            event_dict["timestamp"] = datetime.fromisoformat(event_dict["timestamp"])

            # Convert event_type back to enum
            event_dict["event_type"] = EventType(event_dict["event_type"])

            return Event(**event_dict)

        except Exception as e:
            logger.error(f"Failed to deserialize event: {e}")
            raise EventSystemError(f"Failed to deserialize event: {e}")

    async def _send_to_dead_letter_queue(self, event: Event, error_message: str):
        """Send failed event to dead letter queue."""
        try:
            if not self.redis_client:
                return

            dlq_key = f"{self.channel_prefix}:dlq:{event.event_id}"
            dlq_data = {
                "event": asdict(event),
                "error": error_message,
                "failed_at": datetime.utcnow().isoformat(),
            }

            await self.redis_client.setex(
                dlq_key,
                self.dead_letter_ttl,
                json.dumps(dlq_data)
            )

            self.stats["dead_letter_events"] += 1

            logger.warning(
                f"Event sent to dead letter queue",
                extra={
                    "event_id": event.event_id,
                    "error": error_message,
                }
            )

        except Exception as e:
            logger.error(f"Failed to send event to dead letter queue: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get event system statistics."""
        return {
            **self.stats,
            "subscription_details": {
                sub_id: {
                    "total_processed": sub.total_processed,
                    "error_count": sub.error_count,
                    "last_processed": sub.last_processed.isoformat() if sub.last_processed else None,
                }
                for sub_id, sub in self.subscriptions.items()
            }
        }


# Global event system instance
_event_system: Optional[RedisEventSystem] = None


def get_event_system() -> RedisEventSystem:
    """Get the global Redis event system."""
    global _event_system
    if _event_system is None:
        _event_system = RedisEventSystem()
    return _event_system


async def initialize_event_system(redis_url: Optional[str] = None):
    """Initialize and start the event system."""
    global _event_system
    if redis_url:
        _event_system = RedisEventSystem(redis_url=redis_url)
    else:
        _event_system = get_event_system()

    await _event_system.start()
    return _event_system


async def shutdown_event_system():
    """Shutdown the event system."""
    global _event_system
    if _event_system:
        await _event_system.stop()
        _event_system = None