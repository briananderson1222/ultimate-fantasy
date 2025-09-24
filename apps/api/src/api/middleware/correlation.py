"""
Request correlation ID tracking middleware.

Provides comprehensive request tracking and correlation:
- Unique correlation IDs for each request
- Request/response logging with correlation
- Distributed tracing support
- Performance monitoring
- Error tracking and debugging
"""

import time
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextvars import ContextVar
from dataclasses import dataclass

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from infrastructure.logging.domain_logger import get_logger
except ImportError:
    import logging
    get_logger = logging.getLogger

try:
    from infrastructure.observability.tracing import get_tracer, trace_fantasy_operation
except ImportError:
    class MockSpan:
        def set_attribute(self, key, value):
            pass

    class MockTracer:
        def span(self, name, **kwargs):
            return MockSpan()

    def get_tracer():
        return MockTracer()

    def trace_fantasy_operation(tracer, name, **kwargs):
        from contextlib import contextmanager

        @contextmanager
        def mock_trace():
            yield MockSpan()

        return mock_trace()

logger = get_logger(__name__)
tracer = get_tracer()

# Context variables for correlation tracking
correlation_id_context: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
request_context: ContextVar[Optional['RequestContext']] = ContextVar('request_context', default=None)


@dataclass
class RequestContext:
    """Request context information."""
    correlation_id: str
    trace_id: str
    user_id: Optional[str]
    session_id: Optional[str]
    client_ip: str
    user_agent: str
    method: str
    path: str
    query_params: Dict[str, Any]
    headers: Dict[str, str]
    start_time: datetime
    request_size: int = 0
    response_size: int = 0
    status_code: int = 0
    duration_ms: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request correlation ID tracking and context management.

    Automatically generates and tracks correlation IDs for all requests,
    enabling distributed tracing and comprehensive request monitoring.
    """

    def __init__(
        self,
        app,
        header_name: str = "X-Correlation-ID",
        include_headers: List[str] = None,
        exclude_paths: List[str] = None,
        log_requests: bool = True,
        log_responses: bool = True,
        max_header_size: int = 1024
    ):
        """
        Initialize correlation middleware.

        Args:
            app: FastAPI application
            header_name: Header name for correlation ID
            include_headers: Headers to include in context
            exclude_paths: Paths to exclude from tracking
            log_requests: Whether to log requests
            log_responses: Whether to log responses
            max_header_size: Maximum size for header values
        """
        super().__init__(app)
        self.header_name = header_name
        self.include_headers = include_headers or [
            "user-agent",
            "authorization",
            "content-type",
            "accept",
            "x-forwarded-for",
            "x-real-ip"
        ]
        self.exclude_paths = set(exclude_paths or [
            "/health",
            "/metrics",
            "/favicon.ico"
        ])
        self.log_requests = log_requests
        self.log_responses = log_responses
        self.max_header_size = max_header_size

    async def dispatch(self, request: Request, call_next):
        """Process request with correlation tracking."""
        start_time = time.time()

        # Skip tracking for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Generate or extract correlation ID
        correlation_id = self._get_or_generate_correlation_id(request)

        # Generate trace ID
        trace_id = str(uuid.uuid4())

        # Extract request context
        context = self._build_request_context(
            request, correlation_id, trace_id, start_time
        )

        # Set context variables
        correlation_id_context.set(correlation_id)
        request_context.set(context)

        # Add correlation ID to request state
        request.state.correlation_id = correlation_id
        request.state.trace_id = trace_id

        # Log request if enabled
        if self.log_requests:
            self._log_request(context)

        try:
            # Process request with tracing
            with trace_fantasy_operation(
                tracer,
                f"{request.method} {request.url.path}",
                correlation_id=correlation_id,
                trace_id=trace_id,
                method=request.method,
                path=request.url.path
            ) as span:
                span.set_attribute("correlation_id", correlation_id)
                span.set_attribute("trace_id", trace_id)
                span.set_attribute("user_agent", context.user_agent)
                span.set_attribute("client_ip", context.client_ip)

                # Process request
                response = await call_next(request)

                # Update context with response info
                end_time = time.time()
                context.duration_ms = (end_time - start_time) * 1000
                context.status_code = response.status_code
                context.response_size = self._get_response_size(response)

                # Add correlation headers to response
                response.headers[self.header_name] = correlation_id
                response.headers["X-Trace-ID"] = trace_id
                response.headers["X-Request-Duration-Ms"] = str(int(context.duration_ms))

                # Update span with response info
                span.set_attribute("status_code", response.status_code)
                span.set_attribute("duration_ms", context.duration_ms)
                span.set_attribute("response_size", context.response_size)

                # Log response if enabled
                if self.log_responses:
                    self._log_response(context)

                return response

        except Exception as e:
            # Handle errors
            end_time = time.time()
            context.duration_ms = (end_time - start_time) * 1000
            context.error_message = str(e)
            context.status_code = 500

            # Log error
            self._log_error(context, e)

            # Re-raise exception
            raise

    def _get_or_generate_correlation_id(self, request: Request) -> str:
        """Get existing correlation ID or generate new one."""
        # Check for existing correlation ID in headers
        correlation_id = request.headers.get(self.header_name.lower())

        if correlation_id:
            # Validate and sanitize existing correlation ID
            correlation_id = correlation_id[:36]  # Limit length
            if self._is_valid_correlation_id(correlation_id):
                return correlation_id

        # Generate new correlation ID
        return str(uuid.uuid4())

    def _is_valid_correlation_id(self, correlation_id: str) -> bool:
        """Validate correlation ID format."""
        if not correlation_id or len(correlation_id) > 36:
            return False

        # Check if it's a valid UUID format
        try:
            uuid.UUID(correlation_id)
            return True
        except ValueError:
            # Allow other alphanumeric formats
            return correlation_id.replace("-", "").isalnum()

    def _build_request_context(
        self,
        request: Request,
        correlation_id: str,
        trace_id: str,
        start_time: float
    ) -> RequestContext:
        """Build request context from request data."""
        # Extract user information
        user_id = getattr(request.state, "user_id", None)
        session_id = request.headers.get("x-session-id")

        # Get client IP
        client_ip = self._get_client_ip(request)

        # Get user agent
        user_agent = request.headers.get("user-agent", "")[:self.max_header_size]

        # Extract relevant headers
        headers = {}
        for header_name in self.include_headers:
            header_value = request.headers.get(header_name)
            if header_value:
                headers[header_name] = header_value[:self.max_header_size]

        # Get query parameters
        query_params = dict(request.query_params)

        # Get request size
        request_size = self._get_request_size(request)

        return RequestContext(
            correlation_id=correlation_id,
            trace_id=trace_id,
            user_id=user_id,
            session_id=session_id,
            client_ip=client_ip,
            user_agent=user_agent,
            method=request.method,
            path=request.url.path,
            query_params=query_params,
            headers=headers,
            start_time=datetime.fromtimestamp(start_time),
            request_size=request_size
        )

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        # Check for forwarded headers (reverse proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct connection
        return request.client.host if request.client else "unknown"

    def _get_request_size(self, request: Request) -> int:
        """Get request content size."""
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                return int(content_length)
            except ValueError:
                pass
        return 0

    def _get_response_size(self, response: Response) -> int:
        """Get response content size."""
        content_length = response.headers.get("content-length")
        if content_length:
            try:
                return int(content_length)
            except ValueError:
                pass
        return 0

    def _log_request(self, context: RequestContext):
        """Log request details."""
        logger.info(
            f"Request started",
            extra={
                "correlation_id": context.correlation_id,
                "trace_id": context.trace_id,
                "method": context.method,
                "path": context.path,
                "user_id": context.user_id,
                "client_ip": context.client_ip,
                "user_agent": context.user_agent,
                "request_size": context.request_size,
                "query_params": context.query_params,
                "timestamp": context.start_time.isoformat()
            }
        )

    def _log_response(self, context: RequestContext):
        """Log response details."""
        log_level = logging.INFO
        if context.status_code >= 400:
            log_level = logging.WARNING
        if context.status_code >= 500:
            log_level = logging.ERROR

        logger.log(
            log_level,
            f"Request completed",
            extra={
                "correlation_id": context.correlation_id,
                "trace_id": context.trace_id,
                "method": context.method,
                "path": context.path,
                "user_id": context.user_id,
                "status_code": context.status_code,
                "duration_ms": context.duration_ms,
                "response_size": context.response_size,
                "client_ip": context.client_ip
            }
        )

    def _log_error(self, context: RequestContext, error: Exception):
        """Log error details."""
        logger.error(
            f"Request failed",
            extra={
                "correlation_id": context.correlation_id,
                "trace_id": context.trace_id,
                "method": context.method,
                "path": context.path,
                "user_id": context.user_id,
                "error": str(error),
                "error_type": type(error).__name__,
                "duration_ms": context.duration_ms,
                "client_ip": context.client_ip
            },
            exc_info=True
        )


# Utility functions for accessing correlation context

def get_correlation_id() -> Optional[str]:
    """Get current correlation ID from context."""
    return correlation_id_context.get()


def get_request_context() -> Optional[RequestContext]:
    """Get current request context."""
    return request_context.get()


def set_correlation_metadata(key: str, value: Any):
    """Set metadata for current request context."""
    context = request_context.get()
    if context:
        context.metadata[key] = value


def get_correlation_metadata(key: str) -> Any:
    """Get metadata from current request context."""
    context = request_context.get()
    if context:
        return context.metadata.get(key)
    return None


class CorrelatedLogger:
    """Logger that automatically includes correlation information."""

    def __init__(self, logger_name: str):
        self.logger = get_logger(logger_name)

    def _add_correlation_info(self, extra: Dict[str, Any]) -> Dict[str, Any]:
        """Add correlation information to log extra data."""
        correlation_id = get_correlation_id()
        context = get_request_context()

        if correlation_id:
            extra["correlation_id"] = correlation_id

        if context:
            extra.update({
                "trace_id": context.trace_id,
                "user_id": context.user_id,
                "method": context.method,
                "path": context.path
            })

        return extra

    def debug(self, message: str, **kwargs):
        """Log debug message with correlation info."""
        extra = self._add_correlation_info(kwargs.get("extra", {}))
        self.logger.debug(message, extra=extra)

    def info(self, message: str, **kwargs):
        """Log info message with correlation info."""
        extra = self._add_correlation_info(kwargs.get("extra", {}))
        self.logger.info(message, extra=extra)

    def warning(self, message: str, **kwargs):
        """Log warning message with correlation info."""
        extra = self._add_correlation_info(kwargs.get("extra", {}))
        self.logger.warning(message, extra=extra)

    def error(self, message: str, **kwargs):
        """Log error message with correlation info."""
        extra = self._add_correlation_info(kwargs.get("extra", {}))
        self.logger.error(message, extra=extra, exc_info=kwargs.get("exc_info", False))


def get_correlated_logger(name: str) -> CorrelatedLogger:
    """Get a logger that includes correlation information."""
    return CorrelatedLogger(name)


# Decorators for correlation tracking

def correlate_function(func_name: Optional[str] = None):
    """
    Decorator to add correlation tracking to functions.

    Args:
        func_name: Optional custom function name for logging
    """
    def decorator(func):
        import functools

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = func_name or f"{func.__module__}.{func.__name__}"
            correlation_id = get_correlation_id()

            if correlation_id:
                with trace_fantasy_operation(
                    tracer,
                    name,
                    correlation_id=correlation_id
                ) as span:
                    span.set_attribute("function_name", name)
                    return await func(*args, **kwargs)
            else:
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = func_name or f"{func.__module__}.{func.__name__}"
            correlation_id = get_correlation_id()

            if correlation_id:
                logger = get_correlated_logger(name)
                logger.debug(f"Function {name} called")

            return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator