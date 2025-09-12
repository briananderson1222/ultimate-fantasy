from __future__ import annotations

import logging
import time
import uuid as _uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("uvicorn.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
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

