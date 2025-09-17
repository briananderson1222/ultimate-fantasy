"""
Domain Request Routing Middleware.

This middleware provides request routing and domain-specific processing
for the modularized backend architecture.
"""
from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from infrastructure.container import get_container


class DomainRouterMiddleware(BaseHTTPMiddleware):
    """Middleware for domain-specific request routing and processing."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.domain_mappings = {
            # New API routes with prefix
            "/api/leagues": "leagues",
            "/api/lineups": "lineups",
            "/api/scoreboard": "scoring",
            "/api/waivers": "trading",
            "/api/waitlist": "waitlist",
            "/api/me": "users",
            # Legacy routes without prefix
            "/leagues": "leagues",
            "/lineups": "lineups",
            "/scoreboard": "scoring",
            "/waivers": "trading",
            "/waitlist": "waitlist",
            "/me": "users",
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request with domain-specific routing.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware/handler in the chain

        Returns:
            HTTP response
        """
        start_time = time.time()

        # Determine domain from request path
        domain = self._determine_domain(request.url.path)

        # Add domain context to request state
        request.state.domain = domain
        request.state.start_time = start_time

        try:
            # Get container for domain services (optional during startup)
            try:
                container = await get_container()
                request.state.container = container
                request.state.service_registry = container.get_service_registry()
            except Exception:
                # Container not ready yet - continue without it
                request.state.container = None
                request.state.service_registry = None

            # Add domain-specific headers
            response = await call_next(request)

            # Add domain and performance headers to response
            response.headers["X-Domain"] = str(domain) if domain is not None else "unknown"
            response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"

            return response

        except Exception as e:
            # Handle errors gracefully
            response = Response(
                content=f"Domain routing error: {e!s}",
                status_code=500,
                headers={
                    "X-Domain": str(domain) if domain is not None else "unknown",
                    "X-Error": "domain_routing_error",
                }
            )
            return response

    def _determine_domain(self, path: str) -> str | None:
        """
        Determine the domain from the request path.

        Args:
            path: Request URL path

        Returns:
            Domain name or None if not found
        """
        for prefix, domain in self.domain_mappings.items():
            if path.startswith(prefix):
                return domain

        # Default domain determination logic
        if path.startswith("/api/"):
            # Extract domain from API path
            parts = path.split("/")
            if len(parts) >= 3:
                endpoint = parts[2]
                # Map common endpoints to domains
                endpoint_mappings = {
                    "teams": "leagues",
                    "players": "lineups",
                    "stats": "scoring",
                    "trades": "trading",
                    "queue": "waitlist",
                    "profile": "users",
                }
                return endpoint_mappings.get(endpoint)

        return None


class DomainMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting domain-specific metrics."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.metrics: dict[str, dict[str, Any]] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Collect metrics for domain requests.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware/handler in the chain

        Returns:
            HTTP response with metrics
        """
        start_time = time.time()
        domain = getattr(request.state, "domain", "unknown")
        method = request.method

        try:
            response = await call_next(request)
            status_code = response.status_code
            duration = time.time() - start_time

            # Update metrics
            self._update_metrics(domain, method, status_code, duration)

            # Add metrics headers
            response.headers["X-Metrics-Domain"] = str(domain) if domain is not None else "unknown"
            response.headers["X-Metrics-Duration"] = f"{duration * 1000:.2f}ms"

            return response

        except Exception as e:
            duration = time.time() - start_time
            self._update_metrics(domain, method, 500, duration, error=str(e))
            raise

    def _update_metrics(
        self,
        domain: str,
        method: str,
        status_code: int,
        duration: float,
        error: str | None = None
    ) -> None:
        """Update domain metrics."""
        if domain not in self.metrics:
            self.metrics[domain] = {
                "request_count": 0,
                "total_duration": 0.0,
                "error_count": 0,
                "status_codes": {},
                "methods": {},
                "avg_duration": 0.0,
            }

        domain_metrics = self.metrics[domain]
        domain_metrics["request_count"] += 1
        domain_metrics["total_duration"] += duration

        # Track status codes
        status_str = str(status_code)
        domain_metrics["status_codes"][status_str] = (
            domain_metrics["status_codes"].get(status_str, 0) + 1
        )

        # Track methods
        domain_metrics["methods"][method] = (
            domain_metrics["methods"].get(method, 0) + 1
        )

        # Track errors
        if error or status_code >= 400:
            domain_metrics["error_count"] += 1

        # Calculate average duration
        domain_metrics["avg_duration"] = (
            domain_metrics["total_duration"] / domain_metrics["request_count"]
        )

    def get_metrics(self) -> dict[str, dict[str, Any]]:
        """Get current metrics for all domains."""
        return self.metrics.copy()

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.metrics.clear()


class DomainSecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for domain-specific security policies."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.domain_policies = {
            "leagues": {
                "require_auth": True,
                "rate_limit": 100,  # requests per minute
                "allowed_methods": ["GET", "POST", "PUT", "DELETE"],
            },
            "lineups": {
                "require_auth": True,
                "rate_limit": 200,
                "allowed_methods": ["GET", "POST", "PUT"],
            },
            "scoring": {
                "require_auth": False,  # Public scoring data
                "rate_limit": 500,
                "allowed_methods": ["GET"],
            },
            "trading": {
                "require_auth": True,
                "rate_limit": 50,
                "allowed_methods": ["GET", "POST", "PUT"],
            },
            "waitlist": {
                "require_auth": False,  # Public waitlist signup
                "rate_limit": 20,
                "allowed_methods": ["GET", "POST"],
            },
            "users": {
                "require_auth": True,
                "rate_limit": 100,
                "allowed_methods": ["GET", "PUT"],
            },
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Apply domain-specific security policies.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware/handler in the chain

        Returns:
            HTTP response or security rejection
        """
        domain = getattr(request.state, "domain", None)

        if domain and domain in self.domain_policies:
            policy = self.domain_policies[domain]

            # Check method restrictions
            if request.method not in policy["allowed_methods"]:
                return Response(
                    content=f"Method {request.method} not allowed for {domain} domain",
                    status_code=405,
                    headers={"X-Domain-Policy": "method_not_allowed"}
                )

            # Add security headers
            response = await call_next(request)
            response.headers["X-Domain-Policy"] = domain
            response.headers["X-Rate-Limit"] = str(policy["rate_limit"])

            return response

        return await call_next(request)


# Metrics collection instance
_metrics_middleware: DomainMetricsMiddleware | None = None


def get_domain_metrics() -> dict[str, dict[str, Any]]:
    """
    Get current domain metrics.

    Returns:
        Dictionary of domain metrics
    """
    global _metrics_middleware
    if _metrics_middleware:
        return _metrics_middleware.get_metrics()
    return {}


def reset_domain_metrics() -> None:
    """Reset domain metrics."""
    global _metrics_middleware
    if _metrics_middleware:
        _metrics_middleware.reset_metrics()


def set_metrics_middleware(middleware: DomainMetricsMiddleware) -> None:
    """Set the global metrics middleware instance."""
    global _metrics_middleware
    _metrics_middleware = middleware
