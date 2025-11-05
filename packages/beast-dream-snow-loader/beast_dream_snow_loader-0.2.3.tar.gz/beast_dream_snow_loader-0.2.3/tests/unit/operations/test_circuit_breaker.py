"""Unit tests for CircuitBreaker and circuit breaker functionality."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from beast_dream_snow_loader.operations.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitState,
)


class TestCircuitBreaker:
    """Test cases for CircuitBreaker class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.circuit_breaker = CircuitBreaker(
            name="test_circuit",
            failure_threshold=3,
            recovery_timeout_seconds=5,
            success_threshold=1,
        )

    def test_initial_state(self):
        """Test circuit breaker initial state."""
        assert self.circuit_breaker.state == CircuitState.CLOSED
        assert self.circuit_breaker.failure_count == 0
        assert self.circuit_breaker.success_count == 0

    def test_successful_operation_closed_state(self):
        """Test successful operation in CLOSED state."""
        mock_operation = Mock(return_value="success")

        result = self.circuit_breaker.call(mock_operation, "test_operation")

        assert result == "success"
        assert self.circuit_breaker.state == CircuitState.CLOSED
        assert self.circuit_breaker.failure_count == 0
        assert mock_operation.call_count == 1

    def test_failure_count_increment(self):
        """Test that failure count increments on failures."""
        mock_operation = Mock(side_effect=Exception("Test error"))

        # First failure
        with pytest.raises(Exception):
            self.circuit_breaker.call(mock_operation, "test_operation")

        assert self.circuit_breaker.state == CircuitState.CLOSED
        assert self.circuit_breaker.failure_count == 1

        # Second failure
        with pytest.raises(Exception):
            self.circuit_breaker.call(mock_operation, "test_operation")

        assert self.circuit_breaker.failure_count == 2

    def test_circuit_opens_after_threshold(self):
        """Test that circuit opens after reaching failure threshold."""
        mock_operation = Mock(side_effect=Exception("Test error"))

        # Reach failure threshold (3 failures)
        for i in range(3):
            with pytest.raises(Exception):
                self.circuit_breaker.call(mock_operation, "test_operation")

        assert self.circuit_breaker.state == CircuitState.OPEN
        assert self.circuit_breaker.failure_count == 3

    def test_circuit_breaker_error_when_open(self):
        """Test that CircuitBreakerError is raised when circuit is open."""
        mock_operation = Mock(side_effect=Exception("Test error"))

        # Open the circuit
        for i in range(3):
            with pytest.raises(Exception):
                self.circuit_breaker.call(mock_operation, "test_operation")

        # Now circuit should be open and raise CircuitBreakerError
        with pytest.raises(CircuitBreakerError) as exc_info:
            self.circuit_breaker.call(mock_operation, "test_operation")

        assert "test_circuit" in str(exc_info.value)
        assert "3 failures" in str(exc_info.value)
        # Operation should not be called when circuit is open
        assert mock_operation.call_count == 3  # Only the initial failures

    def test_circuit_transitions_to_half_open_after_timeout(self):
        """Test circuit transitions to HALF_OPEN after recovery timeout."""
        mock_operation = Mock(side_effect=Exception("Test error"))

        # Open the circuit
        for i in range(3):
            with pytest.raises(Exception):
                self.circuit_breaker.call(mock_operation, "test_operation")

        assert self.circuit_breaker.state == CircuitState.OPEN

        # Mock time to simulate timeout passage
        with patch(
            "beast_dream_snow_loader.operations.circuit_breaker.datetime"
        ) as mock_datetime:
            # Set current time to be after recovery timeout
            future_time = datetime.utcnow() + timedelta(seconds=10)
            mock_datetime.utcnow.return_value = future_time

            # Next call should transition to HALF_OPEN and execute operation
            with pytest.raises(Exception):
                self.circuit_breaker.call(mock_operation, "test_operation")

            assert (
                self.circuit_breaker.state == CircuitState.OPEN
            )  # Back to OPEN after failure
            assert mock_operation.call_count == 4  # Operation was called in HALF_OPEN

    def test_circuit_closes_after_success_in_half_open(self):
        """Test circuit closes after successful operation in HALF_OPEN state."""
        mock_operation = Mock()

        # Open the circuit first
        mock_operation.side_effect = Exception("Test error")
        for i in range(3):
            with pytest.raises(Exception):
                self.circuit_breaker.call(mock_operation, "test_operation")

        assert self.circuit_breaker.state == CircuitState.OPEN

        # Mock time and make operation succeed
        with patch(
            "beast_dream_snow_loader.operations.circuit_breaker.datetime"
        ) as mock_datetime:
            future_time = datetime.utcnow() + timedelta(seconds=10)
            mock_datetime.utcnow.return_value = future_time

            mock_operation.side_effect = None
            mock_operation.return_value = "success"

            result = self.circuit_breaker.call(mock_operation, "test_operation")

            assert result == "success"
            assert self.circuit_breaker.state == CircuitState.CLOSED
            assert self.circuit_breaker.failure_count == 0  # Reset on close

    def test_failure_in_half_open_returns_to_open(self):
        """Test that failure in HALF_OPEN state returns circuit to OPEN."""
        # Manually set circuit to HALF_OPEN state
        with self.circuit_breaker._lock:
            self.circuit_breaker._state = CircuitState.HALF_OPEN
            self.circuit_breaker._failure_count = 3

        mock_operation = Mock(side_effect=Exception("Test error"))

        with pytest.raises(Exception):
            self.circuit_breaker.call(mock_operation, "test_operation")

        assert self.circuit_breaker.state == CircuitState.OPEN
        assert self.circuit_breaker.failure_count == 4  # Incremented

    def test_success_resets_failure_count_in_closed_state(self):
        """Test that success resets failure count in CLOSED state."""
        mock_operation = Mock()

        # Add some failures (but not enough to open circuit)
        mock_operation.side_effect = Exception("Test error")
        for i in range(2):
            with pytest.raises(Exception):
                self.circuit_breaker.call(mock_operation, "test_operation")

        assert self.circuit_breaker.failure_count == 2

        # Now succeed
        mock_operation.side_effect = None
        mock_operation.return_value = "success"

        result = self.circuit_breaker.call(mock_operation, "test_operation")

        assert result == "success"
        assert self.circuit_breaker.failure_count == 0  # Reset
        assert self.circuit_breaker.state == CircuitState.CLOSED

    def test_manual_reset(self):
        """Test manual reset of circuit breaker."""
        mock_operation = Mock(side_effect=Exception("Test error"))

        # Open the circuit
        for i in range(3):
            with pytest.raises(Exception):
                self.circuit_breaker.call(mock_operation, "test_operation")

        assert self.circuit_breaker.state == CircuitState.OPEN

        # Manual reset
        self.circuit_breaker.reset()

        assert self.circuit_breaker.state == CircuitState.CLOSED
        assert self.circuit_breaker.failure_count == 0
        assert self.circuit_breaker.success_count == 0

    def test_get_stats(self):
        """Test circuit breaker statistics."""
        stats = self.circuit_breaker.get_stats()

        assert stats["name"] == "test_circuit"
        assert stats["state"] == "closed"
        assert stats["failure_count"] == 0
        assert stats["failure_threshold"] == 3
        assert stats["success_threshold"] == 1
        assert stats["recovery_timeout_seconds"] == 5
        assert stats["last_failure_time"] is None
        assert stats["time_until_retry"] == 0

    def test_get_stats_with_failures(self):
        """Test circuit breaker statistics after failures."""
        mock_operation = Mock(side_effect=Exception("Test error"))

        # Add some failures
        for i in range(2):
            with pytest.raises(Exception):
                self.circuit_breaker.call(mock_operation, "test_operation")

        stats = self.circuit_breaker.get_stats()

        assert stats["failure_count"] == 2
        assert stats["last_failure_time"] is not None

    def test_get_stats_when_open(self):
        """Test circuit breaker statistics when circuit is open."""
        mock_operation = Mock(side_effect=Exception("Test error"))

        # Open the circuit
        for i in range(3):
            with pytest.raises(Exception):
                self.circuit_breaker.call(mock_operation, "test_operation")

        stats = self.circuit_breaker.get_stats()

        assert stats["state"] == "open"
        assert stats["failure_count"] == 3
        assert stats["time_until_retry"] > 0  # Should have time remaining

    def test_custom_success_threshold(self):
        """Test circuit breaker with custom success threshold."""
        circuit_breaker = CircuitBreaker(
            name="test_circuit",
            failure_threshold=2,
            recovery_timeout_seconds=1,
            success_threshold=2,  # Need 2 successes to close
        )

        mock_operation = Mock()

        # Open the circuit
        mock_operation.side_effect = Exception("Test error")
        for i in range(2):
            with pytest.raises(Exception):
                circuit_breaker.call(mock_operation, "test_operation")

        assert circuit_breaker.state == CircuitState.OPEN

        # Transition to HALF_OPEN and succeed once
        with patch(
            "beast_dream_snow_loader.operations.circuit_breaker.datetime"
        ) as mock_datetime:
            future_time = datetime.utcnow() + timedelta(seconds=2)
            mock_datetime.utcnow.return_value = future_time

            mock_operation.side_effect = None
            mock_operation.return_value = "success"

            # First success - should stay in HALF_OPEN
            result = circuit_breaker.call(mock_operation, "test_operation")
            assert result == "success"
            assert circuit_breaker.state == CircuitState.HALF_OPEN
            assert circuit_breaker.success_count == 1

            # Second success - should close circuit
            result = circuit_breaker.call(mock_operation, "test_operation")
            assert result == "success"
            assert circuit_breaker.state == CircuitState.CLOSED
            assert circuit_breaker.success_count == 0  # Reset

    def test_custom_expected_exception(self):
        """Test circuit breaker with custom expected exception type."""
        circuit_breaker = CircuitBreaker(
            name="test_circuit", failure_threshold=2, expected_exception=ValueError
        )

        mock_operation = Mock()

        # ValueError should trigger circuit breaker
        mock_operation.side_effect = ValueError("Test error")
        for i in range(2):
            with pytest.raises(ValueError):
                circuit_breaker.call(mock_operation, "test_operation")

        assert circuit_breaker.state == CircuitState.OPEN

        # Reset circuit breaker to test other exceptions
        circuit_breaker.reset()

        # Other exceptions should not be caught by circuit breaker
        mock_operation.side_effect = RuntimeError("Different error")
        with pytest.raises(RuntimeError):
            circuit_breaker.call(mock_operation, "test_operation")

        # Failure count should not increase for non-expected exceptions
        assert circuit_breaker.failure_count == 0

    def test_thread_safety(self):
        """Test basic thread safety of circuit breaker operations."""
        import threading

        mock_operation = Mock(return_value="success")
        results = []
        exceptions = []

        def worker():
            try:
                result = self.circuit_breaker.call(mock_operation, "test_operation")
                results.append(result)
            except Exception as e:
                exceptions.append(e)

        # Run multiple threads concurrently
        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All operations should succeed
        assert len(results) == 10
        assert len(exceptions) == 0
        assert all(result == "success" for result in results)
        assert self.circuit_breaker.state == CircuitState.CLOSED
