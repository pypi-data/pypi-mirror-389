"""Unit tests for RetryManager and retry functionality."""

import time
from unittest.mock import Mock, patch

import pytest
import requests

from beast_dream_snow_loader.operations.retry import RetryManager, RetryPolicy


class TestRetryPolicy:
    """Test cases for RetryPolicy dataclass."""

    def test_default_policy(self):
        """Test default retry policy values."""
        policy = RetryPolicy()

        assert policy.max_attempts == 3
        assert policy.base_delay_seconds == 1.0
        assert policy.max_delay_seconds == 60.0
        assert policy.exponential_base == 2.0
        assert policy.jitter is True
        assert requests.exceptions.RequestException in policy.retryable_exceptions
        assert 429 in policy.retryable_status_codes
        assert 500 in policy.retryable_status_codes

    def test_custom_policy(self):
        """Test custom retry policy creation."""
        policy = RetryPolicy(
            max_attempts=5,
            base_delay_seconds=2.0,
            max_delay_seconds=120.0,
            exponential_base=3.0,
            jitter=False,
        )

        assert policy.max_attempts == 5
        assert policy.base_delay_seconds == 2.0
        assert policy.max_delay_seconds == 120.0
        assert policy.exponential_base == 3.0
        assert policy.jitter is False


class TestRetryManager:
    """Test cases for RetryManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.retry_manager = RetryManager()

    def test_successful_operation_no_retry(self):
        """Test successful operation that doesn't need retry."""
        mock_operation = Mock(return_value="success")

        result = self.retry_manager.execute_with_retry(
            mock_operation, operation_name="test_operation"
        )

        assert result == "success"
        assert mock_operation.call_count == 1

    def test_operation_succeeds_after_retries(self):
        """Test operation that succeeds after some failures."""
        mock_operation = Mock()
        # Fail twice, then succeed
        mock_operation.side_effect = [
            requests.exceptions.ConnectionError("Connection failed"),
            requests.exceptions.Timeout("Request timeout"),
            "success",
        ]

        with patch("time.sleep"):  # Mock sleep to speed up test
            result = self.retry_manager.execute_with_retry(
                mock_operation, operation_name="test_operation"
            )

        assert result == "success"
        assert mock_operation.call_count == 3

    def test_operation_fails_after_max_attempts(self):
        """Test operation that fails after max attempts."""
        mock_operation = Mock()
        mock_operation.side_effect = requests.exceptions.ConnectionError(
            "Connection failed"
        )

        with patch("time.sleep"):  # Mock sleep to speed up test
            with pytest.raises(requests.exceptions.ConnectionError):
                self.retry_manager.execute_with_retry(
                    mock_operation, operation_name="test_operation"
                )

        assert mock_operation.call_count == 3  # Default max_attempts

    def test_non_retryable_error_no_retry(self):
        """Test that non-retryable errors are not retried."""
        mock_operation = Mock()
        mock_operation.side_effect = ValueError("Invalid input")

        with pytest.raises(ValueError):
            self.retry_manager.execute_with_retry(
                mock_operation, operation_name="test_operation"
            )

        assert mock_operation.call_count == 1  # No retries

    def test_custom_retry_policy(self):
        """Test retry with custom policy."""
        policy = RetryPolicy(max_attempts=2, base_delay_seconds=0.1)
        mock_operation = Mock()
        mock_operation.side_effect = requests.exceptions.ConnectionError(
            "Connection failed"
        )

        with patch("time.sleep"):
            with pytest.raises(requests.exceptions.ConnectionError):
                self.retry_manager.execute_with_retry(
                    mock_operation, policy=policy, operation_name="test_operation"
                )

        assert mock_operation.call_count == 2  # Custom max_attempts

    def test_exponential_backoff_calculation(self):
        """Test exponential backoff delay calculation."""
        policy = RetryPolicy(
            base_delay_seconds=1.0,
            exponential_base=2.0,
            max_delay_seconds=60.0,
            jitter=False,  # Disable jitter for predictable testing
        )

        # Test delay calculations
        delay1 = self.retry_manager.calculate_delay(1, policy)
        delay2 = self.retry_manager.calculate_delay(2, policy)
        delay3 = self.retry_manager.calculate_delay(3, policy)

        assert delay1 == 1.0  # 1.0 * 2^0
        assert delay2 == 2.0  # 1.0 * 2^1
        assert delay3 == 4.0  # 1.0 * 2^2

    def test_max_delay_limit(self):
        """Test that delay is capped at max_delay_seconds."""
        policy = RetryPolicy(
            base_delay_seconds=10.0,
            exponential_base=2.0,
            max_delay_seconds=30.0,
            jitter=False,
        )

        # High attempt number should be capped
        delay = self.retry_manager.calculate_delay(10, policy)
        assert delay == 30.0  # Capped at max_delay_seconds

    def test_jitter_application(self):
        """Test that jitter is applied when enabled."""
        policy = RetryPolicy(
            base_delay_seconds=10.0,
            exponential_base=2.0,
            max_delay_seconds=60.0,
            jitter=True,
        )

        # With jitter, delay should be random between 0 and calculated delay
        delays = [self.retry_manager.calculate_delay(2, policy) for _ in range(10)]

        # All delays should be between 0 and 20.0 (base * exponential_base^1)
        for delay in delays:
            assert 0 <= delay <= 20.0

        # Delays should vary (not all the same)
        assert len(set(delays)) > 1

    def test_is_retryable_error_connection_error(self):
        """Test retryable error detection for connection errors."""
        policy = RetryPolicy()

        # Retryable errors
        assert self.retry_manager.is_retryable_error(
            requests.exceptions.ConnectionError("Connection failed"), policy
        )
        assert self.retry_manager.is_retryable_error(
            requests.exceptions.Timeout("Request timeout"), policy
        )

        # Non-retryable errors
        assert not self.retry_manager.is_retryable_error(
            ValueError("Invalid input"), policy
        )
        assert not self.retry_manager.is_retryable_error(
            KeyError("Missing key"), policy
        )

    def test_is_retryable_error_http_status_codes(self):
        """Test retryable error detection for HTTP status codes."""
        policy = RetryPolicy()

        # Create mock HTTP errors with different status codes
        def create_http_error(status_code):
            response = Mock()
            response.status_code = status_code
            error = requests.HTTPError("HTTP Error")
            error.response = response
            return error

        # Retryable status codes
        assert self.retry_manager.is_retryable_error(
            create_http_error(429), policy
        )  # Rate limit
        assert self.retry_manager.is_retryable_error(
            create_http_error(500), policy
        )  # Server error
        assert self.retry_manager.is_retryable_error(
            create_http_error(502), policy
        )  # Bad gateway
        assert self.retry_manager.is_retryable_error(
            create_http_error(503), policy
        )  # Service unavailable

        # Non-retryable status codes
        assert not self.retry_manager.is_retryable_error(
            create_http_error(400), policy
        )  # Bad request
        assert not self.retry_manager.is_retryable_error(
            create_http_error(401), policy
        )  # Unauthorized
        assert not self.retry_manager.is_retryable_error(
            create_http_error(404), policy
        )  # Not found

    def test_rate_limit_handling_retry_after_header(self):
        """Test rate limit handling with Retry-After header."""
        response = Mock()
        response.status_code = 429
        response.headers = {"Retry-After": "30"}

        delay = self.retry_manager.handle_rate_limit(response)
        assert delay == 30.0

    def test_rate_limit_handling_x_ratelimit_reset(self):
        """Test rate limit handling with X-RateLimit-Reset header."""
        response = Mock()
        response.status_code = 429
        future_time = time.time() + 45
        response.headers = {"X-RateLimit-Reset": str(future_time)}

        delay = self.retry_manager.handle_rate_limit(response)
        # Should be approximately 45 seconds (allowing for small timing differences)
        assert 40 <= delay <= 50

    def test_rate_limit_handling_no_headers(self):
        """Test rate limit handling when no rate limit headers are present."""
        response = Mock()
        response.status_code = 429
        response.headers = {}

        delay = self.retry_manager.handle_rate_limit(response)
        assert delay == 60.0  # Default delay

    def test_rate_limit_handling_non_rate_limit_status(self):
        """Test rate limit handling for non-429 status codes."""
        response = Mock()
        response.status_code = 500
        response.headers = {"Retry-After": "30"}

        delay = self.retry_manager.handle_rate_limit(response)
        assert delay == 0.0  # No delay for non-rate-limit errors

    def test_create_custom_policy(self):
        """Test creating custom retry policy with additional exceptions."""
        custom_policy = self.retry_manager.create_policy(
            max_attempts=5,
            base_delay_seconds=2.0,
            additional_retryable_exceptions=(IOError,),
            additional_retryable_status_codes=(418,),  # I'm a teapot
        )

        assert custom_policy.max_attempts == 5
        assert custom_policy.base_delay_seconds == 2.0
        assert IOError in custom_policy.retryable_exceptions
        assert (
            requests.exceptions.RequestException in custom_policy.retryable_exceptions
        )
        assert 418 in custom_policy.retryable_status_codes
        assert 429 in custom_policy.retryable_status_codes

    @patch("time.sleep")
    def test_retry_with_rate_limit_response(self, mock_sleep):
        """Test retry behavior when encountering rate limits."""
        mock_operation = Mock()

        # Create rate limit response
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"Retry-After": "10"}

        rate_limit_error = requests.HTTPError("Rate limited")
        rate_limit_error.response = rate_limit_response

        # First call fails with rate limit, second succeeds
        mock_operation.side_effect = [rate_limit_error, "success"]

        result = self.retry_manager.execute_with_retry(
            mock_operation, operation_name="test_operation"
        )

        assert result == "success"
        assert mock_operation.call_count == 2

        # Verify sleep was called with at least the rate limit delay
        mock_sleep.assert_called()
        sleep_delay = mock_sleep.call_args[0][0]
        assert sleep_delay >= 10.0  # Should respect rate limit delay

    def test_retry_manager_with_default_policy(self):
        """Test RetryManager initialization with default policy."""
        manager = RetryManager()
        assert manager.default_policy.max_attempts == 3

        custom_policy = RetryPolicy(max_attempts=5)
        manager_with_custom = RetryManager(custom_policy)
        assert manager_with_custom.default_policy.max_attempts == 5
