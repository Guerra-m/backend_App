# =============================================================================
# custom_exceptions.py — Excepciones de dominio de FoodStore
# =============================================================================
# El Service lanza estas excepciones (no HTTPException).
# Los exception_handlers las convierten a JSON con formato unificado.
# Esto desacopla el service de FastAPI (testeable sin HTTP).
# =============================================================================


class AppError(Exception):
    """Base de todas las excepciones de dominio de FoodStore."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(
        self,
        message: str = "Error interno de la aplicación",
        status_code: int | None = None,
        code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code


class ResourceNotFoundError(AppError):
    """404 — El recurso solicitado no existe."""
    status_code = 404
    code = "not_found"

    def __init__(
        self,
        message: str | None = None,
        resource: str | None = None,
        identifier: str | int | None = None,
    ) -> None:
        if message is None and resource is not None:
            message = f"No se encontró el {resource}"
            if identifier is not None:
                message += f" con identificador '{identifier}'"
            message += "."
        if message is None:
            message = "Recurso no encontrado"
        super().__init__(message=message)
        self.resource = resource
        self.identifier = str(identifier) if identifier is not None else None


class DuplicateResourceError(AppError):
    """409 — Se intentó crear un recurso que ya existe."""
    status_code = 409
    code = "duplicate_resource"

    def __init__(
        self,
        message: str | None = None,
        resource: str | None = None,
        field: str | None = None,
        value: str | int | None = None,
    ) -> None:
        if message is None and resource is not None:
            message = f"Ya existe un {resource}"
            if field is not None:
                message += f" con {field}='{value}'"
            message += "."
        if message is None:
            message = "El recurso ya existe"
        super().__init__(message=message)
        self.resource = resource
        self.field = field
        self.value = str(value) if value is not None else None


class BusinessRuleError(AppError):
    """400 — La operación viola una regla de negocio."""
    status_code = 400
    code = "business_rule_violation"

    def __init__(self, message: str = "La operación viola una regla de negocio") -> None:
        super().__init__(message=message)


class AuthenticationError(AppError):
    """401 — No autenticado."""
    status_code = 401
    code = "authentication_error"

    def __init__(self, message: str = "No autenticado") -> None:
        super().__init__(message=message)


class AuthorizationError(AppError):
    """403 — Autenticado pero sin permisos."""
    status_code = 403
    code = "authorization_error"

    def __init__(self, message: str = "Permisos insuficientes") -> None:
        super().__init__(message=message)


class RateLimitExceededError(AppError):
    """429 — Rate limit superado."""
    status_code = 429
    code = "rate_limit_exceeded"

    def __init__(
        self,
        message: str = "Demasiadas peticiones. Intenta de nuevo más tarde.",
        retry_after: int = 60,
    ) -> None:
        super().__init__(message=message)
        self.retry_after = retry_after