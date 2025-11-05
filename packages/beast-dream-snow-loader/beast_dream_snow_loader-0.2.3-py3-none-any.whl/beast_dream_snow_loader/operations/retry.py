"""Retry management with exponential backoff and jitter for operational resilience."""

import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import requests

from .logger import StructuredLogger


@dataclass
class RetryPolicy:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple[type[Exception], ...] = (
        requests.exceptions.RequestException,
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.HTTPError,
    )
    retryable_status_codes: tuple[int, ...] = (429, 500, 502, 503, 504)


class RetryManager:
    """Manages retry logic with exponential backoff and jitter."""

    def __init__(self, default_policy: RetryPolicy | None = None):
        self.default_policy = default_policy or RetryPolicy()
        self.logger = StructuredLogger("retry_manager")

    def execute_with_retry(
        self,
        operation: Callable[[], Any],
        policy: RetryPolicy | None = None,
        operation_name: str = "unknown",
    ) -> Any:
        """Execute operation with retry logic."""
        retry_policy = policy or self.default_policy
        last_exception = None

        for attempt in range(1, retry_policy.max_attempts + 1):
            try:
                # Log attempt (except first one)
                if attempt > 1:
                    self.logger.log_retry_attempt(
                        operation_name,
                        attempt,
                        retry_policy.max_attempts,
                        0,  # Delay already applied
                        str(last_exception) if last_exception else None,
                    )

                # Execute the operation
                result = operation()

                # If we get here, operation succeeded
                if attempt > 1:
                    self.logger.info(
                        f"Operation {operation_name} succeeded on attempt {attempt}",
                        operation=operation_name,
                        attempt=attempt,
                        total_attempts=retry_policy.max_attempts,
                        resilience_event=True,
                    )

                return result

            except Exception as e:
                last_exception = e

                # Check if this is the last attempt
                if attempt == retry_policy.max_attempts:
                    self.logger.error(
                        f"Operation {operation_name} failed after {attempt} attempts",
                        operation=operation_name,
                        final_attempt=attempt,
                        total_attempts=retry_policy.max_attempts,
                        final_error=str(e),
                        resilience_event=True,
                    )
                    raise e

                # Check if error is retryable
                if not self.is_retryable_error(e, retry_policy):
                    self.logger.warning(
                        f"Operation {operation_name} failed with non-retryable error",
                        operation=operation_name,
                        attempt=attempt,
                        error=str(e),
                        error_type=type(e).__name__,
                        resilience_event=True,
                    )
                    raise e

                # Calculate delay for next attempt
                delay = self.calculate_delay(attempt, retry_policy)

                # Handle rate limiting specially
                if isinstance(e, requests.HTTPError) and hasattr(e, "response"):
                    rate_limit_delay = self.handle_rate_limit(e.response)
                    if rate_limit_delay > 0:
                        delay = max(delay, rate_limit_delay)

                self.logger.log_retry_attempt(
                    operation_name,
                    attempt + 1,  # Next attempt number
                    retry_policy.max_attempts,
                    delay,
                    str(e),
                )

                # Wait before retry
                time.sleep(delay)

        # This should never be reached, but just in case
        raise last_exception or RuntimeError("Retry loop completed without result")

    def is_retryable_error(self, exception: Exception, policy: RetryPolicy) -> bool:
        """Determine if an error is retryable based on policy."""
        # Check exception type
        if not isinstance(exception, policy.retryable_exceptions):
            return False

        # For HTTP errors, check status code
        if isinstance(exception, requests.HTTPError) and hasattr(exception, "response"):
            status_code = exception.response.status_code
            return status_code in policy.retryable_status_codes

        # For other request exceptions, they're generally retryable
        if isinstance(
            exception,
            (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout,
            ),
        ):
            return True

        return False

    def calculate_delay(self, attempt: int, policy: RetryPolicy) -> float:
        """Calculate delay for retry attempt with exponential backoff and jitter."""
        # Calculate exponential backoff
        delay = policy.base_delay_seconds * (policy.exponential_base ** (attempt - 1))

        # Apply maximum delay limit
        delay = min(delay, policy.max_delay_seconds)

        # Apply jitter to avoid thundering herd
        if policy.jitter:
            # Use full jitter: random value between 0 and calculated delay
            delay = random.uniform(0, delay)

        return delay

    def handle_rate_limit(self, response: requests.Response) -> float:
        """Extract rate limit delay from response headers."""
        if response.status_code != 429:
            return 0.0

        # Check for Retry-After header (standard)
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                # Can be seconds (integer) or HTTP date
                return float(retry_after)
            except ValueError:
                # If it's a date, we'll use default delay
                pass

        # Check for X-RateLimit-Reset header (common alternative)
        rate_limit_reset = response.headers.get("X-RateLimit-Reset")
        if rate_limit_reset:
            try:
                # Usually Unix timestamp
                reset_time = float(rate_limit_reset)
                current_time = time.time()
                delay = max(0, reset_time - current_time)
                return delay
            except ValueError:
                pass

        # Check for X-Rate-Limit-Retry-After-Seconds
        retry_after_seconds = response.headers.get("X-Rate-Limit-Retry-After-Seconds")
        if retry_after_seconds:
            try:
                return float(retry_after_seconds)
            except ValueError:
                pass

        # Default rate limit delay if no header found
        self.logger.warning(
            "Rate limit encountered but no retry delay header found, using default",
            status_code=response.status_code,
            headers=dict(response.headers),
            resilience_event=True,
        )
        return 60.0  # Default 1 minute delay

    def create_policy(
        self,
        max_attempts: int = 3,
        base_delay_seconds: float = 1.0,
        max_delay_seconds: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        additional_retryable_exceptions: tuple[type[Exception], ...] | None = None,
        additional_retryable_status_codes: tuple[int, ...] | None = None,
    ) -> RetryPolicy:
        """Create a custom retry policy."""
        retryable_exceptions = RetryPolicy.retryable_exceptions
        if additional_retryable_exceptions:
            retryable_exceptions = (
                retryable_exceptions + additional_retryable_exceptions
            )

        retryable_status_codes = RetryPolicy.retryable_status_codes
        if additional_retryable_status_codes:
            retryable_status_codes = (
                retryable_status_codes + additional_retryable_status_codes
            )

        return RetryPolicy(
            max_attempts=max_attempts,
            base_delay_seconds=base_delay_seconds,
            max_delay_seconds=max_delay_seconds,
            exponential_base=exponential_base,
            jitter=jitter,
            retryable_exceptions=retryable_exceptions,
            retryable_status_codes=retryable_status_codes,
        )
