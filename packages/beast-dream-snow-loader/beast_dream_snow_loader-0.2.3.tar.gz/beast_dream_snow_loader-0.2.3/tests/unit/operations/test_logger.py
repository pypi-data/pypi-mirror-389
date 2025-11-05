"""Unit tests for StructuredLogger and logging functionality."""

import json
import logging
import tempfile
from datetime import datetime
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from beast_dream_snow_loader.operations.error_handler import (
    ErrorCategory,
    ErrorContext,
    ErrorSeverity,
)
from beast_dream_snow_loader.operations.logger import (
    StructuredFormatter,
    StructuredLogger,
)


class TestStructuredFormatter:
    """Test cases for StructuredFormatter class."""

    def test_format_basic_record(self):
        """Test formatting of basic log record."""
        formatter = StructuredFormatter()

        # Create a log record
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.funcName = "test_function"
        record.module = "test_module"

        formatted = formatter.format(record)
        log_data = json.loads(formatted)

        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test.logger"
        assert log_data["message"] == "Test message"
        assert log_data["module"] == "test_module"
        assert log_data["function"] == "test_function"
        assert log_data["line"] == 42
        assert "timestamp" in log_data

    def test_format_with_exception(self):
        """Test formatting with exception information."""
        formatter = StructuredFormatter()

        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys

            exc_info = sys.exc_info()
            record = logging.LogRecord(
                name="test.logger",
                level=logging.ERROR,
                pathname="/test/path.py",
                lineno=42,
                msg="Error occurred",
                args=(),
                exc_info=exc_info,
            )
            record.funcName = "test_function"
            record.module = "test_module"

        formatted = formatter.format(record)
        log_data = json.loads(formatted)

        assert "exception" in log_data
        assert "ValueError: Test exception" in log_data["exception"]

    def test_format_with_extra_fields(self):
        """Test formatting with extra fields."""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.funcName = "test_function"
        record.module = "test_module"
        record.operation = "test_operation"
        record.correlation_id = "test-123"

        formatted = formatter.format(record)
        log_data = json.loads(formatted)

        assert log_data["operation"] == "test_operation"
        assert log_data["correlation_id"] == "test-123"


