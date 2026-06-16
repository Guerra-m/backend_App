# =============================================================================
# logging_middleware.py — Logging de requests/responses para FoodStore
# =============================================================================
# Agrega X-Request-ID a cada request (para correlacionar logs).
# Loggea método, path, status y duración de cada request.
# =============================================================================

import time
import uuid
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

import logging

logger = logging.getLogger("app.middleware.logging")

EXCLUDED_PATHS: set[str] = {
    "/health",
    "/favicon.ico",
    "/openapi.json",
    "/docs",
    "/redoc",
}


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware que loggea cada request y agrega X-Request-ID.

    El request_id se guarda en request.state para que los
    exception_handlers lo incluyan en las respuestas de error.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # Generar ID único para correlacionar logs del mismo request
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        # Guardamos en state para que exception_handlers lo usen
        request.state.request_id = request_id

        # Paths excluidos: no loggear
        if request.url.path in EXCLUDED_PATHS:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

        logger.info(
            "→ %s %s [id=%s]",
            request.method,
            request.url.path,
            request_id,
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "✗ %s %s [id=%s] EXCEPTION after %.1fms: %s",
                request.method,
                request.url.path,
                request_id,
                duration_ms,
                repr(exc),
            )
            raise

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Nivel según status code
        if response.status_code >= 500:
            log_fn = logger.error
        elif response.status_code >= 400:
            log_fn = logger.warning
        else:
            log_fn = logger.info

        log_fn(
            "← %s %s [id=%s] %d in %.1fms",
            request.method,
            request.url.path,
            request_id,
            response.status_code,
            duration_ms,
        )

        # Inyectar el request_id en la response para debugging
        response.headers["X-Request-ID"] = request_id

        return response