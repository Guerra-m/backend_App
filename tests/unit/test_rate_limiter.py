"""
tests/unit/test_rate_limiter.py
Tests unitarios del TokenBucket y RateLimiter.
Tests puros sin DB, sin HTTP, sin FastAPI.
"""
import time
import threading
import pytest
from app.core.rate_limit.rate_limiter import RateLimiter, TokenBucket


class TestTokenBucket:

    def test_arranca_lleno(self):
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.tokens == 10

    def test_consume_exitoso(self):
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.try_consume(1) is True
        assert bucket.tokens == pytest.approx(9, abs=0.01)

    def test_consume_falla_si_vacio(self):
        bucket = TokenBucket(capacity=2, refill_rate=1.0)
        assert bucket.try_consume(2) is True
        assert bucket.try_consume(1) is False

    def test_consume_multiple_tokens(self):
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.try_consume(5) is True
        assert bucket.tokens == pytest.approx(5, abs=0.01)

    def test_rechaza_mas_que_capacity(self):
        bucket = TokenBucket(capacity=5, refill_rate=1.0)
        assert bucket.try_consume(10) is False
        assert bucket.tokens == 5

    def test_refill_con_tiempo(self):
        bucket = TokenBucket(capacity=10, refill_rate=10)
        bucket.try_consume(10)
        assert bucket.tokens == 0
        time.sleep(0.2)
        assert bucket.try_consume(1) is True

    def test_refill_no_supera_capacity(self):
        bucket = TokenBucket(capacity=5, refill_rate=100)
        time.sleep(0.2)
        assert bucket.try_consume(5) is True

    def test_reset_vuelve_a_lleno(self):
        bucket = TokenBucket(capacity=5, refill_rate=1.0)
        bucket.try_consume(5)
        assert bucket.try_consume(1) is False
        bucket.reset()
        assert bucket.try_consume(5) is True


class TestRateLimiter:

    def test_primer_request_permitido(self):
        limiter = RateLimiter(capacity=10, refill_rate_per_minute=60)
        assert limiter.is_allowed("ip:1.2.3.4") is True

    def test_keys_distintas_independientes(self):
        limiter = RateLimiter(capacity=2, refill_rate_per_minute=1)
        assert limiter.is_allowed("ip:A") is True
        assert limiter.is_allowed("ip:A") is True
        assert limiter.is_allowed("ip:A") is False
        assert limiter.is_allowed("ip:B") is True
        assert limiter.is_allowed("ip:B") is True

    def test_burst_igual_a_capacity(self):
        limiter = RateLimiter(capacity=5, refill_rate_per_minute=1)
        for _ in range(5):
            assert limiter.is_allowed("ip:X") is True
        assert limiter.is_allowed("ip:X") is False

    def test_reset_all_limpia_todo(self):
        limiter = RateLimiter(capacity=2, refill_rate_per_minute=1)
        limiter.is_allowed("ip:A")
        limiter.is_allowed("ip:A")
        assert limiter.is_allowed("ip:A") is False
        limiter.reset_all()
        assert limiter.is_allowed("ip:A") is True

    def test_reset_key_limpia_solo_esa_key(self):
        limiter = RateLimiter(capacity=2, refill_rate_per_minute=1)
        limiter.is_allowed("ip:A")
        limiter.is_allowed("ip:A")
        limiter.is_allowed("ip:B")
        limiter.reset_key("ip:A")
        assert limiter.is_allowed("ip:A") is True
        assert limiter.is_allowed("ip:B") is True
        assert limiter.is_allowed("ip:B") is False


class TestThreadSafety:

    def test_concurrencia_respeta_capacity(self):
        capacity = 50
        limiter = RateLimiter(capacity=capacity, refill_rate_per_minute=1)
        successes = []
        lock = threading.Lock()

        def consume():
            ok = limiter.is_allowed("shared")
            with lock:
                successes.append(ok)

        threads = [threading.Thread(target=consume) for _ in range(100)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert sum(successes) == capacity