"""Health monitoring and system status checks for operational resilience."""

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import psutil

from .logger import StructuredLogger


class HealthStatus(Enum):
    """Health check status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheck:
    """Result of a health check operation."""

    name: str
    status: HealthStatus
    message: str
    response_time_ms: float | None = None
    details: dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class HealthMonitor:
    """Health monitoring system for checking service and system status."""

    def __init__(self, servicenow_client=None):
        self.servicenow_client = servicenow_client
        self.checks: dict[str, Callable[[], HealthCheck]] = {}
        self.logger = StructuredLogger("health_monitor")

        # Register default checks
        self._register_default_checks()

    def _register_default_checks(self) -> None:
        """Register default health checks."""
        self.register_check("system_resources", self.check_system_resources)
        self.register_check(
            "credential_availability", self.check_credential_availability
        )

        if self.servicenow_client:
            self.register_check(
                "servicenow_connectivity", self.check_servicenow_connectivity
            )

    def register_check(self, name: str, check_func: Callable[[], HealthCheck]) -> None:
        """Register a custom health check function."""
        self.checks[name] = check_func
        self.logger.debug(
            f"Registered health check: {name}", check_name=name, health_event=True
        )

    def unregister_check(self, name: str) -> None:
        """Unregister a health check."""
        if name in self.checks:
            del self.checks[name]
            self.logger.debug(
                f"Unregistered health check: {name}", check_name=name, health_event=True
            )

    async def run_all_checks(self) -> dict[str, HealthCheck]:
        """Run all registered health checks asynchronously."""
        results = {}

        # Run checks concurrently
        tasks = []
        for name, check_func in self.checks.items():
            task = asyncio.create_task(self._run_single_check(name, check_func))
            tasks.append(task)

        # Wait for all checks to complete
        check_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, (name, _) in enumerate(self.checks.items()):
            result = check_results[i]
            if isinstance(result, Exception):
                # Health check itself failed
                results[name] = HealthCheck(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(result)}",
                    details={
                        "exception": str(result),
                        "exception_type": type(result).__name__,
                    },
                )
            else:
                results[name] = result

        # Log overall health status
        overall_status = self.get_overall_status(results)
        self.logger.log_health_check(
            "overall_system",
            overall_status.value,
            details={
                "individual_checks": {
                    name: check.status.value for name, check in results.items()
                },
                "total_checks": len(results),
                "healthy_checks": sum(
                    1
                    for check in results.values()
                    if check.status == HealthStatus.HEALTHY
                ),
                "degraded_checks": sum(
                    1
                    for check in results.values()
                    if check.status == HealthStatus.DEGRADED
                ),
                "unhealthy_checks": sum(
                    1
                    for check in results.values()
                    if check.status == HealthStatus.UNHEALTHY
                ),
            },
        )

        return results

    async def _run_single_check(
        self, name: str, check_func: Callable[[], HealthCheck]
    ) -> HealthCheck:
        """Run a single health check with timing."""
        start_time = time.time()

        try:
            # Run check in thread pool for CPU-bound operations
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, check_func)

            # Add timing if not already set
            if result.response_time_ms is None:
                result.response_time_ms = (time.time() - start_time) * 1000

            # Log individual check result
            self.logger.log_health_check(
                result.name,
                result.status.value,
                result.response_time_ms,
                result.details,
            )

            return result

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000

            result = HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check exception: {str(e)}",
                response_time_ms=response_time_ms,
                details={"exception": str(e), "exception_type": type(e).__name__},
            )

            self.logger.log_health_check(
                result.name,
                result.status.value,
                result.response_time_ms,
                result.details,
            )

            return result

    def run_all_checks_sync(self) -> dict[str, HealthCheck]:
        """Run all health checks synchronously."""
        return asyncio.run(self.run_all_checks())

    def check_servicenow_connectivity(self) -> HealthCheck:
        """Check ServiceNow API connectivity and response time."""
        if not self.servicenow_client:
            return HealthCheck(
                name="servicenow_connectivity",
                status=HealthStatus.UNHEALTHY,
                message="ServiceNow client not configured",
                details={"error": "No ServiceNow client available"},
            )

        start_time = time.time()

        try:
            # Try a simple query to test connectivity
            # Use sys_user table as it's always available and lightweight
            results = self.servicenow_client.query_records("sys_user", limit=1)

            response_time_ms = (time.time() - start_time) * 1000

            # Determine status based on response time
            if response_time_ms < 1000:  # < 1 second
                status = HealthStatus.HEALTHY
                message = "ServiceNow API responding normally"
            elif response_time_ms < 5000:  # < 5 seconds
                status = HealthStatus.DEGRADED
                message = "ServiceNow API responding slowly"
            else:
                status = HealthStatus.DEGRADED
                message = "ServiceNow API responding very slowly"

            return HealthCheck(
                name="servicenow_connectivity",
                status=status,
                message=message,
                response_time_ms=response_time_ms,
                details={
                    "instance": self.servicenow_client.instance,
                    "query_result_count": len(results) if results else 0,
                    "response_time_category": (
                        "fast"
                        if response_time_ms < 1000
                        else "slow" if response_time_ms < 5000 else "very_slow"
                    ),
                },
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000

            return HealthCheck(
                name="servicenow_connectivity",
                status=HealthStatus.UNHEALTHY,
                message=f"ServiceNow API connection failed: {str(e)}",
                response_time_ms=response_time_ms,
                details={
                    "instance": getattr(self.servicenow_client, "instance", "unknown"),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )

    def check_credential_availability(self) -> HealthCheck:
        """Check availability of credential sources."""
        import os
        import shutil
        import subprocess

        details = {}
        issues = []

        # Check 1Password CLI availability
        op_available = shutil.which("op") is not None
        details["1password_cli_installed"] = op_available

        if op_available:
            try:
                # Check if signed in (without prompting)
                result = subprocess.run(
                    ["op", "whoami"], capture_output=True, text=True, timeout=5
                )
                op_signed_in = result.returncode == 0 and result.stdout.strip() != ""
                details["1password_cli_signed_in"] = op_signed_in

                if not op_signed_in:
                    issues.append("1Password CLI not signed in")

            except (
                subprocess.TimeoutExpired,
                FileNotFoundError,
                subprocess.SubprocessError,
            ):
                details["1password_cli_signed_in"] = False
                issues.append("1Password CLI check failed")
        else:
            issues.append("1Password CLI not installed")

        # Check environment variables
        env_vars_present = {
            "SERVICENOW_INSTANCE": bool(os.getenv("SERVICENOW_INSTANCE")),
            "SERVICENOW_USERNAME": bool(os.getenv("SERVICENOW_USERNAME")),
            "SERVICENOW_API_KEY": bool(os.getenv("SERVICENOW_API_KEY")),
            "SERVICENOW_PASSWORD": bool(os.getenv("SERVICENOW_PASSWORD")),
            "SERVICENOW_OAUTH_TOKEN": bool(os.getenv("SERVICENOW_OAUTH_TOKEN")),
        }

        details["environment_variables"] = env_vars_present

        # Check if we have at least one complete auth method
        has_api_key_auth = (
            env_vars_present["SERVICENOW_INSTANCE"]
            and env_vars_present["SERVICENOW_USERNAME"]
            and env_vars_present["SERVICENOW_API_KEY"]
        )
        has_oauth_auth = (
            env_vars_present["SERVICENOW_INSTANCE"]
            and env_vars_present["SERVICENOW_OAUTH_TOKEN"]
        )
        has_basic_auth = (
            env_vars_present["SERVICENOW_INSTANCE"]
            and env_vars_present["SERVICENOW_USERNAME"]
            and env_vars_present["SERVICENOW_PASSWORD"]
        )

        details["auth_methods_available"] = {
            "api_key": has_api_key_auth,
            "oauth": has_oauth_auth,
            "basic": has_basic_auth,
        }

        if not (has_api_key_auth or has_oauth_auth or has_basic_auth):
            if not op_available or not details.get("1password_cli_signed_in", False):
                issues.append("No complete authentication method available")

        # Determine overall status
        if not issues:
            status = HealthStatus.HEALTHY
            message = "All credential sources available"
        elif op_available and details.get("1password_cli_signed_in", False):
            status = HealthStatus.DEGRADED
            message = "1Password CLI available but environment variables incomplete"
        elif any(details["auth_methods_available"].values()):
            status = HealthStatus.DEGRADED
            message = "Environment variables available but 1Password CLI unavailable"
        else:
            status = HealthStatus.UNHEALTHY
            message = "No credential sources available"

        details["issues"] = issues

        return HealthCheck(
            name="credential_availability",
            status=status,
            message=message,
            details=details,
        )

    def check_system_resources(self) -> HealthCheck:
        """Check system resource usage (CPU, memory, disk)."""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            details = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / (1024 * 1024),
                "memory_total_mb": memory.total / (1024 * 1024),
                "disk_percent": (disk.used / disk.total) * 100,
                "disk_free_gb": disk.free / (1024 * 1024 * 1024),
                "disk_total_gb": disk.total / (1024 * 1024 * 1024),
            }

            # Determine status based on resource usage
            issues = []

            if cpu_percent > 90:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            elif cpu_percent > 70:
                issues.append(f"Elevated CPU usage: {cpu_percent:.1f}%")

            if memory.percent > 90:
                issues.append(f"High memory usage: {memory.percent:.1f}%")
            elif memory.percent > 70:
                issues.append(f"Elevated memory usage: {memory.percent:.1f}%")

            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > 95:
                issues.append(f"Critical disk usage: {disk_percent:.1f}%")
            elif disk_percent > 85:
                issues.append(f"High disk usage: {disk_percent:.1f}%")

            # Determine overall status
            if not issues:
                status = HealthStatus.HEALTHY
                message = "System resources normal"
            elif any("High" in issue or "Elevated" in issue for issue in issues):
                status = HealthStatus.DEGRADED
                message = f"Resource constraints detected: {', '.join(issues)}"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Critical resource issues: {', '.join(issues)}"

            details["issues"] = issues

            return HealthCheck(
                name="system_resources", status=status, message=message, details=details
            )

        except Exception as e:
            return HealthCheck(
                name="system_resources",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check system resources: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
            )

    def get_overall_status(self, checks: dict[str, HealthCheck]) -> HealthStatus:
        """Determine overall system health status from individual checks."""
        if not checks:
            return HealthStatus.UNHEALTHY

        statuses = [check.status for check in checks.values()]

        # If any check is unhealthy, overall is unhealthy
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY

        # If any check is degraded, overall is degraded
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED

        # All checks are healthy
        return HealthStatus.HEALTHY

    def get_health_summary(self) -> dict[str, Any]:
        """Get a summary of current health status."""
        checks = self.run_all_checks_sync()
        overall_status = self.get_overall_status(checks)

        return {
            "overall_status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "checks": {
                name: {
                    "status": check.status.value,
                    "message": check.message,
                    "response_time_ms": check.response_time_ms,
                }
                for name, check in checks.items()
            },
            "summary": {
                "total_checks": len(checks),
                "healthy": sum(
                    1
                    for check in checks.values()
                    if check.status == HealthStatus.HEALTHY
                ),
                "degraded": sum(
                    1
                    for check in checks.values()
                    if check.status == HealthStatus.DEGRADED
                ),
                "unhealthy": sum(
                    1
                    for check in checks.values()
                    if check.status == HealthStatus.UNHEALTHY
                ),
            },
        }
