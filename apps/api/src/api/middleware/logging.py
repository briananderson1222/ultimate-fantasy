from __future__ import annotations

import logging
import time
import uuid as _uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.requests")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        started = time.perf_counter()
        req_id = request.headers.get("x-request-id") or str(_uuid.uuid4())
        request.state.request_id = req_id
        response = await call_next(request)
        response.headers.setdefault("x-request-id", req_id)
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "Request: %s %s - Status: %d - Time: %.1fms - ID: %s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            req_id,
        )
        return response
