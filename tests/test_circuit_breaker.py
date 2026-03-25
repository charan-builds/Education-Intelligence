import asyncio

import pytest

from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError


def test_circuit_breaker_opens_after_threshold():
    async def _run():
        breaker = CircuitBreaker("test_dependency")
        breaker.failure_threshold = 2
        breaker.recovery_timeout_seconds = 60

        async def _fail():
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            await breaker.call(_fail)
        with pytest.raises(RuntimeError):
            await breaker.call(_fail)
        with pytest.raises(CircuitBreakerOpenError):
            await breaker.call(_fail)

    asyncio.run(_run())
