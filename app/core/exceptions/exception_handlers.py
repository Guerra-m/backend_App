# =============================================================================
# exception_handlers.py — Handlers globales de FoodStore
# =============================================================================
# Formato unificado de respuesta para TODOS los errores:
# {
#   "detail": "mensaje legible",
#   "code": "codigo_interno",
#   "request_id": "uuid",
#   "timestamp": "ISO8601"
# }
# =============================================================================

from datetime import datetime, timezone

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions.custom_exceptions import (
    AppError,
    RateLimitExceededError,
)


def _build_error_response(
    *,
    code: str,
    message: str,
    status_code: int,
    request_id: str | None = None,
    extra: dict | None = None,
) -> JSONResponse:
    """Construye la respuesta JSON estándar para todos los errores."""
    body: dict = {
        "detail": message,
        "code": code,
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        body.update(extra)

    return JSONResponse(status_code=status_code, content=body)


def _get_request_id(request: Request) -> str | None:
    """Recupera el request_id guardado por LoggingMiddleware."""
    return getattr(request.state, "request_id", None)


# ─── HANDLER 1: Excepciones de dominio (AppError) ────────────────────────────

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Captura toda excepción que hereda de AppError."""
    request_id = _get_request_id(request)

    response = _build_error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        request_id=request_id,
    )

    if isinstance(exc, RateLimitExceededError):
        response.headers["Retry-After"] = str(exc.retry_after)

    return response


# ─── HANDLER 2: HTTPException estándar de FastAPI ────────────────────────────

async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Override del handler default de FastAPI para usar nuestro formato."""
    request_id = _get_request_id(request)

    code_map = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed",
        409: "conflict",
        422: "validation_error",
        429: "rate_limit_exceeded",
        500: "internal_error",
    }
    code = code_map.get(exc.status_code, "http_error")

    return _build_error_response(
        code=code,
        message=str(exc.detail),
        status_code=exc.status_code,
        request_id=request_id,
    )


# ─── HANDLER 3: Errores de validación Pydantic (422) ─────────────────────────

async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Reformatea errores de Pydantic a formato amigable."""
    request_id = _get_request_id(request)

    errors = []
    for err in exc.errors():
        location = ".".join(str(x) for x in err.get("loc", []))
        errors.append({
            "field": location,
            "message": err.get("msg", "Error de validación"),
            "type": err.get("type", "validation_error"),
        })

    return _build_error_response(
        code="validation_error",
        message="Los datos enviados no son válidos",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        request_id=request_id,
        extra={"fields": errors},
    )


# ─── HANDLER 4: Errores de SQLAlchemy ────────────────────────────────────────

async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Captura errores de BD no manejados. No expone detalles al cliente."""
    request_id = _get_request_id(request)

    if isinstance(exc, IntegrityError):
        return _build_error_response(
            code="duplicate_resource",
            message="La operación viola una restricción de unicidad o integridad.",
            status_code=status.HTTP_409_CONFLICT,
            request_id=request_id,
        )

    return _build_error_response(
        code="database_error",
        message="Error de base de datos. Contacta al administrador.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=request_id,
    )


# ─── HANDLER 5: Catch-all ────────────────────────────────────────────────────

async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Red de seguridad: captura cualquier excepción no manejada."""
    request_id = _get_request_id(request)

    return _build_error_response(
        code="internal_error",
        message="Error interno del servidor.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=request_id,
    )


# ─── Registro ─────────────────────────────────────────────────────────────────

def register_exception_handlers(app: FastAPI) -> None:
    """Registra todos los handlers. Llamar UNA vez en main.py."""
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)