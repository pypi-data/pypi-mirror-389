"""Metrics collection and performance tracking for operational monitoring."""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock
from typing import Any

from .logger import StructuredLogger


@dataclass
class OperationMetrics:
    """Metrics for a specific operation."""

    operation_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time_ms: float = 0.0
    min_response_time_ms: float = float("inf")
    max_response_time_ms: float = 0.0
    response_times: deque = field(
        default_factory=lambda: deque(maxlen=1000)
    )  # Keep last 1000 for percentiles
    last_updated: datetime = field(default_factory=datetime.utcnow)

    @property
    def average_response_time_ms(self) -> float:
        """Calculate average response time."""
        return self.total_response_time_ms / max(1, self.total_requests)

    @property
    def error_rate_percent(self) -> float:
        """Calculate error rate as percentage."""
        return (self.failed_requests / max(1, self.total_requests)) * 100

    @property
    def success_rate_percent(self) -> float:
        """Calculate success rate as percentage."""
        return (self.successful_requests / max(1, self.total_requests)) * 100

    def get_percentile(self, percentile: float) -> float:
        """Get response time percentile (e.g., 95th percentile)."""
        if not self.response_times:
            return 0.0

        sorted_times = sorted(self.response_times)
        index = int((percentile / 100) * len(sorted_times))
        index = min(index, len(sorted_times) - 1)
        return sorted_times[index]

    @property
    def p95_response_time_ms(self) -> float:
        """Get 95th percentile response time."""
        return self.get_percentile(95.0)

    @property
    def p99_response_time_ms(self) -> float:
        """Get 99th percentile response time."""
        return self.get_percentile(99.0)


