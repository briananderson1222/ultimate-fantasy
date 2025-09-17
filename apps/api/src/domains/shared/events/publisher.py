"""
Event Publisher Interface.

This module defines the interface for publishing domain events,
enabling loose coupling between event producers and consumers.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import Any

from .base import AggregateEvent, DomainEvent, IntegrationEvent


class EventPublisher(ABC):
    """
    Abstract interface for publishing domain events.

    Publishers are responsible for delivering events to subscribers
    and handling event persistence, retry logic, and error handling.
    """

    @abstractmethod
    async def publish(self, event: DomainEvent) -> bool:
        """
        Publish a single domain event.

        Args:
            event: The domain event to publish

        Returns:
            True if event was successfully published, False otherwise

        Raises:
            PublishError: If event publishing fails critically
        """

    @abstractmethod
    async def publish_batch(self, events: list[DomainEvent]) -> dict[str, bool]:
        """
        Publish multiple domain events in a batch.

        Args:
            events: List of domain events to publish

        Returns:
            Dictionary mapping event IDs to success status

        Raises:
            PublishError: If batch publishing fails critically
        """

    @abstractmethod
    async def publish_integration_event(self, event: IntegrationEvent) -> bool:
        """
        Publish an integration event for cross-domain communication.

        Args:
            event: The integration event to publish

        Returns:
            True if event was successfully published, False otherwise
        """

    @abstractmethod
    async def publish_aggregate_events(self, aggregate: AggregateEvent) -> dict[str, bool]:
        """
        Publish all events from an aggregate.

        Args:
            aggregate: Aggregate event container

        Returns:
            Dictionary mapping event IDs to success status
        """

    @abstractmethod
    async def schedule_event(self, event: DomainEvent, delay_seconds: int) -> bool:
        """
        Schedule an event to be published after a delay.

        Args:
            event: The domain event to schedule
            delay_seconds: Delay in seconds before publishing

        Returns:
            True if event was successfully scheduled, False otherwise
        """


class EventPublishError(Exception):
    """Exception raised when event publishing fails."""

    def __init__(self, message: str, event_id: str | None = None, original_error: Exception | None = None):
        super().__init__(message)
        self.event_id = event_id
        self.original_error = original_error


class PublishResult:
    """Result of an event publishing operation."""

    def __init__(self, success: bool, event_id: str, error: str | None = None, retry_after: int | None = None):
        self.success = success
        self.event_id = event_id
        self.error = error
        self.retry_after = retry_after  # Seconds until retry

    def __bool__(self) -> bool:
        return self.success


class EventBuffer:
    """
    Buffer for collecting events before publishing.

    Useful for transactional scenarios where events should only
    be published after successful completion of business operations.
    """

    def __init__(self):
        self._events: list[DomainEvent] = []
        self._integration_events: list[IntegrationEvent] = []

    def add_event(self, event: DomainEvent) -> None:
        """Add an event to the buffer."""
        if isinstance(event, IntegrationEvent):
            self._integration_events.append(event)
        else:
            self._events.append(event)

    def add_events(self, events: list[DomainEvent]) -> None:
        """Add multiple events to the buffer."""
        for event in events:
            self.add_event(event)

    def get_events(self) -> list[DomainEvent]:
        """Get all buffered events."""
        return self._events.copy()

    def get_integration_events(self) -> list[IntegrationEvent]:
        """Get all buffered integration events."""
        return self._integration_events.copy()

    def get_all_events(self) -> list[DomainEvent]:
        """Get all events (both domain and integration)."""
        return self._events + self._integration_events

    def clear(self) -> None:
        """Clear all buffered events."""
        self._events.clear()
        self._integration_events.clear()

    def has_events(self) -> bool:
        """Check if buffer has any events."""
        return len(self._events) > 0 or len(self._integration_events) > 0

    def __len__(self) -> int:
        """Get total number of buffered events."""
        return len(self._events) + len(self._integration_events)


class TransactionalEventPublisher:
    """
    Publisher wrapper that supports transactional event publishing.

    Events are buffered during a transaction and only published
    when the transaction is committed.
    """

    def __init__(self, publisher: EventPublisher):
        self.publisher = publisher
        self.buffer = EventBuffer()
        self._in_transaction = False

    @asynccontextmanager
    async def transaction(self):
        """
        Context manager for transactional event publishing.

        Usage:
            async with publisher.transaction():
                # Add events during transaction
                await publisher.add_event(event)
                # Events are published when transaction exits successfully
        """
        self._in_transaction = True
        self.buffer.clear()

        try:
            yield self
            # Commit: publish all buffered events
            await self._commit()
        except Exception:
            # Rollback: clear buffer without publishing
            await self._rollback()
            raise
        finally:
            self._in_transaction = False

    async def add_event(self, event: DomainEvent) -> None:
        """
        Add event to transaction buffer or publish immediately.

        Args:
            event: Domain event to add/publish
        """
        if self._in_transaction:
            self.buffer.add_event(event)
        else:
            await self.publisher.publish(event)

    async def add_events(self, events: list[DomainEvent]) -> None:
        """
        Add multiple events to transaction buffer or publish immediately.

        Args:
            events: List of domain events to add/publish
        """
        if self._in_transaction:
            self.buffer.add_events(events)
        else:
            await self.publisher.publish_batch(events)

    async def _commit(self) -> None:
        """Commit transaction by publishing all buffered events."""
        if self.buffer.has_events():
            all_events = self.buffer.get_all_events()
            await self.publisher.publish_batch(all_events)
        self.buffer.clear()

    async def _rollback(self) -> None:
        """Rollback transaction by clearing buffer."""
        self.buffer.clear()


class EventFilter:
    """Filter for selectively publishing events based on criteria."""

    def __init__(self):
        self._domain_filters: dict[str, list[Callable[[DomainEvent], bool]]] = defaultdict(list)
        self._global_filters: list[Callable[[DomainEvent], bool]] = []

    def add_domain_filter(self, domain: str, filter_func: Callable[[DomainEvent], bool]) -> None:
        """
        Add a filter for a specific domain.

        Args:
            domain: Domain name to filter
            filter_func: Function that returns True if event should be published
        """
        self._domain_filters[domain].append(filter_func)

    def add_global_filter(self, filter_func: Callable[[DomainEvent], bool]) -> None:
        """
        Add a global filter for all events.

        Args:
            filter_func: Function that returns True if event should be published
        """
        self._global_filters.append(filter_func)

    def should_publish(self, event: DomainEvent) -> bool:
        """
        Check if event should be published based on filters.

        Args:
            event: Domain event to check

        Returns:
            True if event passes all filters, False otherwise
        """
        # Check global filters first
        for filter_func in self._global_filters:
            if not filter_func(event):
                return False

        # Check domain-specific filters
        domain_filters = self._domain_filters.get(event.domain, [])
        for filter_func in domain_filters:
            if not filter_func(event):
                return False

        return True


class FilteredEventPublisher:
    """Publisher wrapper that applies filters before publishing."""

    def __init__(self, publisher: EventPublisher, event_filter: EventFilter):
        self.publisher = publisher
        self.filter = event_filter

    async def publish(self, event: DomainEvent) -> bool:
        """Publish event if it passes filters."""
        if self.filter.should_publish(event):
            return await self.publisher.publish(event)
        return True  # Filtered events are considered "successfully" handled

    async def publish_batch(self, events: list[DomainEvent]) -> dict[str, bool]:
        """Publish batch of events, filtering as needed."""
        filtered_events = [event for event in events if self.filter.should_publish(event)]

        if not filtered_events:
            # All events filtered - return success for all
            return {event.event_id: True for event in events}

        results = await self.publisher.publish_batch(filtered_events)

        # Add filtered events as successful
        for event in events:
            if event.event_id not in results:
                results[event.event_id] = True

        return results


# Convenient publisher interface for domain services
class DomainEventPublisher:
    """
    Simplified publisher interface for domain services.

    Provides convenient methods for publishing domain-specific events.
    """

    def __init__(self, publisher: EventPublisher, domain: str):
        self.publisher = publisher
        self.domain = domain

    async def publish_event(self, event_type: str, aggregate_id: str, data: dict[str, Any]) -> bool:
        """
        Publish a domain event.

        Args:
            event_type: Type of the event
            aggregate_id: ID of the aggregate that generated the event
            data: Event data

        Returns:
            True if successful, False otherwise
        """
        from .base import DomainEvent

        event = DomainEvent(aggregate_id, self.domain, event_type, data)
        return await self.publisher.publish(event)

    async def publish_integration_event(
        self,
        event_type: str,
        aggregate_id: str,
        data: dict[str, Any],
        target_domains: list[str] | None = None
    ) -> bool:
        """
        Publish an integration event for cross-domain communication.

        Args:
            event_type: Type of the event
            aggregate_id: ID of the aggregate that generated the event
            data: Event data
            target_domains: Target domains (None means all domains)

        Returns:
            True if successful, False otherwise
        """
        event = IntegrationEvent(aggregate_id, self.domain, event_type, data, target_domains)
        return await self.publisher.publish_integration_event(event)

    async def publish_aggregate_events(self, aggregate: AggregateEvent) -> dict[str, bool]:
        """
        Publish all events from an aggregate.

        Args:
            aggregate: Aggregate event container

        Returns:
            Dictionary mapping event IDs to success status
        """
        return await self.publisher.publish_aggregate_events(aggregate)
