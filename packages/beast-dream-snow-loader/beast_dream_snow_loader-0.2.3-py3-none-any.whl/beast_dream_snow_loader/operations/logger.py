"""Structured logging for operational resilience and debugging."""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .error_handler import ErrorContext


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            if record.exc_info is True:
                # Get current exception info
                import sys

                exc_info = sys.exc_info()
                if exc_info[0] is not None:
                    log_data["exception"] = self.formatException(exc_info)
            else:
                log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
            }:
                # Convert enum values to strings for JSON serialization
                if hasattr(value, "value"):
                    log_data[key] = value.value
                else:
                    log_data[key] = value

        # Convert any remaining enum values to strings for JSON serialization
        def json_serializer(obj):
            if hasattr(obj, "value"):  # Handle enums
                return obj.value
            return str(obj)

        return json.dumps(log_data, default=json_serializer, separators=(",", ":"))


class StructuredLogger:
    """Structured logger with operational context and multiple output targets."""

    def __init__(
        self,
        name: str,
        level: str = "INFO",
        console_output: bool = True,
        file_output: str | None = None,
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Set up structured formatter
        formatter = StructuredFormatter()

        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # File handler
        if file_output:
            file_path = Path(file_output)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(file_path)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        # Prevent propagation to root logger
        self.logger.propagate = False

    def log_operation_start(self, operation: str, context: dict[str, Any]) -> None:
        """Log the start of an operation with context."""
        self.logger.info(
            f"Operation started: {operation}",
            extra={
                "operation": operation,
                "operation_phase": "start",
                "context": context,
                "correlation_id": context.get("correlation_id"),
            },
        )

    def log_operation_complete(
        self, operation: str, duration_ms: int, success: bool, context: dict[str, Any]
    ) -> None:
        """Log the completion of an operation with timing and success status."""
        level = logging.INFO if success else logging.WARNING
        status = "success" if success else "failure"

        self.logger.log(
            level,
            f"Operation {status}: {operation} ({duration_ms}ms)",
            extra={
                "operation": operation,
                "operation_phase": "complete",
                "duration_ms": duration_ms,
                "success": success,
                "context": context,
                "correlation_id": context.get("correlation_id"),
            },
        )

    def log_error(self, error_context: ErrorContext) -> None:
        """Log an error with full operational context."""
        self.logger.error(
            f"Error in {error_context.operation}: {error_context.error_message}",
            extra={
                "operation": error_context.operation,
                "error_category": error_context.category.value,
                "error_severity": error_context.severity.value,
                "correlation_id": error_context.correlation_id,
                "error_details": error_context.details,
                "environment_info": error_context.environment_info,
                "input_data": error_context.input_data,
                "stack_trace": error_context.stack_trace,
            },
        )

    def log_credential_access(
        self, method: str, success: bool, details: str | None = None
    ) -> None:
        """Log credential access attempts without exposing sensitive data."""
        level = logging.INFO if success else logging.WARNING
        status = "success" if success else "failure"

        self.logger.log(
            level,
            f"Credential access {status}: {method}",
            extra={
                "operation": "credential_access",
                "auth_method": method,
                "success": success,
                "details": details,  # Should already be sanitized
                "security_event": True,
            },
        )

    def log_data_quality_issue(
        self, issue_type: str, affected_records: int, details: dict[str, Any]
    ) -> None:
        """Log data quality issues with affected record counts."""
        self.logger.warning(
            f"Data quality issue: {issue_type} ({affected_records} records affected)",
            extra={
                "operation": "data_quality_check",
                "issue_type": issue_type,
                "affected_records": affected_records,
                "details": details,
                "data_quality_event": True,
            },
        )

    def log_performance_metric(
        self, metric_name: str, value: float, unit: str, context: dict[str, Any]
    ) -> None:
        """Log performance metrics for monitoring and analysis."""
        self.logger.info(
            f"Performance metric: {metric_name} = {value} {unit}",
            extra={
                "operation": "performance_metric",
                "metric_name": metric_name,
                "metric_value": value,
                "metric_unit": unit,
                "context": context,
                "performance_event": True,
            },
        )

    def log_health_check(
        self,
        check_name: str,
        status: str,
        response_time_ms: float | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Log health check results."""
        level = logging.INFO if status == "healthy" else logging.WARNING

        self.logger.log(
            level,
            f"Health check: {check_name} = {status}",
            extra={
                "operation": "health_check",
                "check_name": check_name,
                "health_status": status,
                "response_time_ms": response_time_ms,
                "details": details or {},
                "health_event": True,
            },
        )

    def log_audit_event(
        self,
        event_type: str,
        resource: str,
        action: str,
        user_context: dict[str, Any] | None = None,
        additional_data: dict[str, Any] | None = None,
    ) -> None:
        """Log audit events for security and compliance."""
        self.logger.info(
            f"Audit event: {event_type} - {action} on {resource}",
            extra={
                "operation": "audit_event",
                "event_type": event_type,
                "resource": resource,
                "action": action,
                "user_context": user_context or {},
                "additional_data": additional_data or {},
                "audit_event": True,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )

    def log_circuit_breaker_event(
        self,
        circuit_name: str,
        old_state: str,
        new_state: str,
        failure_count: int = 0,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Log circuit breaker state changes."""
        self.logger.warning(
            f"Circuit breaker state change: {circuit_name} {old_state} -> {new_state}",
            extra={
                "operation": "circuit_breaker_event",
                "circuit_name": circuit_name,
                "old_state": old_state,
                "new_state": new_state,
                "failure_count": failure_count,
                "details": details or {},
                "resilience_event": True,
            },
        )

    def log_retry_attempt(
        self,
        operation: str,
        attempt: int,
        max_attempts: int,
        delay_seconds: float,
        error: str | None = None,
    ) -> None:
        """Log retry attempts for debugging."""
        self.logger.info(
            f"Retry attempt {attempt}/{max_attempts} for {operation} (delay: {delay_seconds}s)",
            extra={
                "operation": "retry_attempt",
                "target_operation": operation,
                "attempt": attempt,
                "max_attempts": max_attempts,
                "delay_seconds": delay_seconds,
                "error": error,
                "resilience_event": True,
            },
        )

    def debug(self, message: str, **kwargs) -> None:
        """Debug level logging with extra context."""
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Info level logging with extra context."""
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Warning level logging with extra context."""
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Error level logging with extra context."""
        self.logger.error(message, extra=kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Critical level logging with extra context."""
        self.logger.critical(message, extra=kwargs)
