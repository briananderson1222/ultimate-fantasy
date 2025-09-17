"""
Event Subscriber Interface.

This module defines the interface for subscribing to and handling domain events,
enabling event-driven architecture and loose coupling between domains.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .base import DomainEvent, IntegrationEvent


class SubscriptionType(Enum):
    """Type of event subscription."""
    DOMAIN = "domain"              # Subscribe to all events from a domain
    EVENT_TYPE = "event_type"      # Subscribe to specific event types
    AGGREGATE = "aggregate"        # Subscribe to events from specific aggregates
    PATTERN = "pattern"           # Subscribe using pattern matching


class HandlerPriority(Enum):
    """Priority levels for event handlers."""
    LOWEST = 0
    LOW = 25
    NORMAL = 50
    HIGH = 75
    HIGHEST = 100


@dataclass
class SubscriptionConfig:
    """Configuration for event subscriptions."""
    subscription_id: str
    subscription_type: SubscriptionType
    filter_criteria: dict[str, Any]
    handler_priority: HandlerPriority = HandlerPriority.NORMAL
    max_retry_attempts: int = 3
    retry_delay_seconds: int = 1
    dead_letter_enabled: bool = True
    batch_size: int = 1
    concurrent_handlers: int = 1
    timeout_seconds: int = 30


EventHandler = Callable[[DomainEvent], Awaitable[bool]]


class EventSubscriber(ABC):
    """
    Abstract interface for subscribing to domain events.

    Subscribers register handlers for specific events and receive
    notifications when matching events are published.
    """

    @abstractmethod
    async def subscribe(
        self,
        subscription_config: SubscriptionConfig,
        handler: EventHandler
    ) -> str:
        """
        Subscribe to events with a handler.

        Args:
            subscription_config: Configuration for the subscription
            handler: Async function to handle matching events

        Returns:
            Subscription ID for managing the subscription

        Raises:
            SubscriptionError: If subscription fails
        """

    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Remove a subscription.

        Args:
            subscription_id: ID of subscription to remove

        Returns:
            True if subscription was removed, False if not found
        """

    @abstractmethod
    async def handle_event(self, event: DomainEvent) -> dict[str, bool]:
        """
        Handle an incoming event by notifying all matching subscribers.

        Args:
            event: Domain event to handle

        Returns:
            Dictionary mapping subscription IDs to success status
        """

    @abstractmethod
    async def get_subscriptions(self) -> list[SubscriptionConfig]:
        """
        Get all active subscriptions.

        Returns:
            List of subscription configurations
        """


class EventSubscriptionError(Exception):
    """Exception raised when event subscription operations fail."""

    def __init__(self, message: str, subscription_id: str | None = None):
        super().__init__(message)
        self.subscription_id = subscription_id


class HandlerResult:
    """Result of an event handler execution."""

    def __init__(
        self,
        success: bool,
        subscription_id: str,
        event_id: str,
        error: str | None = None,
        execution_time_ms: float | None = None
    ):
        self.success = success
        self.subscription_id = subscription_id
        self.event_id = event_id
        self.error = error
        self.execution_time_ms = execution_time_ms

    def __bool__(self) -> bool:
        return self.success


class EventMatcher:
    """Utility for matching events against subscription criteria."""

    @staticmethod
    def matches_domain(event: DomainEvent, domain: str) -> bool:
        """Check if event matches a domain."""
        return event.domain == domain

    @staticmethod
    def matches_event_type(event: DomainEvent, event_types: str | list[str]) -> bool:
        """Check if event matches specific event types."""
        if isinstance(event_types, str):
            return event.event_type == event_types
        return event.event_type in event_types

    @staticmethod
    def matches_aggregate(event: DomainEvent, aggregate_ids: str | list[str]) -> bool:
        """Check if event matches specific aggregates."""
        if isinstance(aggregate_ids, str):
            return event.aggregate_id == aggregate_ids
        return event.aggregate_id in aggregate_ids

    @staticmethod
    def matches_pattern(event: DomainEvent, pattern: str) -> bool:
        """Check if event matches a pattern (simple wildcard matching)."""
        import fnmatch
        return fnmatch.fnmatch(event.event_type, pattern)

    @staticmethod
    def matches_criteria(event: DomainEvent, config: SubscriptionConfig) -> bool:
        """Check if event matches subscription criteria."""
        criteria = config.filter_criteria

        if config.subscription_type == SubscriptionType.DOMAIN:
            return EventMatcher.matches_domain(event, criteria.get("domain", ""))

        elif config.subscription_type == SubscriptionType.EVENT_TYPE:
            return EventMatcher.matches_event_type(event, criteria.get("event_types", []))

        elif config.subscription_type == SubscriptionType.AGGREGATE:
            return EventMatcher.matches_aggregate(event, criteria.get("aggregate_ids", []))

        elif config.subscription_type == SubscriptionType.PATTERN:
            return EventMatcher.matches_pattern(event, criteria.get("pattern", ""))

        return False


