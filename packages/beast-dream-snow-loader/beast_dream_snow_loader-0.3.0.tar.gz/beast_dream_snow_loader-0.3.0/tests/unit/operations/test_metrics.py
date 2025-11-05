"""Unit tests for MetricsCollector and metrics functionality."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from beast_dream_snow_loader.operations.metrics import (
    MetricsCollector,
    OperationMetrics,
    SystemMetrics,
)


class TestOperationMetrics:
    """Test cases for OperationMetrics dataclass."""

    def test_operation_metrics_creation(self):
        """Test OperationMetrics creation and default values."""
        metrics = OperationMetrics("test_operation")

        assert metrics.operation_name == "test_operation"
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.total_response_time_ms == 0.0
        assert metrics.min_response_time_ms == float("inf")
        assert metrics.max_response_time_ms == 0.0
        assert len(metrics.response_times) == 0

    def test_average_response_time_calculation(self):
        """Test average response time calculation."""
        metrics = OperationMetrics("test_operation")
        metrics.total_requests = 3
        metrics.total_response_time_ms = 600.0

        assert metrics.average_response_time_ms == 200.0

    def test_average_response_time_no_requests(self):
        """Test average response time with no requests."""
        metrics = OperationMetrics("test_operation")

        assert metrics.average_response_time_ms == 0.0

    def test_error_rate_calculation(self):
        """Test error rate percentage calculation."""
        metrics = OperationMetrics("test_operation")
        metrics.total_requests = 10
        metrics.failed_requests = 2

        assert metrics.error_rate_percent == 20.0

    def test_success_rate_calculation(self):
        """Test success rate percentage calculation."""
        metrics = OperationMetrics("test_operation")
        metrics.total_requests = 10
        metrics.successful_requests = 8

        assert metrics.success_rate_percent == 80.0

    def test_percentile_calculation(self):
        """Test percentile calculation."""
        metrics = OperationMetrics("test_operation")
        # Add response times: 100, 200, 300, 400, 500
        for time_ms in [100, 200, 300, 400, 500]:
            metrics.response_times.append(time_ms)

        # 95th percentile of [100, 200, 300, 400, 500] should be 500
        assert metrics.get_percentile(95.0) == 500

        # 50th percentile should be 300 (index 2 of 5 items)
        assert metrics.get_percentile(50.0) == 300

    def test_percentile_empty_response_times(self):
        """Test percentile calculation with no response times."""
        metrics = OperationMetrics("test_operation")

        assert metrics.get_percentile(95.0) == 0.0

    def test_p95_and_p99_properties(self):
        """Test P95 and P99 response time properties."""
        metrics = OperationMetrics("test_operation")
        for time_ms in range(1, 101):  # 1 to 100
            metrics.response_times.append(time_ms)

        assert metrics.p95_response_time_ms == 96.0
        assert metrics.p99_response_time_ms == 100.0


class TestSystemMetrics:
    """Test cases for SystemMetrics dataclass."""

    def test_system_metrics_creation(self):
        """Test SystemMetrics creation with default values."""
        metrics = SystemMetrics()

        assert metrics.memory_usage_mb == 0.0
        assert metrics.cpu_usage_percent == 0.0
        assert metrics.active_connections == 0
        assert metrics.circuit_breaker_states == {}
        assert metrics.health_status == "unknown"
        assert metrics.uptime_seconds == 0
        assert isinstance(metrics.timestamp, datetime)

    def test_system_metrics_with_values(self):
        """Test SystemMetrics creation with specific values."""
        circuit_states = {"api": "closed", "db": "open"}

        metrics = SystemMetrics(
            memory_usage_mb=1024.0,
            cpu_usage_percent=45.5,
            active_connections=10,
            circuit_breaker_states=circuit_states,
            health_status="healthy",
            uptime_seconds=3600,
        )

        assert metrics.memory_usage_mb == 1024.0
        assert metrics.cpu_usage_percent == 45.5
        assert metrics.active_connections == 10
        assert metrics.circuit_breaker_states == circuit_states
        assert metrics.health_status == "healthy"
        assert metrics.uptime_seconds == 3600


class TestMetricsCollector:
    """Test cases for MetricsCollector class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.metrics_collector = MetricsCollector()

    def test_initialization(self):
        """Test MetricsCollector initialization."""
        collector = MetricsCollector(max_history_hours=48)

        assert collector.max_history_hours == 48
        assert isinstance(collector.start_time, datetime)
        assert len(collector.operation_metrics) == 0
        assert len(collector.system_metrics_history) == 0
        assert len(collector.request_history) == 0
        assert len(collector.error_history) == 0

    def test_record_successful_request(self):
        """Test recording a successful request."""
        self.metrics_collector.record_request(
            operation="test_api_call",
            response_time_ms=150.0,
            success=True,
            additional_context={"endpoint": "/api/test"},
        )

        # Check operation metrics
        metrics = self.metrics_collector.get_operation_metrics("test_api_call")
        assert metrics is not None
        assert metrics.operation_name == "test_api_call"
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1
        assert metrics.failed_requests == 0
        assert metrics.total_response_time_ms == 150.0
        assert metrics.min_response_time_ms == 150.0
        assert metrics.max_response_time_ms == 150.0
        assert len(metrics.response_times) == 1
        assert metrics.response_times[0] == 150.0

        # Check request history
        assert len(self.metrics_collector.request_history) == 1
        request = self.metrics_collector.request_history[0]
        assert request["operation"] == "test_api_call"
        assert request["response_time_ms"] == 150.0
        assert request["success"] is True
        assert request["context"]["endpoint"] == "/api/test"

    def test_record_failed_request(self):
        """Test recording a failed request."""
        self.metrics_collector.record_request(
            operation="test_api_call", response_time_ms=2000.0, success=False
        )

        metrics = self.metrics_collector.get_operation_metrics("test_api_call")
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 1
        assert metrics.error_rate_percent == 100.0

    def test_record_multiple_requests(self):
        """Test recording multiple requests for the same operation."""
        # Record 3 successful and 2 failed requests
        response_times = [
            100.0,
            150.0,
            200.0,
            500.0,
            600.0,
        ]  # Total: 1550.0, Average: 310.0
        success_flags = [True, True, True, False, False]

        for _i, (time_ms, success) in enumerate(
            zip(response_times, success_flags, strict=True)
        ):
            self.metrics_collector.record_request("api_call", time_ms, success)

        metrics = self.metrics_collector.get_operation_metrics("api_call")
        assert metrics.total_requests == 5
        assert metrics.successful_requests == 3
        assert metrics.failed_requests == 2
        assert metrics.success_rate_percent == 60.0
        assert metrics.error_rate_percent == 40.0
        assert metrics.min_response_time_ms == 100.0
        assert metrics.max_response_time_ms == 600.0
        assert (
            metrics.average_response_time_ms == 310.0
        )  # (100+150+200+500+600)/5 = 1550/5

    def test_record_error(self):
        """Test recording an error."""
        self.metrics_collector.record_error(
            operation="test_operation",
            error_type="ConnectionError",
            error_message="Failed to connect to server",
            additional_context={"host": "example.com"},
        )

        assert len(self.metrics_collector.error_history) == 1
        error = self.metrics_collector.error_history[0]
        assert error["operation"] == "test_operation"
        assert error["error_type"] == "ConnectionError"
        assert error["error_message"] == "Failed to connect to server"
        assert error["context"]["host"] == "example.com"

    def test_record_system_metrics(self):
        """Test recording system metrics."""
        system_metrics = SystemMetrics(
            memory_usage_mb=2048.0,
            cpu_usage_percent=65.5,
            active_connections=25,
            health_status="healthy",
        )

        self.metrics_collector.record_system_metrics(system_metrics)

        assert len(self.metrics_collector.system_metrics_history) == 1
        recorded_metrics = self.metrics_collector.get_system_metrics()
        assert recorded_metrics is not None
        assert recorded_metrics.memory_usage_mb == 2048.0
        assert recorded_metrics.cpu_usage_percent == 65.5
        assert recorded_metrics.active_connections == 25
        assert recorded_metrics.health_status == "healthy"
        assert (
            recorded_metrics.uptime_seconds >= 0
        )  # Uptime is calculated from start_time

    def test_get_operation_metrics_nonexistent(self):
        """Test getting metrics for non-existent operation."""
        metrics = self.metrics_collector.get_operation_metrics("nonexistent")
        assert metrics is None

    def test_get_all_operation_metrics(self):
        """Test getting all operation metrics."""
        self.metrics_collector.record_request("op1", 100.0, True)
        self.metrics_collector.record_request("op2", 200.0, False)

        all_metrics = self.metrics_collector.get_all_operation_metrics()

        assert len(all_metrics) == 2
        assert "op1" in all_metrics
        assert "op2" in all_metrics
        assert all_metrics["op1"].successful_requests == 1
        assert all_metrics["op2"].failed_requests == 1

    def test_get_system_metrics_empty(self):
        """Test getting system metrics when none recorded."""
        metrics = self.metrics_collector.get_system_metrics()
        assert metrics is None

    def test_get_metrics_summary(self):
        """Test getting metrics summary."""
        # Record some requests
        self.metrics_collector.record_request("op1", 100.0, True)
        self.metrics_collector.record_request("op1", 200.0, True)
        self.metrics_collector.record_request("op2", 300.0, False)

        # Record some errors
        self.metrics_collector.record_error("op2", "TimeoutError", "Request timeout")

        # Record system metrics
        system_metrics = SystemMetrics(memory_usage_mb=1024.0, cpu_usage_percent=50.0)
        self.metrics_collector.record_system_metrics(system_metrics)

        summary = self.metrics_collector.get_metrics_summary(time_window_minutes=60)

        assert summary["time_window_minutes"] == 60
        assert "timestamp" in summary
        assert summary["summary"]["total_requests"] == 3
        assert summary["summary"]["successful_requests"] == 2
        assert summary["summary"]["failed_requests"] == 1
        assert summary["summary"]["success_rate_percent"] == pytest.approx(
            66.67, rel=1e-2
        )
        assert summary["summary"]["error_rate_percent"] == pytest.approx(
            33.33, rel=1e-2
        )
        assert summary["summary"]["average_response_time_ms"] == 200.0

        assert "TimeoutError" in summary["error_breakdown"]
        assert summary["error_breakdown"]["TimeoutError"] == 1

        assert "op1" in summary["operation_breakdown"]
        assert "op2" in summary["operation_breakdown"]
        assert summary["operation_breakdown"]["op1"]["requests"] == 2
        assert summary["operation_breakdown"]["op1"]["errors"] == 0
        assert summary["operation_breakdown"]["op2"]["requests"] == 1
        assert summary["operation_breakdown"]["op2"]["errors"] == 1

        assert summary["system_metrics"]["memory_usage_mb"] == 1024.0
        assert summary["system_metrics"]["cpu_usage_percent"] == 50.0

    def test_get_metrics_summary_time_window(self):
        """Test metrics summary with time window filtering."""
        # Record an old request (simulate by mocking timestamp)
        old_time = datetime.utcnow() - timedelta(hours=2)

        with patch(
            "beast_dream_snow_loader.operations.metrics.datetime"
        ) as mock_datetime:
            mock_datetime.utcnow.return_value = old_time
            self.metrics_collector.record_request("old_op", 100.0, True)

        # Record a recent request
        self.metrics_collector.record_request("new_op", 200.0, True)

        # Get summary for last 60 minutes (should only include recent request)
        summary = self.metrics_collector.get_metrics_summary(time_window_minutes=60)

        assert summary["summary"]["total_requests"] == 1
        assert "new_op" in summary["operation_breakdown"]
        assert "old_op" not in summary["operation_breakdown"]

    def test_get_performance_trends(self):
        """Test getting performance trends."""
        # Record system metrics at different times
        for i in range(3):
            system_metrics = SystemMetrics(
                memory_usage_mb=1000.0 + i * 100, cpu_usage_percent=50.0 + i * 10
            )
            self.metrics_collector.record_system_metrics(system_metrics)

        # Record some requests
        self.metrics_collector.record_request("op1", 100.0, True)
        self.metrics_collector.record_request("op1", 200.0, True)

        trends = self.metrics_collector.get_performance_trends(hours=24)

        assert trends["time_period_hours"] == 24
        assert "timestamp" in trends
        assert "trends" in trends

        memory_trend = trends["trends"]["memory_usage"]
        assert memory_trend["trend"] == "increasing"  # 1000 -> 1200
        assert memory_trend["current_mb"] == 1200.0
        assert memory_trend["min_mb"] == 1000.0
        assert memory_trend["max_mb"] == 1200.0

        cpu_trend = trends["trends"]["cpu_usage"]
        assert cpu_trend["trend"] == "increasing"  # 50 -> 70
        assert cpu_trend["current_percent"] == 70.0

    def test_get_performance_trends_insufficient_data(self):
        """Test performance trends with insufficient data."""
        trends = self.metrics_collector.get_performance_trends(hours=24)

        assert "error" in trends
        assert "Insufficient data" in trends["error"]

    def test_reset_metrics(self):
        """Test resetting all metrics."""
        # Add some data
        self.metrics_collector.record_request("op1", 100.0, True)
        self.metrics_collector.record_error("op1", "Error", "Test error")
        system_metrics = SystemMetrics(memory_usage_mb=1024.0)
        self.metrics_collector.record_system_metrics(system_metrics)

        # Verify data exists
        assert len(self.metrics_collector.operation_metrics) > 0
        assert len(self.metrics_collector.request_history) > 0
        assert len(self.metrics_collector.error_history) > 0
        assert len(self.metrics_collector.system_metrics_history) > 0

        # Reset
        self.metrics_collector.reset_metrics()

        # Verify data is cleared
        assert len(self.metrics_collector.operation_metrics) == 0
        assert len(self.metrics_collector.request_history) == 0
        assert len(self.metrics_collector.error_history) == 0
        assert len(self.metrics_collector.system_metrics_history) == 0

    def test_cleanup_old_data(self):
        """Test cleaning up old data."""
        # Mock old timestamps
        old_time = datetime.utcnow() - timedelta(
            hours=25
        )  # Older than default 24h retention

        with patch(
            "beast_dream_snow_loader.operations.metrics.datetime"
        ) as mock_datetime:
            mock_datetime.utcnow.return_value = old_time

            # Add old data
            self.metrics_collector.record_request("old_op", 100.0, True)
            self.metrics_collector.record_error("old_op", "Error", "Old error")

        # Add recent data
        self.metrics_collector.record_request("new_op", 200.0, True)
        self.metrics_collector.record_error("new_op", "Error", "New error")

        # Verify we have both old and new data
        assert len(self.metrics_collector.request_history) == 2
        assert len(self.metrics_collector.error_history) == 2

        # Cleanup old data
        self.metrics_collector.cleanup_old_data()

        # Verify only recent data remains
        assert len(self.metrics_collector.request_history) == 1
        assert len(self.metrics_collector.error_history) == 1
        assert self.metrics_collector.request_history[0]["operation"] == "new_op"
        assert self.metrics_collector.error_history[0]["operation"] == "new_op"
