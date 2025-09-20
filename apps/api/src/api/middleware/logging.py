"""
Enhanced logging and monitoring middleware for Ultimate Fantasy Platform API
"""

from __future__ import annotations

import json
import logging
import time
import traceback
import uuid as _uuid
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

logger = logging.getLogger("app.requests")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Enhanced logging and monitoring middleware that provides:
    - Request/response correlation IDs
    - Structured logging with consistent format
    - Performance metrics and timing
    - Error tracking and stack traces
    - Request/response payload logging (configurable)
    - User activity tracking
    """

    def __init__(self, app: ASGIApp, log_payloads: bool = False, max_payload_size: int = 1024):
        super().__init__(app)
        self.log_payloads = log_payloads
        self.max_payload_size = max_payload_size
        self.metrics = {
            'requests_total': 0,
            'requests_by_status': {},
            'requests_by_method': {},
            'requests_by_endpoint': {},
            'response_times': [],
            'errors_total': 0,
            'slow_requests': 0
        }

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request with comprehensive logging and monitoring"""

        # Generate correlation ID for request tracking
        correlation_id = request.headers.get("x-request-id") or str(_uuid.uuid4())
        request.state.request_id = correlation_id
        request.state.correlation_id = correlation_id

        # Start timing
        start_time = time.perf_counter()
        request_timestamp = datetime.now(timezone.utc)

        # Extract request context
        user_id = getattr(request.state, 'user_id', None)
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get('user-agent', 'Unknown')

        # Log incoming request with structured data
        await self._log_request(
            correlation_id=correlation_id,
            request=request,
            user_id=user_id,
            client_ip=client_ip,
            user_agent=user_agent,
            timestamp=request_timestamp
        )

        # Process request and capture response
        response = None
        error = None

        try:
            response = await call_next(request)

        except Exception as e:
            error = e
            self.metrics['errors_total'] += 1

            # Log error with full context
            await self._log_error(
                correlation_id=correlation_id,
                request=request,
                error=e,
                user_id=user_id,
                client_ip=client_ip
            )

            # Create error response
            response = Response(
                content=json.dumps({
                    "error": "Internal server error",
                    "correlation_id": correlation_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }),
                status_code=500,
                media_type="application/json"
            )

        # Calculate response time
        end_time = time.perf_counter()
        response_time = end_time - start_time

        # Add correlation ID and timing to response headers
        response.headers.setdefault("x-request-id", correlation_id)
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Response-Time"] = f"{response_time:.3f}s"

        # Log response with metrics
        await self._log_response(
            correlation_id=correlation_id,
            request=request,
            response=response,
            response_time=response_time,
            user_id=user_id,
            client_ip=client_ip,
            error=error
        )

        # Update internal metrics
        self._update_metrics(request, response, response_time)

        return response

    async def _log_request(
        self,
        correlation_id: str,
        request: Request,
        user_id: Optional[str],
        client_ip: str,
        user_agent: str,
        timestamp: datetime
    ):
        """Log incoming request with structured format"""

        # Get request body if configured
        request_body = None
        if self.log_payloads and request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = await request.body()
                if len(body) <= self.max_payload_size:
                    try:
                        request_body = json.loads(body.decode('utf-8'))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        request_body = body.decode('utf-8', errors='ignore')[:self.max_payload_size]
                else:
                    request_body = f"<payload too large: {len(body)} bytes>"
            except Exception:
                request_body = "<unable to read body>"

        log_data = {
            "type": "request",
            "correlation_id": correlation_id,
            "timestamp": timestamp.isoformat(),
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": {
                key: value for key, value in request.headers.items()
                if key.lower() not in ['authorization', 'cookie', 'x-api-key']
            },
            "client_ip": client_ip,
            "user_agent": user_agent,
            "user_id": user_id,
            "request_body": request_body
        }

        logger.info(f"Incoming request: {request.method} {request.url.path}", extra=log_data)

    async def _log_response(
        self,
        correlation_id: str,
        request: Request,
        response: Response,
        response_time: float,
        user_id: Optional[str],
        client_ip: str,
        error: Optional[Exception]
    ):
        """Log outgoing response with metrics"""

        # Get response body if configured and small enough
        response_body = None
        if self.log_payloads and hasattr(response, 'body'):
            try:
                if len(response.body) <= self.max_payload_size:
                    try:
                        response_body = json.loads(response.body.decode('utf-8'))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        response_body = response.body.decode('utf-8', errors='ignore')[:self.max_payload_size]
                else:
                    response_body = f"<response too large: {len(response.body)} bytes>"
            except Exception:
                response_body = "<unable to read response body>"

        elapsed_ms = response_time * 1000

        log_data = {
            "type": "response",
            "correlation_id": correlation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "status_code": response.status_code,
            "response_time_ms": round(elapsed_ms, 2),
            "response_headers": dict(response.headers),
            "client_ip": client_ip,
            "user_id": user_id,
            "response_body": response_body,
            "error": str(error) if error else None
        }

        # Log at appropriate level based on status code
        if response.status_code >= 500:
            logger.error(
                f"Response: {request.method} {request.url.path} -> {response.status_code} ({elapsed_ms:.1f}ms)",
                extra=log_data
            )
        elif response.status_code >= 400:
            logger.warning(
                f"Response: {request.method} {request.url.path} -> {response.status_code} ({elapsed_ms:.1f}ms)",
                extra=log_data
            )
        else:
            logger.info(
                f"Response: {request.method} {request.url.path} -> {response.status_code} ({elapsed_ms:.1f}ms)",
                extra=log_data
            )

    async def _log_error(
        self,
        correlation_id: str,
        request: Request,
        error: Exception,
        user_id: Optional[str],
        client_ip: str
    ):
        """Log error with full context and stack trace"""

        log_data = {
            "type": "error",
            "correlation_id": correlation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "stack_trace": traceback.format_exc(),
            "client_ip": client_ip,
            "user_id": user_id
        }

        logger.error(
            f"Unhandled exception in {request.method} {request.url.path}: {error}",
            extra=log_data
        )

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request headers"""

        # Check for forwarded headers (common in load balancers/proxies)
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()

        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip

        # Fallback to direct client IP
        return getattr(request.client, 'host', 'unknown')

    def _update_metrics(self, request: Request, response: Response, response_time: float):
        """Update internal metrics for monitoring"""

        self.metrics['requests_total'] += 1

        # Track by status code
        status_code = response.status_code
        if status_code not in self.metrics['requests_by_status']:
            self.metrics['requests_by_status'][status_code] = 0
        self.metrics['requests_by_status'][status_code] += 1

        # Track by method
        method = request.method
        if method not in self.metrics['requests_by_method']:
            self.metrics['requests_by_method'][method] = 0
        self.metrics['requests_by_method'][method] += 1

        # Track by endpoint (path without query params)
        endpoint = request.url.path
        if endpoint not in self.metrics['requests_by_endpoint']:
            self.metrics['requests_by_endpoint'][endpoint] = 0
        self.metrics['requests_by_endpoint'][endpoint] += 1

        # Track response times
        self.metrics['response_times'].append(response_time)

        # Keep only last 1000 response times for memory efficiency
        if len(self.metrics['response_times']) > 1000:
            self.metrics['response_times'] = self.metrics['response_times'][-1000:]

        # Track slow requests (> 2 seconds)
        if response_time > 2.0:
            self.metrics['slow_requests'] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics for monitoring dashboard"""

        response_times = self.metrics['response_times']

        return {
            "requests_total": self.metrics['requests_total'],
            "requests_by_status": self.metrics['requests_by_status'],
            "requests_by_method": self.metrics['requests_by_method'],
            "requests_by_endpoint": self.metrics['requests_by_endpoint'],
            "errors_total": self.metrics['errors_total'],
            "slow_requests": self.metrics['slow_requests'],
            "response_time_stats": {
                "count": len(response_times),
                "average": sum(response_times) / len(response_times) if response_times else 0,
                "min": min(response_times) if response_times else 0,
                "max": max(response_times) if response_times else 0,
                "p95": self._percentile(response_times, 95) if response_times else 0,
                "p99": self._percentile(response_times, 99) if response_times else 0
            }
        }

    def _percentile(self, data: list, percentile: int) -> float:
        """Calculate percentile from list of values"""
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)

        if index >= len(sorted_data):
            return sorted_data[-1]

        return sorted_data[index]


class CorrelationIDFilter(logging.Filter):
    """Logging filter to add correlation ID to log records"""

    def filter(self, record):
        # Try to get correlation ID from current request context
        correlation_id = getattr(record, 'correlation_id', None)
        if not correlation_id:
            correlation_id = 'no-correlation-id'

        record.correlation_id = correlation_id
        return True


def configure_logging():
    """Configure application logging with structured format"""

    # Create custom formatter for structured logging
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(correlation_id)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Add correlation ID filter to all handlers
    correlation_filter = CorrelationIDFilter()
    root_logger.addFilter(correlation_filter)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Configure console handler with structured format
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    return root_logger