class RetryPolicy:
    """Policy for retrying failed event handlers."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    def get_delay(self, attempt: int) -> float:
        """Get delay for a specific retry attempt."""
        if attempt <= 0:
            return 0.0

        delay = self.initial_delay * (self.exponential_base ** (attempt - 1))
        return min(delay, self.max_delay)

    def should_retry(self, attempt: int) -> bool:
        """Check if should retry after a failed attempt."""
        return attempt < self.max_attempts


class DeadLetterQueue:
    """Queue for events that failed all retry attempts."""

    def __init__(self):
        self._failed_events: list[dict[str, Any]] = []

    async def add_failed_event(
        self,
        event: DomainEvent,
        subscription_id: str,
        error: str,
        attempts: int
    ) -> None:
        """Add a failed event to the dead letter queue."""
        self._failed_events.append({
            "event": event.to_dict(),
            "subscription_id": subscription_id,
            "error": error,
            "attempts": attempts,
            "failed_at": event.timestamp.isoformat(),
        })

    async def get_failed_events(self) -> list[dict[str, Any]]:
        """Get all failed events."""
        return self._failed_events.copy()

    async def clear_failed_events(self) -> None:
        """Clear all failed events."""
        self._failed_events.clear()

    def __len__(self) -> int:
        """Get number of failed events."""
        return len(self._failed_events)


class HandlerRegistry:
    """Registry for managing event handlers and subscriptions."""

    def __init__(self):
        self._handlers: dict[str, dict[str, Any]] = {}
        self._domain_handlers: dict[str, list[str]] = defaultdict(list)
        self._event_type_handlers: dict[str, list[str]] = defaultdict(list)
        self._pattern_handlers: list[str] = []

    def register_handler(
        self,
        subscription_config: SubscriptionConfig,
        handler: EventHandler
    ) -> None:
        """Register an event handler."""
        sub_id = subscription_config.subscription_id

        self._handlers[sub_id] = {
            "config": subscription_config,
            "handler": handler,
            "retry_count": 0,
        }

        # Index by subscription type for efficient lookup
        if subscription_config.subscription_type == SubscriptionType.DOMAIN:
            domain = subscription_config.filter_criteria.get("domain", "")
            self._domain_handlers[domain].append(sub_id)

        elif subscription_config.subscription_type == SubscriptionType.EVENT_TYPE:
            event_types = subscription_config.filter_criteria.get("event_types", [])
            if isinstance(event_types, str):
                event_types = [event_types]
            for event_type in event_types:
                self._event_type_handlers[event_type].append(sub_id)

        elif subscription_config.subscription_type == SubscriptionType.PATTERN:
            self._pattern_handlers.append(sub_id)

    def unregister_handler(self, subscription_id: str) -> bool:
        """Unregister an event handler."""
        if subscription_id not in self._handlers:
            return False

        config = self._handlers[subscription_id]["config"]

        # Remove from indexes
        if config.subscription_type == SubscriptionType.DOMAIN:
            domain = config.filter_criteria.get("domain", "")
            if subscription_id in self._domain_handlers[domain]:
                self._domain_handlers[domain].remove(subscription_id)

        elif config.subscription_type == SubscriptionType.EVENT_TYPE:
            event_types = config.filter_criteria.get("event_types", [])
            if isinstance(event_types, str):
                event_types = [event_types]
            for event_type in event_types:
                if subscription_id in self._event_type_handlers[event_type]:
                    self._event_type_handlers[event_type].remove(subscription_id)

        elif config.subscription_type == SubscriptionType.PATTERN:
            if subscription_id in self._pattern_handlers:
                self._pattern_handlers.remove(subscription_id)

        # Remove from main registry
        del self._handlers[subscription_id]
        return True

    def get_matching_handlers(self, event: DomainEvent) -> list[dict[str, Any]]:
        """Get all handlers that match an event."""
        matching_handlers = []
        candidate_ids: set[str] = set()

        # Get candidates from indexes
        candidate_ids.update(self._domain_handlers.get(event.domain, []))
        candidate_ids.update(self._event_type_handlers.get(event.event_type, []))
        candidate_ids.update(self._pattern_handlers)

        # Check each candidate for actual match
        for sub_id in candidate_ids:
            if sub_id not in self._handlers:
                continue

            handler_info = self._handlers[sub_id]
            config = handler_info["config"]

            if EventMatcher.matches_criteria(event, config):
                matching_handlers.append(handler_info)

        # Sort by priority (highest first)
        matching_handlers.sort(
            key=lambda h: h["config"].handler_priority.value,
            reverse=True
        )

        return matching_handlers

    def get_all_configs(self) -> list[SubscriptionConfig]:
        """Get all subscription configurations."""
        return [handler["config"] for handler in self._handlers.values()]


class DomainEventSubscriber:
    """
    Simplified subscriber interface for domain services.

    Provides convenient methods for subscribing to domain-specific events.
    """

    def __init__(self, subscriber: EventSubscriber, domain: str):
        self.subscriber = subscriber
        self.domain = domain

    async def subscribe_to_domain_events(
        self,
        target_domain: str,
        handler: EventHandler,
        priority: HandlerPriority = HandlerPriority.NORMAL
    ) -> str:
        """
        Subscribe to all events from a specific domain.

        Args:
            target_domain: Domain to subscribe to
            handler: Event handler function
            priority: Handler priority

        Returns:
            Subscription ID
        """
        config = SubscriptionConfig(
            subscription_id=f"{self.domain}_to_{target_domain}_{id(handler)}",
            subscription_type=SubscriptionType.DOMAIN,
            filter_criteria={"domain": target_domain},
            handler_priority=priority
        )

        return await self.subscriber.subscribe(config, handler)

    async def subscribe_to_event_types(
        self,
        event_types: str | list[str],
        handler: EventHandler,
        priority: HandlerPriority = HandlerPriority.NORMAL
    ) -> str:
        """
        Subscribe to specific event types.

        Args:
            event_types: Event type(s) to subscribe to
            handler: Event handler function
            priority: Handler priority

        Returns:
            Subscription ID
        """
        if isinstance(event_types, str):
            event_types = [event_types]

        config = SubscriptionConfig(
            subscription_id=f"{self.domain}_events_{id(handler)}",
            subscription_type=SubscriptionType.EVENT_TYPE,
            filter_criteria={"event_types": event_types},
            handler_priority=priority
        )

        return await self.subscriber.subscribe(config, handler)

    async def subscribe_to_integration_events(
        self,
        handler: EventHandler,
        priority: HandlerPriority = HandlerPriority.NORMAL
    ) -> str:
        """
        Subscribe to integration events targeting this domain.

        Args:
            handler: Event handler function
            priority: Handler priority

        Returns:
            Subscription ID
        """
        async def integration_handler(event: DomainEvent) -> bool:
            if isinstance(event, IntegrationEvent):
                if event.is_for_domain(self.domain):
                    return await handler(event)
                return True  # Not for this domain, consider handled
            return await handler(event)

        config = SubscriptionConfig(
            subscription_id=f"{self.domain}_integration_{id(handler)}",
            subscription_type=SubscriptionType.PATTERN,
            filter_criteria={"pattern": "*"},  # Match all, filter in handler
            handler_priority=priority
        )

        return await self.subscriber.subscribe(config, integration_handler)
