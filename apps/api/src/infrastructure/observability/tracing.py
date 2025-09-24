"""
OpenTelemetry tracing configuration for Ultimate Fantasy Platform.

Provides comprehensive tracing for FastAPI, SQLAlchemy, and external API calls
with fantasy sports specific trace attributes and context propagation.
"""

import os

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


class FantasyTracingConfig:
    """Configuration for OpenTelemetry tracing in fantasy sports context."""

    def __init__(
        self,
        service_name: str = "ultimate-fantasy-api",
        service_version: str = "1.0.0",
        environment: str = "development",
        jaeger_endpoint: str | None = None,
        sample_rate: float = 1.0,
    ):
        """
        Initialize tracing configuration.

        Args:
            service_name: Name of the service for trace identification
            service_version: Version of the service
            environment: Environment name (dev, staging, prod)
            jaeger_endpoint: Jaeger collector endpoint
            sample_rate: Sampling rate for traces (0.0 to 1.0)
        """
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment
        self.jaeger_endpoint = jaeger_endpoint or os.getenv(
            "JAEGER_ENDPOINT", "http://localhost:14268/api/traces"
        )
        self.sample_rate = sample_rate

        # Fantasy sports specific trace attributes
        self.fantasy_attributes = {
            "service.name": service_name,
            "service.version": service_version,
            "deployment.environment": environment,
            "fantasy.platform": "ultimate-fantasy",
            "fantasy.domain": "fantasy-sports",
        }

    def setup_tracing(self) -> trace.Tracer:
        """
        Configure and initialize OpenTelemetry tracing.

        Returns:
            Configured tracer instance
        """
        # Create resource with fantasy sports context
        resource = Resource.create(self.fantasy_attributes)

        # Set up tracer provider
        trace.set_tracer_provider(TracerProvider(resource=resource))
        tracer = trace.get_tracer(__name__)

        # Configure Jaeger exporter
        jaeger_exporter = JaegerExporter(
            collector_endpoint=self.jaeger_endpoint,
        )

        # Add span processor
        span_processor = BatchSpanProcessor(jaeger_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)

        return tracer

    def instrument_fastapi(self, app) -> None:
        """
        Instrument FastAPI application with tracing.

        Args:
            app: FastAPI application instance
        """
        FastAPIInstrumentor.instrument_app(
            app,
            tracer_provider=trace.get_tracer_provider(),
            excluded_urls="/health,/metrics,/docs,/openapi.json",
        )

    def instrument_sqlalchemy(self, engine) -> None:
        """
        Instrument SQLAlchemy engine with tracing.

        Args:
            engine: SQLAlchemy engine instance
        """
        SQLAlchemyInstrumentor().instrument(
            engine=engine,
            tracer_provider=trace.get_tracer_provider(),
            enable_commenter=True,
            commenter_options={
                "db_driver": True,
                "db_framework": True,
                "opentelemetry_values": True,
            },
        )

    def instrument_httpx(self) -> None:
        """Instrument HTTPX client for external API tracing."""
        HTTPXClientInstrumentor().instrument(
            tracer_provider=trace.get_tracer_provider()
        )


class FantasySpanContext:
    """Context manager for fantasy sports specific span attributes."""

    def __init__(self, tracer: trace.Tracer, name: str, **attributes):
        """
        Initialize span context.

        Args:
            tracer: OpenTelemetry tracer
            name: Span name
            **attributes: Additional span attributes
        """
        self.tracer = tracer
        self.name = name
        self.attributes = attributes
        self.span = None

    def __enter__(self):
        """Start the span and set fantasy sports context."""
        self.span = self.tracer.start_span(self.name)

        # Set fantasy sports specific attributes
        if self.attributes:
            for key, value in self.attributes.items():
                self.span.set_attribute(key, value)

        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End the span and handle exceptions."""
        if self.span:
            if exc_type:
                self.span.record_exception(exc_val)
                self.span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
            else:
                self.span.set_status(trace.Status(trace.StatusCode.OK))

            self.span.end()


# Convenience functions for fantasy sports tracing


def trace_fantasy_operation(
    tracer: trace.Tracer,
    operation_name: str,
    league_id: str | None = None,
    user_id: str | None = None,
    player_id: str | None = None,
    **kwargs,
) -> FantasySpanContext:
    """
    Create a traced context for fantasy sports operations.

    Args:
        tracer: OpenTelemetry tracer
        operation_name: Name of the operation
        league_id: League identifier
        user_id: User identifier
        player_id: Player identifier
        **kwargs: Additional attributes

    Returns:
        Span context manager
    """
    attributes = {}

    if league_id:
        attributes["fantasy.league.id"] = league_id
    if user_id:
        attributes["fantasy.user.id"] = user_id
    if player_id:
        attributes["fantasy.player.id"] = player_id

    # Add operation type
    attributes["fantasy.operation.type"] = operation_name

    # Add any additional attributes
    attributes.update(kwargs)

    return FantasySpanContext(tracer, f"fantasy.{operation_name}", **attributes)


def trace_draft_operation(
    tracer: trace.Tracer,
    draft_id: str,
    operation: str,
    pick_number: int | None = None,
    team_id: str | None = None,
) -> FantasySpanContext:
    """
    Create a traced context for draft operations.

    Args:
        tracer: OpenTelemetry tracer
        draft_id: Draft identifier
        operation: Draft operation type
        pick_number: Current pick number
        team_id: Team making the pick

    Returns:
        Span context manager
    """
    attributes = {"fantasy.draft.id": draft_id, "fantasy.draft.operation": operation}

    if pick_number is not None:
        attributes["fantasy.draft.pick_number"] = pick_number
    if team_id:
        attributes["fantasy.draft.team_id"] = team_id

    return FantasySpanContext(tracer, f"fantasy.draft.{operation}", **attributes)


def trace_trade_operation(
    tracer: trace.Tracer,
    trade_id: str,
    operation: str,
    from_team_id: str | None = None,
    to_team_id: str | None = None,
) -> FantasySpanContext:
    """
    Create a traced context for trade operations.

    Args:
        tracer: OpenTelemetry tracer
        trade_id: Trade identifier
        operation: Trade operation type
        from_team_id: Proposing team ID
        to_team_id: Receiving team ID

    Returns:
        Span context manager
    """
    attributes = {"fantasy.trade.id": trade_id, "fantasy.trade.operation": operation}

    if from_team_id:
        attributes["fantasy.trade.from_team_id"] = from_team_id
    if to_team_id:
        attributes["fantasy.trade.to_team_id"] = to_team_id

    return FantasySpanContext(tracer, f"fantasy.trade.{operation}", **attributes)


# Global tracer instance
_tracer: trace.Tracer | None = None


def get_tracer() -> trace.Tracer:
    """
    Get the global tracer instance.

    Returns:
        OpenTelemetry tracer
    """
    global _tracer
    if _tracer is None:
        config = FantasyTracingConfig()
        _tracer = config.setup_tracing()
    return _tracer


def setup_tracing(app, engine=None) -> trace.Tracer:
    """
    Setup complete tracing for the application.

    Args:
        app: FastAPI application
        engine: SQLAlchemy engine (optional)

    Returns:
        Configured tracer
    """
    config = FantasyTracingConfig()
    tracer = config.setup_tracing()

    # Instrument FastAPI
    config.instrument_fastapi(app)

    # Instrument SQLAlchemy if provided
    if engine:
        config.instrument_sqlalchemy(engine)

    # Instrument HTTPX for external APIs
    config.instrument_httpx()

    global _tracer
    _tracer = tracer

    return tracer
