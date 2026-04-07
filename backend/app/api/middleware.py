"""Custom middleware: request logging and basic rate limiting."""

import logging
import time
from collections import defaultdict
from typing import Dict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

# Simple in-memory rate limiter: max 120 requests/minute per IP
_request_counts: Dict[str, list] = defaultdict(list)
RATE_LIMIT = 120
WINDOW_SECONDS = 60


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log every incoming request and its response time."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s %s %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple per-IP rate limiter."""

    async def dispatch(self, request: Request, call_next) -> Response:
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        timestamps = _request_counts[ip]
        # Keep only timestamps within the current window
        _request_counts[ip] = [t for t in timestamps if now - t < WINDOW_SECONDS]
        if len(_request_counts[ip]) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
            )
        _request_counts[ip].append(now)
        return await call_next(request)