class TestStructuredLogger:
    """Test cases for StructuredLogger class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.logger_name = "test.logger"

    def test_logger_initialization_console_only(self):
        """Test logger initialization with console output only."""
        logger = StructuredLogger(self.logger_name, level="DEBUG", console_output=True)

        assert logger.logger.name == self.logger_name
        assert logger.logger.level == logging.DEBUG
        assert len(logger.logger.handlers) == 1
        assert isinstance(logger.logger.handlers[0], logging.StreamHandler)

    def test_logger_initialization_with_file(self):
        """Test logger initialization with file output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"

            logger = StructuredLogger(
                self.logger_name,
                level="INFO",
                console_output=False,
                file_output=str(log_file),
            )

            assert len(logger.logger.handlers) == 1
            assert isinstance(logger.logger.handlers[0], logging.FileHandler)
            assert log_file.exists()

    def test_log_operation_start(self):
        """Test logging operation start."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            logger = StructuredLogger(self.logger_name, console_output=True)

            context = {"correlation_id": "test-123", "user": "test_user"}
            logger.log_operation_start("test_operation", context)

            output = mock_stdout.getvalue()
            log_data = json.loads(output.strip())

            assert "Operation started: test_operation" in log_data["message"]
            assert log_data["operation"] == "test_operation"
            assert log_data["operation_phase"] == "start"
            assert log_data["context"] == context
            assert log_data["correlation_id"] == "test-123"

    def test_log_operation_complete_success(self):
        """Test logging successful operation completion."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            logger = StructuredLogger(self.logger_name, console_output=True)

            context = {"correlation_id": "test-123"}
            logger.log_operation_complete("test_operation", 150, True, context)

            output = mock_stdout.getvalue()
            log_data = json.loads(output.strip())

            assert "Operation success: test_operation (150ms)" in log_data["message"]
            assert log_data["operation"] == "test_operation"
            assert log_data["operation_phase"] == "complete"
            assert log_data["duration_ms"] == 150
            assert log_data["success"] is True
            assert log_data["level"] == "INFO"

    def test_log_operation_complete_failure(self):
        """Test logging failed operation completion."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            logger = StructuredLogger(self.logger_name, console_output=True)

            context = {"correlation_id": "test-123"}
            logger.log_operation_complete("test_operation", 250, False, context)

            output = mock_stdout.getvalue()
            log_data = json.loads(output.strip())

            assert "Operation failure: test_operation (250ms)" in log_data["message"]
            assert log_data["success"] is False
            assert log_data["level"] == "WARNING"

    def test_log_error_with_context(self):
        """Test logging error with full context."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            logger = StructuredLogger(self.logger_name, console_output=True)

            error_context = ErrorContext(
                operation="test_operation",
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.HIGH,
                timestamp=datetime.utcnow(),
                error_message="Connection failed",
                correlation_id="test-123",
                details={"host": "example.com", "port": 443},
            )

            logger.log_error(error_context)

            output = mock_stdout.getvalue()
            log_data = json.loads(output.strip())

            assert "Error in test_operation: Connection failed" in log_data["message"]
            assert log_data["operation"] == "test_operation"
            assert log_data["error_category"] == "network"
            assert log_data["error_severity"] == "high"
            assert log_data["correlation_id"] == "test-123"
            assert log_data["error_details"]["host"] == "example.com"
            assert log_data["level"] == "ERROR"

    def test_log_credential_access_success(self):
        """Test logging successful credential access."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            logger = StructuredLogger(self.logger_name, console_output=True)

            logger.log_credential_access("1password_cli", True, "Retrieved from vault")

            output = mock_stdout.getvalue()
            log_data = json.loads(output.strip())

            assert "Credential access success: 1password_cli" in log_data["message"]
            assert log_data["auth_method"] == "1password_cli"
            assert log_data["success"] is True
            assert log_data["security_event"] is True
            assert log_data["level"] == "INFO"

    def test_log_credential_access_failure(self):
        """Test logging failed credential access."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            logger = StructuredLogger(self.logger_name, console_output=True)

            logger.log_credential_access("api_key", False, "Invalid format")

            output = mock_stdout.getvalue()
            log_data = json.loads(output.strip())

            assert "Credential access failure: api_key" in log_data["message"]
            assert log_data["success"] is False
            assert log_data["level"] == "WARNING"

    def test_log_data_quality_issue(self):
        """Test logging data quality issues."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            logger = StructuredLogger(self.logger_name, console_output=True)

            details = {
                "missing_fields": ["hostname", "ip_address"],
                "invalid_records": [{"id": "123", "reason": "invalid IP"}],
            }

            logger.log_data_quality_issue("missing_required_fields", 5, details)

            output = mock_stdout.getvalue()
            log_data = json.loads(output.strip())

            assert (
                "Data quality issue: missing_required_fields (5 records affected)"
                in log_data["message"]
            )
            assert log_data["issue_type"] == "missing_required_fields"
            assert log_data["affected_records"] == 5
            assert log_data["details"] == details
            assert log_data["data_quality_event"] is True
            assert log_data["level"] == "WARNING"

    def test_log_performance_metric(self):
        """Test logging performance metrics."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            logger = StructuredLogger(self.logger_name, console_output=True)

            context = {"operation": "data_load", "batch_size": 100}
            logger.log_performance_metric("response_time", 245.5, "ms", context)

            output = mock_stdout.getvalue()
            log_data = json.loads(output.strip())

            assert "Performance metric: response_time = 245.5 ms" in log_data["message"]
            assert log_data["metric_name"] == "response_time"
            assert log_data["metric_value"] == 245.5
            assert log_data["metric_unit"] == "ms"
            assert log_data["context"] == context
            assert log_data["performance_event"] is True

    def test_log_health_check_healthy(self):
        """Test logging healthy health check."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            logger = StructuredLogger(self.logger_name, console_output=True)

            details = {"endpoint": "/api/health", "status_code": 200}
            logger.log_health_check("servicenow_api", "healthy", 150.0, details)

            output = mock_stdout.getvalue()
            log_data = json.loads(output.strip())

            assert "Health check: servicenow_api = healthy" in log_data["message"]
            assert log_data["check_name"] == "servicenow_api"
            assert log_data["health_status"] == "healthy"
            assert log_data["response_time_ms"] == 150.0
            assert log_data["details"] == details
            assert log_data["health_event"] is True
            assert log_data["level"] == "INFO"

    def test_log_health_check_unhealthy(self):
        """Test logging unhealthy health check."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            logger = StructuredLogger(self.logger_name, console_output=True)

            logger.log_health_check(
                "database", "unhealthy", None, {"error": "Connection timeout"}
            )

            output = mock_stdout.getvalue()
            log_data = json.loads(output.strip())

            assert log_data["health_status"] == "unhealthy"
            assert log_data["level"] == "WARNING"

    def test_log_audit_event(self):
        """Test logging audit events."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            logger = StructuredLogger(self.logger_name, console_output=True)

            user_context = {"user_id": "admin", "session_id": "sess-123"}
            additional_data = {"record_count": 50, "table": "cmdb_ci"}

            logger.log_audit_event(
                "data_modification",
                "servicenow_records",
                "bulk_create",
                user_context,
                additional_data,
            )

            output = mock_stdout.getvalue()
            log_data = json.loads(output.strip())

            assert (
                "Audit event: data_modification - bulk_create on servicenow_records"
                in log_data["message"]
            )
            assert log_data["event_type"] == "data_modification"
            assert log_data["resource"] == "servicenow_records"
            assert log_data["action"] == "bulk_create"
            assert log_data["user_context"] == user_context
            assert log_data["additional_data"] == additional_data
            assert log_data["audit_event"] is True

    def test_log_circuit_breaker_event(self):
        """Test logging circuit breaker events."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            logger = StructuredLogger(self.logger_name, console_output=True)

            details = {"last_error": "Connection timeout", "threshold": 5}
            logger.log_circuit_breaker_event(
                "servicenow_api", "closed", "open", 5, details
            )

            output = mock_stdout.getvalue()
            log_data = json.loads(output.strip())

            assert (
                "Circuit breaker state change: servicenow_api closed -> open"
                in log_data["message"]
            )
            assert log_data["circuit_name"] == "servicenow_api"
            assert log_data["old_state"] == "closed"
            assert log_data["new_state"] == "open"
            assert log_data["failure_count"] == 5
            assert log_data["details"] == details
            assert log_data["resilience_event"] is True
            assert log_data["level"] == "WARNING"

    def test_log_retry_attempt(self):
        """Test logging retry attempts."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            logger = StructuredLogger(self.logger_name, console_output=True)

            logger.log_retry_attempt("api_request", 2, 3, 4.0, "Connection timeout")

            output = mock_stdout.getvalue()
            log_data = json.loads(output.strip())

            assert (
                "Retry attempt 2/3 for api_request (delay: 4.0s)" in log_data["message"]
            )
            assert log_data["target_operation"] == "api_request"
            assert log_data["attempt"] == 2
            assert log_data["max_attempts"] == 3
            assert log_data["delay_seconds"] == 4.0
            assert log_data["error"] == "Connection timeout"
            assert log_data["resilience_event"] is True

    def test_basic_logging_methods(self):
        """Test basic logging methods (debug, info, warning, error, critical)."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            logger = StructuredLogger(
                self.logger_name, console_output=True, level="DEBUG"
            )

            logger.debug("Debug message", extra_field="debug_value")
            logger.info("Info message", extra_field="info_value")
            logger.warning("Warning message", extra_field="warning_value")
            logger.error("Error message", extra_field="error_value")
            logger.critical("Critical message", extra_field="critical_value")

            output = mock_stdout.getvalue()
            lines = output.strip().split("\n")

            assert len(lines) == 5

            # Check each log level
            debug_log = json.loads(lines[0])
            assert debug_log["level"] == "DEBUG"
            assert debug_log["message"] == "Debug message"
            assert debug_log["extra_field"] == "debug_value"

            info_log = json.loads(lines[1])
            assert info_log["level"] == "INFO"

            warning_log = json.loads(lines[2])
            assert warning_log["level"] == "WARNING"

            error_log = json.loads(lines[3])
            assert error_log["level"] == "ERROR"

            critical_log = json.loads(lines[4])
            assert critical_log["level"] == "CRITICAL"

    def test_logger_propagation_disabled(self):
        """Test that logger propagation is disabled."""
        logger = StructuredLogger(self.logger_name, console_output=True)
        assert logger.logger.propagate is False