@dataclass
class SystemMetrics:
    """System-wide metrics."""

    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    active_connections: int = 0
    circuit_breaker_states: dict[str, str] = field(default_factory=dict)
    health_status: str = "unknown"
    uptime_seconds: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class MetricsCollector:
    """Collects and aggregates performance metrics."""

    def __init__(self, max_history_hours: int = 24):
        self.max_history_hours = max_history_hours
        self.start_time = datetime.utcnow()

        # Operation metrics by name
        self.operation_metrics: dict[str, OperationMetrics] = {}

        # System metrics history
        self.system_metrics_history: deque = deque(
            maxlen=max_history_hours * 60
        )  # One per minute

        # Request/error tracking by time windows
        self.request_history: deque = deque(maxlen=10000)  # Keep last 10k requests
        self.error_history: deque = deque(maxlen=1000)  # Keep last 1k errors

        # Thread safety
        self._lock = Lock()

        # Logging
        self.logger = StructuredLogger("metrics_collector")

    def record_request(
        self,
        operation: str,
        response_time_ms: float,
        success: bool,
        additional_context: dict[str, Any] | None = None,
    ) -> None:
        """Record a request with timing and success status."""
        with self._lock:
            # Get or create operation metrics
            if operation not in self.operation_metrics:
                self.operation_metrics[operation] = OperationMetrics(
                    operation_name=operation
                )

            metrics = self.operation_metrics[operation]

            # Update counters
            metrics.total_requests += 1
            if success:
                metrics.successful_requests += 1
            else:
                metrics.failed_requests += 1

            # Update timing
            metrics.total_response_time_ms += response_time_ms
            metrics.min_response_time_ms = min(
                metrics.min_response_time_ms, response_time_ms
            )
            metrics.max_response_time_ms = max(
                metrics.max_response_time_ms, response_time_ms
            )
            metrics.response_times.append(response_time_ms)
            metrics.last_updated = datetime.utcnow()

            # Add to request history
            self.request_history.append(
                {
                    "timestamp": datetime.utcnow(),
                    "operation": operation,
                    "response_time_ms": response_time_ms,
                    "success": success,
                    "context": additional_context or {},
                }
            )

            # Log performance metric
            self.logger.log_performance_metric(
                f"{operation}_response_time",
                response_time_ms,
                "ms",
                {
                    "operation": operation,
                    "success": success,
                    "total_requests": metrics.total_requests,
                    "error_rate_percent": metrics.error_rate_percent,
                    **(additional_context or {}),
                },
            )

    def record_error(
        self,
        operation: str,
        error_type: str,
        error_message: str,
        additional_context: dict[str, Any] | None = None,
    ) -> None:
        """Record an error occurrence."""
        with self._lock:
            # Add to error history
            self.error_history.append(
                {
                    "timestamp": datetime.utcnow(),
                    "operation": operation,
                    "error_type": error_type,
                    "error_message": error_message,
                    "context": additional_context or {},
                }
            )

            # Log error metric
            self.logger.log_performance_metric(
                f"{operation}_error_count",
                1,
                "count",
                {
                    "operation": operation,
                    "error_type": error_type,
                    "error_message": error_message[:100],  # Truncate long messages
                    **(additional_context or {}),
                },
            )

    def record_system_metrics(self, system_metrics: SystemMetrics) -> None:
        """Record system-wide metrics."""
        with self._lock:
            system_metrics.timestamp = datetime.utcnow()
            system_metrics.uptime_seconds = int(
                (datetime.utcnow() - self.start_time).total_seconds()
            )

            self.system_metrics_history.append(system_metrics)

            # Log system metrics
            self.logger.log_performance_metric(
                "system_memory_usage",
                system_metrics.memory_usage_mb,
                "MB",
                {"uptime_seconds": system_metrics.uptime_seconds},
            )

            self.logger.log_performance_metric(
                "system_cpu_usage",
                system_metrics.cpu_usage_percent,
                "percent",
                {"uptime_seconds": system_metrics.uptime_seconds},
            )

    def get_operation_metrics(self, operation: str) -> OperationMetrics | None:
        """Get metrics for a specific operation."""
        with self._lock:
            return self.operation_metrics.get(operation)

    def get_all_operation_metrics(self) -> dict[str, OperationMetrics]:
        """Get metrics for all operations."""
        with self._lock:
            return dict(self.operation_metrics)

    def get_system_metrics(self) -> SystemMetrics | None:
        """Get latest system metrics."""
        with self._lock:
            return (
                self.system_metrics_history[-1] if self.system_metrics_history else None
            )

    def get_metrics_summary(self, time_window_minutes: int = 60) -> dict[str, Any]:
        """Get a summary of metrics within a time window."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)

        with self._lock:
            # Filter recent requests
            recent_requests = [
                req for req in self.request_history if req["timestamp"] >= cutoff_time
            ]

            # Filter recent errors
            recent_errors = [
                err for err in self.error_history if err["timestamp"] >= cutoff_time
            ]

            # Calculate summary statistics
            total_requests = len(recent_requests)
            successful_requests = sum(1 for req in recent_requests if req["success"])
            failed_requests = total_requests - successful_requests

            # Response time statistics
            response_times = [req["response_time_ms"] for req in recent_requests]
            avg_response_time = (
                sum(response_times) / len(response_times) if response_times else 0
            )

            # Error breakdown
            error_breakdown = defaultdict(int)
            for error in recent_errors:
                error_breakdown[error["error_type"]] += 1

            # Operation breakdown
            operation_breakdown = defaultdict(
                lambda: {"requests": 0, "errors": 0, "avg_response_time": 0}
            )
            for req in recent_requests:
                op = req["operation"]
                operation_breakdown[op]["requests"] += 1
                if not req["success"]:
                    operation_breakdown[op]["errors"] += 1

            # Calculate average response times per operation
            for op in operation_breakdown:
                op_requests = [req for req in recent_requests if req["operation"] == op]
                if op_requests:
                    op_response_times = [req["response_time_ms"] for req in op_requests]
                    operation_breakdown[op]["avg_response_time"] = sum(
                        op_response_times
                    ) / len(op_response_times)

            return {
                "time_window_minutes": time_window_minutes,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "summary": {
                    "total_requests": total_requests,
                    "successful_requests": successful_requests,
                    "failed_requests": failed_requests,
                    "success_rate_percent": (
                        successful_requests / max(1, total_requests)
                    )
                    * 100,
                    "error_rate_percent": (failed_requests / max(1, total_requests))
                    * 100,
                    "average_response_time_ms": avg_response_time,
                },
                "error_breakdown": dict(error_breakdown),
                "operation_breakdown": dict(operation_breakdown),
                "system_metrics": (
                    {
                        "memory_usage_mb": self.system_metrics_history[
                            -1
                        ].memory_usage_mb,
                        "cpu_usage_percent": self.system_metrics_history[
                            -1
                        ].cpu_usage_percent,
                        "uptime_seconds": self.system_metrics_history[
                            -1
                        ].uptime_seconds,
                        "health_status": self.system_metrics_history[-1].health_status,
                    }
                    if self.system_metrics_history
                    else None
                ),
            }

    def get_performance_trends(self, hours: int = 24) -> dict[str, Any]:
        """Get performance trends over time."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        with self._lock:
            # Filter system metrics history
            recent_system_metrics = [
                metrics
                for metrics in self.system_metrics_history
                if metrics.timestamp >= cutoff_time
            ]

            # Calculate trends
            if len(recent_system_metrics) < 2:
                return {"error": "Insufficient data for trend analysis"}

            # Memory trend
            memory_values = [m.memory_usage_mb for m in recent_system_metrics]
            memory_trend = (
                "increasing" if memory_values[-1] > memory_values[0] else "decreasing"
            )

            # CPU trend
            cpu_values = [m.cpu_usage_percent for m in recent_system_metrics]
            cpu_trend = "increasing" if cpu_values[-1] > cpu_values[0] else "decreasing"

            # Request volume trend (requests per hour)
            hourly_requests = defaultdict(int)
            for req in self.request_history:
                if req["timestamp"] >= cutoff_time:
                    hour_key = req["timestamp"].replace(
                        minute=0, second=0, microsecond=0
                    )
                    hourly_requests[hour_key] += 1

            request_volumes = list(hourly_requests.values())
            request_trend = (
                "increasing"
                if len(request_volumes) > 1 and request_volumes[-1] > request_volumes[0]
                else "stable"
            )

            return {
                "time_period_hours": hours,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "trends": {
                    "memory_usage": {
                        "trend": memory_trend,
                        "current_mb": memory_values[-1] if memory_values else 0,
                        "min_mb": min(memory_values) if memory_values else 0,
                        "max_mb": max(memory_values) if memory_values else 0,
                        "avg_mb": (
                            sum(memory_values) / len(memory_values)
                            if memory_values
                            else 0
                        ),
                    },
                    "cpu_usage": {
                        "trend": cpu_trend,
                        "current_percent": cpu_values[-1] if cpu_values else 0,
                        "min_percent": min(cpu_values) if cpu_values else 0,
                        "max_percent": max(cpu_values) if cpu_values else 0,
                        "avg_percent": (
                            sum(cpu_values) / len(cpu_values) if cpu_values else 0
                        ),
                    },
                    "request_volume": {
                        "trend": request_trend,
                        "hourly_volumes": request_volumes,
                        "avg_requests_per_hour": (
                            sum(request_volumes) / len(request_volumes)
                            if request_volumes
                            else 0
                        ),
                    },
                },
                "data_points": len(recent_system_metrics),
            }

    def reset_metrics(self) -> None:
        """Reset all collected metrics."""
        with self._lock:
            self.operation_metrics.clear()
            self.system_metrics_history.clear()
            self.request_history.clear()
            self.error_history.clear()
            self.start_time = datetime.utcnow()

            self.logger.info("Metrics collector reset", performance_event=True)

    def cleanup_old_data(self) -> None:
        """Clean up old data beyond retention period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.max_history_hours)

        with self._lock:
            # Clean up request history
            original_request_count = len(self.request_history)
            self.request_history = deque(
                (
                    req
                    for req in self.request_history
                    if req["timestamp"] >= cutoff_time
                ),
                maxlen=self.request_history.maxlen,
            )

            # Clean up error history
            original_error_count = len(self.error_history)
            self.error_history = deque(
                (err for err in self.error_history if err["timestamp"] >= cutoff_time),
                maxlen=self.error_history.maxlen,
            )

            cleaned_requests = original_request_count - len(self.request_history)
            cleaned_errors = original_error_count - len(self.error_history)

            if cleaned_requests > 0 or cleaned_errors > 0:
                self.logger.debug(
                    f"Cleaned up old metrics data: {cleaned_requests} requests, {cleaned_errors} errors",
                    cleaned_requests=cleaned_requests,
                    cleaned_errors=cleaned_errors,
                    performance_event=True,
                )
