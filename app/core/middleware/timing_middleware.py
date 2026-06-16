# =============================================================================
# timing_middleware.py — Mide el tiempo de cada request
# =============================================================================
# Expone la duración en headers estándar:
#   X-Response-Time-ms: tiempo en milisegundos
#   Server-Timing:      header W3C para DevTools del navegador
# =============================================================================

import time
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

import logging

logger = logging.getLogger("app.middleware.timing")

# Umbral para considerar un request como "lento" (log warning)
SLOW_REQUEST_THRESHOLD_MS = 1000.0


class TimingMiddleware(BaseHTTPMiddleware):
    """
    Mide el tiempo total de cada request y lo expone en headers.
    Requests que superan el umbral se loggean como WARNING.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000.0

        # Header estándar W3C (legible en DevTools → Network → Timing)
        response.headers["Server-Timing"] = (
            f'total;dur={duration_ms:.2f};desc="Total request time"'
        )
        # Header custom más fácil de parsear
        response.headers["X-Response-Time-ms"] = f"{duration_ms:.2f}"

        if duration_ms > SLOW_REQUEST_THRESHOLD_MS:
            logger.warning(
                "SLOW REQUEST: %s %s took %.1fms",
                request.method,
                request.url.path,
                duration_ms,
            )

        return response