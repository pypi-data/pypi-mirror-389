"""Error handling and context capture for operational resilience."""

import os
import platform
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import requests


class ErrorSeverity(Enum):
    """Error severity levels for operational classification."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for operational classification."""

    AUTHENTICATION = "authentication"
    NETWORK = "network"
    DATA_VALIDATION = "data_validation"
    SERVICENOW_API = "servicenow_api"
    TRANSFORMATION = "transformation"
    CONFIGURATION = "configuration"


@dataclass
class ErrorContext:
    """Comprehensive error context for debugging and analysis."""

    operation: str
    category: ErrorCategory
    severity: ErrorSeverity
    timestamp: datetime
    error_message: str
    stack_trace: str | None = None
    input_data: dict[str, Any] | None = None
    environment_info: dict[str, Any] = field(default_factory=dict)
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    details: dict[str, Any] = field(default_factory=dict)


class OperationalError(Exception):
    """Exception that carries operational error context."""

    def __init__(self, context: ErrorContext):
        self.context = context
        super().__init__(context.error_message)


class ErrorHandler:
    """Centralized error handling and context capture."""

    def __init__(self):
        self._error_history: list[ErrorContext] = []
        self._max_history = 1000  # Keep last 1000 errors

    def capture_error(
        self,
        operation: str,
        exception: Exception,
        category: ErrorCategory,
        severity: ErrorSeverity,
        input_data: dict[str, Any] | None = None,
        additional_details: dict[str, Any] | None = None,
    ) -> ErrorContext:
        """Capture comprehensive error context."""
        context = ErrorContext(
            operation=operation,
            category=category,
            severity=severity,
            timestamp=datetime.utcnow(),
            error_message=str(exception),
            stack_trace=traceback.format_exc(),
            input_data=self._sanitize_input_data(input_data),
            environment_info=self._get_environment_info(),
            details=additional_details or {},
        )

        # Add to history (with rotation)
        self._error_history.append(context)
        if len(self._error_history) > self._max_history:
            self._error_history.pop(0)

        return context

    def handle_servicenow_error(
        self,
        response: requests.Response,
        operation: str,
        input_data: dict[str, Any] | None = None,
    ) -> ErrorContext:
        """Handle ServiceNow-specific API errors with detailed parsing."""
        error_details = self._parse_servicenow_error(response)

        # Determine severity based on status code
        severity = self._determine_severity_from_status(response.status_code)

        # Create synthetic exception for context
        error_message = f"ServiceNow API Error: {response.status_code} - {error_details.get('message', 'Unknown error')}"
        exception = requests.HTTPError(error_message, response=response)

        return self.capture_error(
            operation=operation,
            exception=exception,
            category=ErrorCategory.SERVICENOW_API,
            severity=severity,
            input_data=input_data,
            additional_details={
                "status_code": response.status_code,
                "response_headers": dict(response.headers),
                "servicenow_error": error_details,
                "url": getattr(response, "url", "unknown"),
                "method": response.request.method if response.request else "unknown",
            },
        )

    def handle_authentication_error(
        self, auth_method: str, details: str, operation: str = "authentication"
    ) -> ErrorContext:
        """Handle authentication-specific errors with secure messaging."""
        # Create secure error message (no credential exposure)
        secure_message = f"Authentication failed using {auth_method}: {details}"

        exception = ValueError(secure_message)

        return self.capture_error(
            operation=operation,
            exception=exception,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            additional_details={
                "auth_method": auth_method,
                "secure_details": details,  # Already sanitized by caller
            },
        )

    def aggregate_errors(self, time_window_minutes: int = 60) -> dict[str, int]:
        """Aggregate error patterns within a time window."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)

        recent_errors = [
            error for error in self._error_history if error.timestamp >= cutoff_time
        ]

        # Aggregate by category and severity
        aggregation = {}
        for error in recent_errors:
            key = f"{error.category.value}_{error.severity.value}"
            aggregation[key] = aggregation.get(key, 0) + 1

        return aggregation

    def get_error_history(self, limit: int = 100) -> list[ErrorContext]:
        """Get recent error history for analysis."""
        return self._error_history[-limit:]

    def _sanitize_input_data(
        self, input_data: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        """Sanitize input data to remove sensitive information."""
        if not input_data:
            return None

        # List of sensitive keys to redact
        sensitive_keys = {
            "password",
            "api_key",
            "token",
            "secret",
            "credential",
            "auth",
            "authorization",
            "key",
            "pass",
            "pwd",
        }

        sanitized = {}
        for key, value in input_data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_input_data(value)
            elif isinstance(value, str) and len(value) > 100:
                # Truncate very long strings
                sanitized[key] = value[:100] + "...[TRUNCATED]"
            else:
                sanitized[key] = value

        return sanitized

    def _get_environment_info(self) -> dict[str, Any]:
        """Collect environment information for debugging."""
        return {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "hostname": platform.node(),
            "process_id": os.getpid(),
            "working_directory": os.getcwd(),
            "environment_vars": {
                key: value
                for key, value in os.environ.items()
                if not any(
                    sensitive in key.lower()
                    for sensitive in ["password", "key", "token", "secret", "auth"]
                )
            },
        }

    def _parse_servicenow_error(self, response: requests.Response) -> dict[str, Any]:
        """Parse ServiceNow error response for detailed information."""
        error_info = {
            "status_code": response.status_code,
            "reason": response.reason,
            "message": "Unknown ServiceNow error",
        }

        try:
            # Try to parse JSON error response
            if response.headers.get("content-type", "").startswith("application/json"):
                json_data = response.json()

                # ServiceNow error formats
                if "error" in json_data:
                    error_data = json_data["error"]
                    if isinstance(error_data, dict):
                        error_info.update(
                            {
                                "message": error_data.get(
                                    "message", "ServiceNow API error"
                                ),
                                "detail": error_data.get("detail"),
                            }
                        )
                        if "code" in error_data:
                            error_info["code"] = error_data["code"]
                    else:
                        error_info["message"] = str(error_data)

                # Alternative ServiceNow error format
                elif "result" in json_data and isinstance(json_data["result"], dict):
                    result = json_data["result"]
                    if "error_message" in result:
                        error_info["message"] = result["error_message"]
            else:
                # For non-JSON responses, use response text
                if hasattr(response, "text") and response.text:
                    error_info["message"] = response.text[:500]

        except (ValueError, KeyError) as e:
            # If JSON parsing fails, use response text
            if hasattr(response, "text") and response.text:
                error_info["message"] = response.text[:500]
            else:
                error_info["message"] = "No error details available"
            error_info["parse_error"] = str(e)

        return error_info

    def _determine_severity_from_status(self, status_code: int) -> ErrorSeverity:
        """Determine error severity based on HTTP status code."""
        if status_code >= 500:
            return ErrorSeverity.CRITICAL
        elif status_code == 429:  # Rate limit
            return ErrorSeverity.MEDIUM
        elif status_code >= 400:
            return ErrorSeverity.HIGH
        else:
            return ErrorSeverity.LOW
