"""
Domain Event Base Classes.

This module provides the foundation for domain events that enable
loose coupling between domains and support event-driven architecture.
"""
from __future__ import annotations

import uuid
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar


class EventPriority(Enum):
    """Event priority levels for processing order."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class EventStatus(Enum):
    """Event processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class EventMetadata:
    """Metadata associated with domain events."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0"
    source: str | None = None
    correlation_id: str | None = None
    causation_id: str | None = None
    priority: EventPriority = EventPriority.NORMAL
    status: EventStatus = EventStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    tags: list[str] = field(default_factory=list)
    custom_headers: dict[str, Any] = field(default_factory=dict)


T = TypeVar('T')


class DomainEvent(ABC):
    """
    Abstract base class for all domain events.

    Domain events represent something that happened in the domain
    that other parts of the system might be interested in.
    """

    def __init__(
        self,
        aggregate_id: str,
        domain: str,
        event_type: str,
        data: dict[str, Any],
        metadata: EventMetadata | None = None
    ):
        """
        Initialize a domain event.

        Args:
            aggregate_id: ID of the aggregate that generated the event
            domain: Domain name (e.g., "leagues", "users", "lineups")
            event_type: Type of event (e.g., "league_created", "user_joined")
            data: Event payload data
            metadata: Event metadata (auto-generated if not provided)
        """
        self.aggregate_id = aggregate_id
        self.domain = domain
        self.event_type = event_type
        self.data = data
        self.metadata = metadata or EventMetadata()

    @property
    def event_id(self) -> str:
        """Get the unique event ID."""
        return self.metadata.event_id

    @property
    def timestamp(self) -> datetime:
        """Get the event timestamp."""
        return self.metadata.timestamp

    @property
    def version(self) -> str:
        """Get the event schema version."""
        return self.metadata.version

    def to_dict(self) -> dict[str, Any]:
        """
        Convert event to dictionary representation.

        Returns:
            Dictionary representation of the event
        """
        return {
            "event_id": self.event_id,
            "aggregate_id": self.aggregate_id,
            "domain": self.domain,
            "event_type": self.event_type,
            "data": self.data,
            "metadata": {
                "timestamp": self.timestamp.isoformat(),
                "version": self.version,
                "source": self.metadata.source,
                "correlation_id": self.metadata.correlation_id,
                "causation_id": self.metadata.causation_id,
                "priority": self.metadata.priority.value,
                "status": self.metadata.status.value,
                "retry_count": self.metadata.retry_count,
                "max_retries": self.metadata.max_retries,
                "tags": self.metadata.tags,
                "custom_headers": self.metadata.custom_headers,
            }
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DomainEvent:
        """
        Create event from dictionary representation.

        Args:
            data: Dictionary representation of event

        Returns:
            DomainEvent instance
        """
        metadata_dict = data.get("metadata", {})
        metadata = EventMetadata(
            event_id=data["event_id"],
            timestamp=datetime.fromisoformat(metadata_dict.get("timestamp", datetime.utcnow().isoformat())),
            version=metadata_dict.get("version", "1.0"),
            source=metadata_dict.get("source"),
            correlation_id=metadata_dict.get("correlation_id"),
            causation_id=metadata_dict.get("causation_id"),
            priority=EventPriority(metadata_dict.get("priority", "normal")),
            status=EventStatus(metadata_dict.get("status", "pending")),
            retry_count=metadata_dict.get("retry_count", 0),
            max_retries=metadata_dict.get("max_retries", 3),
            tags=metadata_dict.get("tags", []),
            custom_headers=metadata_dict.get("custom_headers", {}),
        )

        return cls(
            aggregate_id=data["aggregate_id"],
            domain=data["domain"],
            event_type=data["event_type"],
            data=data["data"],
            metadata=metadata
        )

    def with_correlation_id(self, correlation_id: str) -> DomainEvent:
        """
        Create a copy of the event with a correlation ID.

        Args:
            correlation_id: Correlation ID to set

        Returns:
            New event instance with correlation ID
        """
        new_metadata = EventMetadata(
            event_id=self.metadata.event_id,
            timestamp=self.metadata.timestamp,
            version=self.metadata.version,
            source=self.metadata.source,
            correlation_id=correlation_id,
            causation_id=self.metadata.causation_id,
            priority=self.metadata.priority,
            status=self.metadata.status,
            retry_count=self.metadata.retry_count,
            max_retries=self.metadata.max_retries,
            tags=self.metadata.tags.copy(),
            custom_headers=self.metadata.custom_headers.copy(),
        )

        return DomainEvent(
            aggregate_id=self.aggregate_id,
            domain=self.domain,
            event_type=self.event_type,
            data=self.data.copy(),
            metadata=new_metadata
        )

    def mark_as_processing(self) -> None:
        """Mark event as currently being processed."""
        self.metadata.status = EventStatus.PROCESSING

    def mark_as_completed(self) -> None:
        """Mark event as successfully processed."""
        self.metadata.status = EventStatus.COMPLETED

    def mark_as_failed(self, increment_retry: bool = True) -> None:
        """
        Mark event as failed.

        Args:
            increment_retry: Whether to increment retry count
        """
        self.metadata.status = EventStatus.FAILED
        if increment_retry:
            self.metadata.retry_count += 1

    def can_retry(self) -> bool:
        """
        Check if event can be retried.

        Returns:
            True if event can be retried, False otherwise
        """
        return self.metadata.retry_count < self.metadata.max_retries

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"event_id={self.event_id}, "
            f"domain={self.domain}, "
            f"event_type={self.event_type}, "
            f"aggregate_id={self.aggregate_id})"
        )


class IntegrationEvent(DomainEvent):
    """
    Integration event for cross-domain communication.

    These events are published to external systems and other domains.
    """

    def __init__(
        self,
        aggregate_id: str,
        domain: str,
        event_type: str,
        data: dict[str, Any],
        target_domains: list[str] | None = None,
        metadata: EventMetadata | None = None
    ):
        """
        Initialize integration event.

        Args:
            aggregate_id: ID of the aggregate that generated the event
            domain: Source domain name
            event_type: Type of event
            data: Event payload data
            target_domains: List of target domains (None means all domains)
            metadata: Event metadata
        """
        super().__init__(aggregate_id, domain, event_type, data, metadata)
        self.target_domains = target_domains or []

    def is_for_domain(self, domain: str) -> bool:
        """
        Check if event is intended for a specific domain.

        Args:
            domain: Domain to check

        Returns:
            True if event is for the domain, False otherwise
        """
        # If no target domains specified, event is for all domains except source
        if not self.target_domains:
            return domain != self.domain

        return domain in self.target_domains


class AggregateEvent(Generic[T]):
    """
    Container for events generated by an aggregate.

    This allows aggregates to collect events during processing
    and publish them afterwards.
    """

    def __init__(self, aggregate_id: str, aggregate_type: type[T]):
        """
        Initialize aggregate event container.

        Args:
            aggregate_id: ID of the aggregate
            aggregate_type: Type of the aggregate
        """
        self.aggregate_id = aggregate_id
        self.aggregate_type = aggregate_type
        self._events: list[DomainEvent] = []

    def add_event(self, event: DomainEvent) -> None:
        """
        Add an event to the container.

        Args:
            event: Event to add
        """
        self._events.append(event)

    def get_events(self) -> list[DomainEvent]:
        """
        Get all events from the container.

        Returns:
            List of domain events
        """
        return self._events.copy()

    def clear_events(self) -> None:
        """Clear all events from the container."""
        self._events.clear()

    def has_events(self) -> bool:
        """
        Check if container has any events.

        Returns:
            True if container has events, False otherwise
        """
        return len(self._events) > 0

    def __len__(self) -> int:
        """Get number of events in container."""
        return len(self._events)


# Common domain event types
class LeagueEvent(DomainEvent):
    """Base class for league domain events."""

    def __init__(self, aggregate_id: str, event_type: str, data: dict[str, Any], metadata: EventMetadata | None = None):
        super().__init__(aggregate_id, "leagues", event_type, data, metadata)


class UserEvent(DomainEvent):
    """Base class for user domain events."""

    def __init__(self, aggregate_id: str, event_type: str, data: dict[str, Any], metadata: EventMetadata | None = None):
        super().__init__(aggregate_id, "users", event_type, data, metadata)


class LineupEvent(DomainEvent):
    """Base class for lineup domain events."""

    def __init__(self, aggregate_id: str, event_type: str, data: dict[str, Any], metadata: EventMetadata | None = None):
        super().__init__(aggregate_id, "lineups", event_type, data, metadata)


class TradingEvent(DomainEvent):
    """Base class for trading domain events."""

    def __init__(self, aggregate_id: str, event_type: str, data: dict[str, Any], metadata: EventMetadata | None = None):
        super().__init__(aggregate_id, "trading", event_type, data, metadata)


class ScoringEvent(DomainEvent):
    """Base class for scoring domain events."""

    def __init__(self, aggregate_id: str, event_type: str, data: dict[str, Any], metadata: EventMetadata | None = None):
        super().__init__(aggregate_id, "scoring", event_type, data, metadata)


class WaitlistEvent(DomainEvent):
    """Base class for waitlist domain events."""

    def __init__(self, aggregate_id: str, event_type: str, data: dict[str, Any], metadata: EventMetadata | None = None):
        super().__init__(aggregate_id, "waitlist", event_type, data, metadata)


# Event factory for convenient event creation
class EventFactory:
    """Factory for creating domain events."""

    @staticmethod
    def create_league_event(
        event_type: str,
        league_id: str,
        data: dict[str, Any],
        integration: bool = False,
        target_domains: list[str] | None = None
    ) -> DomainEvent:
        """Create a league domain event."""
        if integration:
            return IntegrationEvent(league_id, "leagues", event_type, data, target_domains)
        return LeagueEvent(league_id, event_type, data)

    @staticmethod
    def create_user_event(
        event_type: str,
        user_id: str,
        data: dict[str, Any],
        integration: bool = False,
        target_domains: list[str] | None = None
    ) -> DomainEvent:
        """Create a user domain event."""
        if integration:
            return IntegrationEvent(user_id, "users", event_type, data, target_domains)
        return UserEvent(user_id, event_type, data)

    @staticmethod
    def create_lineup_event(
        event_type: str,
        lineup_id: str,
        data: dict[str, Any],
        integration: bool = False,
        target_domains: list[str] | None = None
    ) -> DomainEvent:
        """Create a lineup domain event."""
        if integration:
            return IntegrationEvent(lineup_id, "lineups", event_type, data, target_domains)
        return LineupEvent(lineup_id, event_type, data)

    @staticmethod
    def create_trading_event(
        event_type: str,
        aggregate_id: str,
        data: dict[str, Any],
        integration: bool = False,
        target_domains: list[str] | None = None
    ) -> DomainEvent:
        """Create a trading domain event."""
        if integration:
            return IntegrationEvent(aggregate_id, "trading", event_type, data, target_domains)
        return TradingEvent(aggregate_id, event_type, data)

    @staticmethod
    def create_scoring_event(
        event_type: str,
        aggregate_id: str,
        data: dict[str, Any],
        integration: bool = False,
        target_domains: list[str] | None = None
    ) -> DomainEvent:
        """Create a scoring domain event."""
        if integration:
            return IntegrationEvent(aggregate_id, "scoring", event_type, data, target_domains)
        return ScoringEvent(aggregate_id, event_type, data)

    @staticmethod
    def create_waitlist_event(
        event_type: str,
        aggregate_id: str,
        data: dict[str, Any],
        integration: bool = False,
        target_domains: list[str] | None = None
    ) -> DomainEvent:
        """Create a waitlist domain event."""
        if integration:
            return IntegrationEvent(aggregate_id, "waitlist", event_type, data, target_domains)
        return WaitlistEvent(aggregate_id, event_type, data)
