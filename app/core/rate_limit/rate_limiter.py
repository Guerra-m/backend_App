# =============================================================================
# rate_limiter.py — Algoritmo Token Bucket (en memoria)
# =============================================================================
# Implementación del patrón Token Bucket para rate limiting.
# Cada cliente (identificado por IP) tiene su propio bucket.
# El bucket se llena a una tasa constante (refill_rate tokens/segundo).
# Cada request consume 1 token. Si no hay tokens → 429.
# =============================================================================

import threading
import time
from dataclasses import dataclass, field


@dataclass
class TokenBucket:
    """
    Implementación del algoritmo Token Bucket para UN cliente.

    capacity:     máximo de tokens en el balde (tamaño del burst).
    refill_rate:  tokens por segundo que se agregan al balde.
    tokens:       tokens actuales (float para precisión).
    last_refill:  timestamp del último refill.
    _lock:        lock para thread-safety.
    """

    capacity: float
    refill_rate: float  # tokens por segundo
    tokens: float = field(init=False)
    last_refill: float = field(init=False)
    _lock: threading.Lock = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.tokens = float(self.capacity)  # arranca lleno
        self.last_refill = time.perf_counter()
        self._lock = threading.Lock()

    def try_consume(self, tokens: float = 1.0) -> bool:
        """
        Intenta consumir tokens. Thread-safe.
        Devuelve True si había tokens, False si no (→ 429).
        """
        with self._lock:
            now = time.perf_counter()
            elapsed = now - self.last_refill
            # Refill pasivo: agrega tokens según tiempo transcurrido
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.refill_rate,
            )
            self.last_refill = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def reset(self) -> None:
        """Resetea el bucket a estado inicial (lleno). Útil para tests."""
        with self._lock:
            self.tokens = float(self.capacity)
            self.last_refill = time.perf_counter()


class RateLimiter:
    """
    Rate limiter que mantiene un TokenBucket por cliente (key).

    La key es típicamente la IP del cliente.
    En producción con múltiples workers, usar Redis en vez de dict en memoria.
    """

    def __init__(self, capacity: int, refill_rate_per_minute: int) -> None:
        """
        Args:
            capacity:               burst máximo (ej: 3 para auth, 10 para default).
            refill_rate_per_minute: tokens por minuto (ej: 5 para auth, 60 para default).
        """
        self.capacity = float(capacity)
        # Convertimos por-minuto a por-segundo para el algoritmo
        self.refill_rate = refill_rate_per_minute / 60.0
        self._buckets: dict[str, TokenBucket] = {}
        self._buckets_lock = threading.Lock()

    def _get_bucket(self, key: str) -> TokenBucket:
        """Obtiene (o crea lazy) el bucket para una key."""
        with self._buckets_lock:
            if key not in self._buckets:
                self._buckets[key] = TokenBucket(
                    capacity=self.capacity,
                    refill_rate=self.refill_rate,
                )
            return self._buckets[key]

    def is_allowed(self, key: str) -> bool:
        """
        Verifica si el cliente puede hacer una request.
        True → pasa. False → 429.
        """
        return self._get_bucket(key).try_consume(1.0)

    def reset_all(self) -> None:
        """Resetea TODOS los buckets. Solo para tests."""
        with self._buckets_lock:
            for bucket in self._buckets.values():
                bucket.reset()

    def reset_key(self, key: str) -> None:
        """Resetea el bucket de UNA key. Para tests dirigidos."""
        with self._buckets_lock:
            if key in self._buckets:
                self._buckets[key].reset()