"""
Event Dispatcher Implementation.

This module provides the concrete implementation of event publishing and
subscribing, enabling event-driven communication between domains.
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from contextlib import asynccontextmanager
from typing import Any

from domains.shared.events.base import AggregateEvent, DomainEvent, IntegrationEvent
from domains.shared.events.publisher import (
    EventPublisher,
    EventPublishError,
)
from domains.shared.events.subscriber import (
    DeadLetterQueue,
    EventHandler,
    EventSubscriber,
    EventSubscriptionError,
    HandlerRegistry,
    HandlerResult,
    RetryPolicy,
    SubscriptionConfig,
)

logger = logging.getLogger(__name__)


class InMemoryEventDispatcher(EventPublisher, EventSubscriber):
    """
    In-memory implementation of event dispatcher.

    Provides both publishing and subscribing capabilities for development
    and testing. For production, consider using external message brokers.
    """

    def __init__(
        self,
        max_retry_attempts: int = 3,
        retry_delay_seconds: float = 1.0,
        enable_dead_letter: bool = True,
        max_concurrent_handlers: int = 10
    ):
        """
        Initialize the event dispatcher.

        Args:
            max_retry_attempts: Maximum retry attempts for failed handlers
            retry_delay_seconds: Initial delay between retries
            enable_dead_letter: Whether to use dead letter queue
            max_concurrent_handlers: Maximum concurrent handler executions
        """
        self.handler_registry = HandlerRegistry()
        self.retry_policy = RetryPolicy(max_retry_attempts, retry_delay_seconds)
        self.dead_letter_queue = DeadLetterQueue() if enable_dead_letter else None

        # Event storage for persistence
        self._published_events: deque = deque(maxlen=1000)  # Keep last 1000 events
        self._failed_events: list[dict[str, Any]] = []

        # Concurrency control
        self._handler_semaphore = asyncio.Semaphore(max_concurrent_handlers)
        self._processing_events: set[str] = set()

        # Metrics
        self._metrics = {
            "events_published": 0,
            "events_processed": 0,
            "handlers_executed": 0,
            "handlers_failed": 0,
            "retries_attempted": 0,
            "dead_letter_events": 0,
        }

        # Scheduled events (for delayed publishing)
        self._scheduled_events: dict[str, dict[str, Any]] = {}

    # Publisher interface implementation

    async def publish(self, event: DomainEvent) -> bool:
        """Publish a single domain event."""
        try:
            event.mark_as_processing()
            self._published_events.append(event)
            self._metrics["events_published"] += 1

            # Handle the event immediately for in-memory processing
            results = await self.handle_event(event)

            # Consider successful if at least one handler succeeded or no handlers
            success = not results or any(results.values())

            if success:
                event.mark_as_completed()
            else:
                event.mark_as_failed()

            return success

        except Exception as e:
            logger.error(f"Failed to publish event {event.event_id}: {e}")
            event.mark_as_failed()
            raise EventPublishError(f"Publishing failed: {e}", event.event_id, e)

    async def publish_batch(self, events: list[DomainEvent]) -> dict[str, bool]:
        """Publish multiple domain events in a batch."""
        results = {}

        for event in events:
            try:
                success = await self.publish(event)
                results[event.event_id] = success
            except EventPublishError:
                results[event.event_id] = False

        return results

    async def publish_integration_event(self, event: IntegrationEvent) -> bool:
        """Publish an integration event for cross-domain communication."""
        # Integration events are handled the same as domain events in this implementation
        return await self.publish(event)

    async def publish_aggregate_events(self, aggregate: AggregateEvent) -> dict[str, bool]:
        """Publish all events from an aggregate."""
        events = aggregate.get_events()
        results = await self.publish_batch(events)

        # Clear events from aggregate after publishing
        aggregate.clear_events()

        return results

    async def schedule_event(self, event: DomainEvent, delay_seconds: int) -> bool:
        """Schedule an event to be published after a delay."""
        publish_time = time.time() + delay_seconds

        self._scheduled_events[event.event_id] = {
            "event": event,
            "publish_time": publish_time,
        }

        # Start background task to publish the event
        asyncio.create_task(self._publish_scheduled_event(event, delay_seconds))

        return True

    async def _publish_scheduled_event(self, event: DomainEvent, delay_seconds: int) -> None:
        """Background task to publish a scheduled event."""
        await asyncio.sleep(delay_seconds)

        # Remove from scheduled events
        self._scheduled_events.pop(event.event_id, None)

        # Publish the event
        await self.publish(event)

    # Subscriber interface implementation

    async def subscribe(
        self,
        subscription_config: SubscriptionConfig,
        handler: EventHandler
    ) -> str:
        """Subscribe to events with a handler."""
        try:
            self.handler_registry.register_handler(subscription_config, handler)
            logger.info(f"Registered subscription {subscription_config.subscription_id}")
            return subscription_config.subscription_id

        except Exception as e:
            logger.error(f"Failed to register subscription {subscription_config.subscription_id}: {e}")
            raise EventSubscriptionError(f"Subscription failed: {e}", subscription_config.subscription_id)

    async def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a subscription."""
        success = self.handler_registry.unregister_handler(subscription_id)

        if success:
            logger.info(f"Unregistered subscription {subscription_id}")
        else:
            logger.warning(f"Subscription {subscription_id} not found")

        return success

    async def handle_event(self, event: DomainEvent) -> dict[str, bool]:
        """Handle an incoming event by notifying all matching subscribers."""
        # Prevent duplicate processing
        if event.event_id in self._processing_events:
            logger.warning(f"Event {event.event_id} is already being processed")
            return {}

        self._processing_events.add(event.event_id)

        try:
            self._metrics["events_processed"] += 1
            matching_handlers = self.handler_registry.get_matching_handlers(event)

            if not matching_handlers:
                logger.debug(f"No handlers found for event {event.event_id}")
                return {}

            logger.debug(f"Found {len(matching_handlers)} handlers for event {event.event_id}")

            # Execute handlers concurrently with semaphore control
            tasks = []
            for handler_info in matching_handlers:
                task = asyncio.create_task(
                    self._execute_handler_with_retry(event, handler_info)
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            handler_results = {}
            for i, result in enumerate(results):
                config = matching_handlers[i]["config"]
                subscription_id = config.subscription_id

                if isinstance(result, Exception):
                    logger.error(f"Handler {subscription_id} failed with exception: {result}")
                    handler_results[subscription_id] = False
                elif isinstance(result, HandlerResult):
                    handler_results[subscription_id] = result.success
                else:
                    handler_results[subscription_id] = bool(result)

            return handler_results

        finally:
            self._processing_events.discard(event.event_id)

    async def _execute_handler_with_retry(
        self,
        event: DomainEvent,
        handler_info: dict[str, Any]
    ) -> HandlerResult:
        """Execute a handler with retry logic."""
        config = handler_info["config"]
        handler = handler_info["handler"]
        subscription_id = config.subscription_id

        async with self._handler_semaphore:
            for attempt in range(1, config.max_retry_attempts + 1):
                try:
                    start_time = time.time()

                    # Execute handler with timeout
                    success = await asyncio.wait_for(
                        handler(event),
                        timeout=config.timeout_seconds
                    )

                    execution_time = (time.time() - start_time) * 1000  # Convert to ms
                    self._metrics["handlers_executed"] += 1

                    return HandlerResult(
                        success=success,
                        subscription_id=subscription_id,
                        event_id=event.event_id,
                        execution_time_ms=execution_time
                    )

                except TimeoutError:
                    error_msg = f"Handler timeout after {config.timeout_seconds} seconds"
                    logger.warning(f"Handler {subscription_id} timed out on attempt {attempt}: {error_msg}")

                except Exception as e:
                    error_msg = f"Handler error: {e}"
                    logger.warning(f"Handler {subscription_id} failed on attempt {attempt}: {error_msg}")

                # Check if we should retry
                if attempt < config.max_retry_attempts:
                    self._metrics["retries_attempted"] += 1
                    delay = self.retry_policy.get_delay(attempt)
                    await asyncio.sleep(delay)
                else:
                    # Final failure - add to dead letter queue
                    self._metrics["handlers_failed"] += 1

                    if self.dead_letter_queue and config.dead_letter_enabled:
                        await self.dead_letter_queue.add_failed_event(
                            event, subscription_id, error_msg, attempt
                        )
                        self._metrics["dead_letter_events"] += 1

            # All retries exhausted
            return HandlerResult(
                success=False,
                subscription_id=subscription_id,
                event_id=event.event_id,
                error=f"Failed after {config.max_retry_attempts} attempts"
            )

    async def get_subscriptions(self) -> list[SubscriptionConfig]:
        """Get all active subscriptions."""
        return self.handler_registry.get_all_configs()

    # Management and monitoring methods

    def get_metrics(self) -> dict[str, Any]:
        """Get dispatcher metrics."""
        return {
            **self._metrics,
            "active_subscriptions": len(self.handler_registry._handlers),
            "scheduled_events": len(self._scheduled_events),
            "published_events_count": len(self._published_events),
            "processing_events": len(self._processing_events),
        }

    def get_published_events(self, limit: int = 100) -> list[DomainEvent]:
        """Get recently published events."""
        events = list(self._published_events)
        return events[-limit:] if len(events) > limit else events

    async def get_dead_letter_events(self) -> list[dict[str, Any]]:
        """Get events in the dead letter queue."""
        if self.dead_letter_queue:
            return await self.dead_letter_queue.get_failed_events()
        return []

    async def clear_dead_letter_queue(self) -> None:
        """Clear the dead letter queue."""
        if self.dead_letter_queue:
            await self.dead_letter_queue.clear_failed_events()

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self._metrics = {
            "events_published": 0,
            "events_processed": 0,
            "handlers_executed": 0,
            "handlers_failed": 0,
            "retries_attempted": 0,
            "dead_letter_events": 0,
        }

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on the dispatcher."""
        try:
            # Create a test event
            test_event = DomainEvent("test", "system", "health_check", {})

            # Try to publish it (this will test the basic flow)
            start_time = time.time()
            await self.publish(test_event)
            response_time = (time.time() - start_time) * 1000

            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "metrics": self.get_metrics(),
                "dead_letter_queue_size": len(await self.get_dead_letter_events()),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "metrics": self.get_metrics(),
            }


# Global dispatcher instance
_dispatcher: InMemoryEventDispatcher | None = None


def get_event_dispatcher() -> InMemoryEventDispatcher:
    """
    Get the global event dispatcher instance.

    Returns:
        InMemoryEventDispatcher instance

    Raises:
        RuntimeError: If dispatcher not initialized
    """
    global _dispatcher
    if _dispatcher is None:
        raise RuntimeError("Event dispatcher not initialized. Call initialize_dispatcher() first.")
    return _dispatcher


def initialize_dispatcher(**kwargs) -> InMemoryEventDispatcher:
    """
    Initialize the global event dispatcher.

    Args:
        **kwargs: Configuration parameters for the dispatcher

    Returns:
        InMemoryEventDispatcher instance
    """
    global _dispatcher
    _dispatcher = InMemoryEventDispatcher(**kwargs)
    return _dispatcher


def reset_dispatcher() -> None:
    """Reset the global event dispatcher (useful for testing)."""
    global _dispatcher
    _dispatcher = None


@asynccontextmanager
async def dispatcher_context(**kwargs):
    """
    Context manager for event dispatcher lifecycle.

    Usage:
        async with dispatcher_context() as dispatcher:
            # Use dispatcher
            pass
    """
    dispatcher = initialize_dispatcher(**kwargs)
    try:
        yield dispatcher
    finally:
        reset_dispatcher()


# Convenience functions for common operations

async def publish_event(
    domain: str,
    event_type: str,
    aggregate_id: str,
    data: dict[str, Any]
) -> bool:
    """
    Convenience function to publish a domain event.

    Args:
        domain: Domain name
        event_type: Type of event
        aggregate_id: ID of the aggregate
        data: Event data

    Returns:
        True if successful, False otherwise
    """
    dispatcher = get_event_dispatcher()
    event = DomainEvent(aggregate_id, domain, event_type, data)
    return await dispatcher.publish(event)


async def publish_integration_event(
    domain: str,
    event_type: str,
    aggregate_id: str,
    data: dict[str, Any],
    target_domains: list[str] | None = None
) -> bool:
    """
    Convenience function to publish an integration event.

    Args:
        domain: Source domain name
        event_type: Type of event
        aggregate_id: ID of the aggregate
        data: Event data
        target_domains: Target domains

    Returns:
        True if successful, False otherwise
    """
    dispatcher = get_event_dispatcher()
    event = IntegrationEvent(aggregate_id, domain, event_type, data, target_domains)
    return await dispatcher.publish_integration_event(event)


async def subscribe_to_events(
    subscription_id: str,
    event_types: list[str],
    handler: EventHandler
) -> str:
    """
    Convenience function to subscribe to specific event types.

    Args:
        subscription_id: Unique subscription ID
        event_types: List of event types to subscribe to
        handler: Event handler function

    Returns:
        Subscription ID
    """
    from domains.shared.events.subscriber import SubscriptionConfig, SubscriptionType

    dispatcher = get_event_dispatcher()
    config = SubscriptionConfig(
        subscription_id=subscription_id,
        subscription_type=SubscriptionType.EVENT_TYPE,
        filter_criteria={"event_types": event_types}
    )

    return await dispatcher.subscribe(config, handler)
