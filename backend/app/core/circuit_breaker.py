from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from app.core.config import get_settings
from app.core.metrics import circuit_breaker_state


class CircuitBreakerOpenError(RuntimeError):
    pass


class CircuitBreaker:
    def __init__(self, dependency: str) -> None:
        settings = get_settings()
        self.dependency = dependency
        self.failure_threshold = settings.circuit_breaker_failure_threshold
        self.recovery_timeout_seconds = settings.circuit_breaker_recovery_timeout_seconds
        self.failure_count = 0
        self.opened_at: float | None = None
        circuit_breaker_state.labels(dependency=dependency).set(0)

    def _is_open(self) -> bool:
        if self.opened_at is None:
            return False
        if (time.monotonic() - self.opened_at) >= self.recovery_timeout_seconds:
            self.opened_at = None
            self.failure_count = 0
            circuit_breaker_state.labels(dependency=self.dependency).set(0)
            return False
        return True

    async def call(self, operation: Callable[[], Awaitable]):
        if self._is_open():
            circuit_breaker_state.labels(dependency=self.dependency).set(1)
            raise CircuitBreakerOpenError(f"Circuit breaker open for {self.dependency}")
        try:
            result = await operation()
            self.failure_count = 0
            circuit_breaker_state.labels(dependency=self.dependency).set(0)
            return result
        except Exception:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.opened_at = time.monotonic()
                circuit_breaker_state.labels(dependency=self.dependency).set(1)
            raise
