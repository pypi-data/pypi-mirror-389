"""Unit tests for ErrorHandler and error context capture."""

from datetime import datetime
from unittest.mock import Mock, patch

from beast_dream_snow_loader.operations.error_handler import (
    ErrorCategory,
    ErrorContext,
    ErrorHandler,
    ErrorSeverity,
    OperationalError,
)


class TestErrorHandler:
    """Test cases for ErrorHandler class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()

    def test_capture_error_creates_context(self):
        """Test that capture_error creates proper ErrorContext."""
        operation = "test_operation"
        exception = ValueError("Test error message")
        category = ErrorCategory.DATA_VALIDATION
        severity = ErrorSeverity.HIGH
        input_data = {"test_field": "test_value"}

        context = self.error_handler.capture_error(
            operation=operation,
            exception=exception,
            category=category,
            severity=severity,
            input_data=input_data,
        )

        assert isinstance(context, ErrorContext)
        assert context.operation == operation
        assert context.category == category
        assert context.severity == severity
        assert context.error_message == "Test error message"
        assert context.input_data == input_data
        assert context.stack_trace is not None
        assert context.correlation_id is not None
        assert isinstance(context.timestamp, datetime)
        assert context.environment_info is not None

    def test_capture_error_sanitizes_sensitive_data(self):
        """Test that sensitive data is sanitized in input_data."""
        input_data = {
            "username": "test_user",
            "password": "secret123",
            "api_key": "key123",
            "normal_field": "normal_value",
        }

        context = self.error_handler.capture_error(
            operation="test",
            exception=ValueError("test"),
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            input_data=input_data,
        )

        assert context.input_data["username"] == "test_user"
        assert context.input_data["password"] == "[REDACTED]"
        assert context.input_data["api_key"] == "[REDACTED]"
        assert context.input_data["normal_field"] == "normal_value"

    def test_capture_error_truncates_long_strings(self):
        """Test that very long strings are truncated."""
        long_string = "x" * 200
        input_data = {"long_field": long_string}

        context = self.error_handler.capture_error(
            operation="test",
            exception=ValueError("test"),
            category=ErrorCategory.DATA_VALIDATION,
            severity=ErrorSeverity.LOW,
            input_data=input_data,
        )

        assert len(context.input_data["long_field"]) <= 115  # 100 + "...[TRUNCATED]"
        assert context.input_data["long_field"].endswith("...[TRUNCATED]")

    def test_error_history_management(self):
        """Test that error history is properly managed."""
        # Add some errors
        for i in range(5):
            self.error_handler.capture_error(
                operation=f"test_{i}",
                exception=ValueError(f"Error {i}"),
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
            )

        history = self.error_handler.get_error_history()
        assert len(history) == 5

        # Test history limit
        limited_history = self.error_handler.get_error_history(limit=3)
        assert len(limited_history) == 3
        assert limited_history[-1].operation == "test_4"  # Most recent

    def test_error_aggregation(self):
        """Test error aggregation by category and severity."""
        # Add errors of different types
        self.error_handler.capture_error(
            "op1", ValueError("test"), ErrorCategory.NETWORK, ErrorSeverity.HIGH
        )
        self.error_handler.capture_error(
            "op2", ValueError("test"), ErrorCategory.NETWORK, ErrorSeverity.HIGH
        )
        self.error_handler.capture_error(
            "op3",
            ValueError("test"),
            ErrorCategory.DATA_VALIDATION,
            ErrorSeverity.MEDIUM,
        )

        aggregation = self.error_handler.aggregate_errors(time_window_minutes=60)

        assert aggregation["network_high"] == 2
        assert aggregation["data_validation_medium"] == 1

    def test_servicenow_error_handling(self):
        """Test ServiceNow-specific error handling."""
        # Mock response with JSON error
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.reason = "Bad Request"
        mock_response.url = "https://test.service-now.com/api/now/table/test"
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {
            "error": {
                "message": "Invalid table name",
                "detail": "Table 'invalid_table' does not exist",
                "code": "INVALID_TABLE",
            }
        }
        mock_response.request = Mock()
        mock_response.request.method = "POST"

        context = self.error_handler.handle_servicenow_error(
            response=mock_response,
            operation="create_record",
            input_data={"table": "invalid_table"},
        )

        assert context.category == ErrorCategory.SERVICENOW_API
        assert context.severity == ErrorSeverity.HIGH
        assert context.operation == "create_record"
        assert "Invalid table name" in context.error_message
        assert context.details["status_code"] == 400
        assert context.details["servicenow_error"]["message"] == "Invalid table name"
        assert context.details["servicenow_error"]["code"] == "INVALID_TABLE"

    def test_servicenow_error_with_rate_limit(self):
        """Test ServiceNow rate limit error handling."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.reason = "Too Many Requests"
        mock_response.url = "https://test.service-now.com/api/now/table/test"
        mock_response.headers = {
            "content-type": "application/json",
            "retry-after": "60",
        }
        mock_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}
        mock_response.request = Mock()
        mock_response.request.method = "GET"

        context = self.error_handler.handle_servicenow_error(
            mock_response, "query_records"
        )

        assert (
            context.severity == ErrorSeverity.MEDIUM
        )  # Rate limits are medium severity
        assert context.details["status_code"] == 429

    def test_servicenow_error_with_server_error(self):
        """Test ServiceNow server error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.url = "https://test.service-now.com/api/now/table/test"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = "Internal server error occurred"
        mock_response.json.side_effect = ValueError("No JSON")
        mock_response.request = Mock()
        mock_response.request.method = "POST"

        context = self.error_handler.handle_servicenow_error(
            mock_response, "create_record"
        )

        assert context.severity == ErrorSeverity.CRITICAL  # 5xx errors are critical
        assert (
            "Internal server error occurred"
            in context.details["servicenow_error"]["message"]
        )

    def test_authentication_error_handling(self):
        """Test authentication error handling with secure messaging."""
        auth_method = "api_key"
        details = "Invalid API key format"

        context = self.error_handler.handle_authentication_error(
            auth_method=auth_method, details=details, operation="authenticate"
        )

        assert context.category == ErrorCategory.AUTHENTICATION
        assert context.severity == ErrorSeverity.HIGH
        assert context.operation == "authenticate"
        assert auth_method in context.error_message
        assert details in context.error_message
        assert context.details["auth_method"] == auth_method
        assert context.details["secure_details"] == details

    def test_operational_error_exception(self):
        """Test OperationalError exception with context."""
        context = ErrorContext(
            operation="test_op",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            timestamp=datetime.utcnow(),
            error_message="Test error",
        )

        error = OperationalError(context)

        assert error.context == context
        assert str(error) == "Test error"

    @patch("platform.python_version")
    @patch("platform.platform")
    @patch("platform.node")
    @patch("os.getpid")
    @patch("os.getcwd")
    def test_environment_info_collection(
        self, mock_getcwd, mock_getpid, mock_node, mock_platform, mock_python_version
    ):
        """Test environment information collection."""
        mock_python_version.return_value = "3.10.0"
        mock_platform.return_value = "Linux-5.4.0"
        mock_node.return_value = "test-host"
        mock_getpid.return_value = 12345
        mock_getcwd.return_value = "/test/dir"

        context = self.error_handler.capture_error(
            "test", ValueError("test"), ErrorCategory.NETWORK, ErrorSeverity.LOW
        )

        env_info = context.environment_info
        assert env_info["python_version"] == "3.10.0"
        assert env_info["platform"] == "Linux-5.4.0"
        assert env_info["hostname"] == "test-host"
        assert env_info["process_id"] == 12345
        assert env_info["working_directory"] == "/test/dir"
        assert "environment_vars" in env_info

    def test_max_history_rotation(self):
        """Test that error history rotates when max is exceeded."""
        # Set a small max for testing
        self.error_handler._max_history = 3

        # Add more errors than max
        for i in range(5):
            self.error_handler.capture_error(
                f"test_{i}",
                ValueError(f"Error {i}"),
                ErrorCategory.NETWORK,
                ErrorSeverity.LOW,
            )

        history = self.error_handler.get_error_history()
        assert len(history) == 3
        # Should have the last 3 errors (2, 3, 4)
        assert history[0].operation == "test_2"
        assert history[1].operation == "test_3"
        assert history[2].operation == "test_4"
