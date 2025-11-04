"""Circuit breaker pattern for preventing cascading failures."""

import threading
from collections.abc import Callable
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from .logger import StructuredLogger


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing fast, not calling operation
    HALF_OPEN = "half_open"  # Testing if service has recovered


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""

    def __init__(self, circuit_name: str, failure_count: int):
        self.circuit_name = circuit_name
        self.failure_count = failure_count
        super().__init__(
            f"Circuit breaker '{circuit_name}' is OPEN after {failure_count} failures"
        )


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance."""

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 5,
        recovery_timeout_seconds: int = 60,
        expected_exception: type[Exception] = Exception,
        success_threshold: int = 1,  # Successes needed in HALF_OPEN to close
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = timedelta(seconds=recovery_timeout_seconds)
        self.expected_exception = expected_exception
        self.success_threshold = success_threshold

        # State management
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: datetime | None = None
        self._lock = threading.Lock()

        # Logging
        self.logger = StructuredLogger(f"circuit_breaker.{name}")

    @property
    def state(self) -> CircuitState:
        """Get current circuit breaker state."""
        with self._lock:
            return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        with self._lock:
            return self._failure_count

    @property
    def success_count(self) -> int:
        """Get current success count (in HALF_OPEN state)."""
        with self._lock:
            return self._success_count

    def call(
        self, operation: Callable[[], Any], operation_name: str = "unknown"
    ) -> Any:
        """Execute operation through circuit breaker."""
        with self._lock:
            current_state = self._state

            # Check if we should attempt to reset from OPEN to HALF_OPEN
            if current_state == CircuitState.OPEN and self._should_attempt_reset():
                self._transition_to_half_open()
                current_state = CircuitState.HALF_OPEN

            # If circuit is OPEN, fail fast
            if current_state == CircuitState.OPEN:
                self.logger.warning(
                    f"Circuit breaker {self.name} is OPEN, failing fast for {operation_name}",
                    circuit_name=self.name,
                    operation=operation_name,
                    failure_count=self._failure_count,
                    resilience_event=True,
                )
                raise CircuitBreakerError(self.name, self._failure_count)

        # Execute the operation
        try:
            result = operation()
            self._on_success()
            return result

        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self._last_failure_time is None:
            return False

        return datetime.utcnow() - self._last_failure_time >= self.recovery_timeout

    def _transition_to_half_open(self) -> None:
        """Transition from OPEN to HALF_OPEN state."""
        old_state = self._state
        self._state = CircuitState.HALF_OPEN
        self._success_count = 0

        self.logger.log_circuit_breaker_event(
            self.name,
            old_state.value,
            CircuitState.HALF_OPEN.value,
            self._failure_count,
            {"recovery_timeout_seconds": self.recovery_timeout.total_seconds()},
        )

    def _on_success(self) -> None:
        """Handle successful operation."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1

                # Check if we have enough successes to close the circuit
                if self._success_count >= self.success_threshold:
                    self._transition_to_closed()
                else:
                    self.logger.debug(
                        f"Circuit breaker {self.name} success in HALF_OPEN state",
                        circuit_name=self.name,
                        success_count=self._success_count,
                        success_threshold=self.success_threshold,
                        resilience_event=True,
                    )

            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success in CLOSED state
                if self._failure_count > 0:
                    self.logger.debug(
                        f"Circuit breaker {self.name} resetting failure count after success",
                        circuit_name=self.name,
                        previous_failure_count=self._failure_count,
                        resilience_event=True,
                    )
                    self._failure_count = 0

    def _on_failure(self) -> None:
        """Handle failed operation."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.utcnow()

            if self._state == CircuitState.HALF_OPEN:
                # Any failure in HALF_OPEN goes back to OPEN
                self._transition_to_open()

            elif self._state == CircuitState.CLOSED:
                # Check if we've hit the failure threshold
                if self._failure_count >= self.failure_threshold:
                    self._transition_to_open()
                else:
                    self.logger.debug(
                        f"Circuit breaker {self.name} failure count increased",
                        circuit_name=self.name,
                        failure_count=self._failure_count,
                        failure_threshold=self.failure_threshold,
                        resilience_event=True,
                    )

    def _transition_to_closed(self) -> None:
        """Transition to CLOSED state."""
        old_state = self._state
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0

        self.logger.log_circuit_breaker_event(
            self.name,
            old_state.value,
            CircuitState.CLOSED.value,
            0,  # Reset failure count
            {"success_count": self._success_count},
        )

        self.logger.info(
            f"Circuit breaker {self.name} recovered and closed",
            circuit_name=self.name,
            resilience_event=True,
        )

    def _transition_to_open(self) -> None:
        """Transition to OPEN state."""
        old_state = self._state
        self._state = CircuitState.OPEN
        self._success_count = 0

        self.logger.log_circuit_breaker_event(
            self.name,
            old_state.value,
            CircuitState.OPEN.value,
            self._failure_count,
            {
                "failure_threshold": self.failure_threshold,
                "recovery_timeout_seconds": self.recovery_timeout.total_seconds(),
            },
        )

        self.logger.error(
            f"Circuit breaker {self.name} opened due to {self._failure_count} failures",
            circuit_name=self.name,
            failure_count=self._failure_count,
            failure_threshold=self.failure_threshold,
            resilience_event=True,
        )

    def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state."""
        with self._lock:
            old_state = self._state
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None

            if old_state != CircuitState.CLOSED:
                self.logger.log_circuit_breaker_event(
                    self.name,
                    old_state.value,
                    CircuitState.CLOSED.value,
                    0,
                    {"manual_reset": True},
                )

                self.logger.info(
                    f"Circuit breaker {self.name} manually reset",
                    circuit_name=self.name,
                    resilience_event=True,
                )

    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "failure_threshold": self.failure_threshold,
                "success_threshold": self.success_threshold,
                "recovery_timeout_seconds": self.recovery_timeout.total_seconds(),
                "last_failure_time": (
                    self._last_failure_time.isoformat()
                    if self._last_failure_time
                    else None
                ),
                "time_until_retry": (
                    max(
                        0,
                        (
                            self._last_failure_time
                            + self.recovery_timeout
                            - datetime.utcnow()
                        ).total_seconds(),
                    )
                    if self._last_failure_time and self._state == CircuitState.OPEN
                    else 0
                ),
            }
