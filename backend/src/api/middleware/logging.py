from __future__ import annotations

import logging
import time
import uuid as _uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("uvicorn.access")


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
            "%s %s %s %.1fms req_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            req_id,
        )
        return response
