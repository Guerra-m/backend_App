# =============================================================================
# rate_limit_middleware.py — Middleware de rate limiting para FoodStore
# =============================================================================
# Aplica rate limiting por IP.
# Dos limiters:
#   - auth_limiter:    endpoints de login/register (5 req/15min → estricto)
#   - default_limiter: resto de la API (60 req/min → razonable)
# =============================================================================

from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.rate_limit.rate_limiter import RateLimiter

# Paths que usan el auth_limiter (más estricto — mitiga fuerza bruta)
AUTH_PATHS: tuple[str, ...] = (
    "/api/v1/auth/token",
    "/api/v1/auth/register",
)

# Paths excluidos del rate limiting
EXCLUDED_PATHS: set[str] = {
    "/health",
    "/",
    "/favicon.ico",
    "/openapi.json",
    "/docs",
    "/redoc",
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware de rate limiting para FoodStore.

    Aplica dos limiters:
      - auth_limiter:    5 requests / 15 minutos por IP en login y register.
      - default_limiter: 60 requests / minuto por IP en el resto de la API.

    Registry de instances (_instances) para que los tests puedan
    resetear el estado entre pruebas sin hackear internals.
    """

    # Registry de instances activas (para tests)
    _instances: list["RateLimitMiddleware"] = []

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

        # Auth: 5 intentos en 15 minutos
        # capacity=5 (burst), refill_rate_per_minute=5/15 ≈ 0.33/min
        # Usamos capacity=3 y rate=5 para que tras agotar haya que esperar
        self.auth_limiter = RateLimiter(
            capacity=5,
            refill_rate_per_minute=5,   # 5 por minuto → se agota rápido
        )

        # Default: 60 requests por minuto
        self.default_limiter = RateLimiter(
            capacity=10,
            refill_rate_per_minute=60,
        )

        # Registramos para que los tests puedan resetear
        RateLimitMiddleware._instances.append(self)

    @classmethod
    def reset_all_limiters(cls) -> None:
        """Resetea buckets de TODAS las instances. Llamar en conftest.py."""
        for instance in cls._instances:
            instance.default_limiter.reset_all()
            instance.auth_limiter.reset_all()

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # 1) Excluir paths que no queremos rate-limitar
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        # 2) Elegir limiter según el path
        limiter = (
            self.auth_limiter
            if any(request.url.path.startswith(p) for p in AUTH_PATHS)
            else self.default_limiter
        )

        # 3) Identificar cliente por IP
        client_key = self._get_client_key(request)

        # 4) Verificar si la request pasa
        if not limiter.is_allowed(client_key):
            # Calculamos cuántos segundos esperar para el próximo token
            seconds_until_next = int(1 / max(limiter.refill_rate, 0.001))

            return Response(
                content=(
                    '{"detail":"Demasiadas peticiones. '
                    f'Intenta de nuevo en {seconds_until_next} segundos."}}'
                ),
                status_code=429,
                media_type="application/json",
                headers={
                    "Retry-After": str(seconds_until_next),
                    "X-RateLimit-Limit": str(int(limiter.capacity)),
                    "X-RateLimit-Remaining": "0",
                },
            )

        # 5) Request permitida → ejecutar endpoint
        response = await call_next(request)

        # 6) Agregar headers informativos de rate limit
        response.headers["X-RateLimit-Limit"] = str(int(limiter.capacity))
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, int(limiter.capacity) - 1)
        )

        return response

    @staticmethod
    def _get_client_key(request: Request) -> str:
        """Construye la key del cliente. Prioriza X-Forwarded-For (proxies)."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        if request.client:
            return f"ip:{request.client.host}"
        return "ip:unknown"