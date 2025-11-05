"""Unit tests for HealthMonitor and health check functionality."""

from unittest.mock import Mock, patch

import pytest

from beast_dream_snow_loader.operations.health import (
    HealthCheck,
    HealthMonitor,
    HealthStatus,
)


class TestHealthCheck:
    """Test cases for HealthCheck dataclass."""

    def test_health_check_creation(self):
        """Test HealthCheck creation with required fields."""
        check = HealthCheck(
            name="test_check", status=HealthStatus.HEALTHY, message="All good"
        )

        assert check.name == "test_check"
        assert check.status == HealthStatus.HEALTHY
        assert check.message == "All good"
        assert check.response_time_ms is None
        assert check.details == {}

    def test_health_check_with_optional_fields(self):
        """Test HealthCheck creation with optional fields."""
        details = {"endpoint": "/health", "status_code": 200}
        check = HealthCheck(
            name="api_check",
            status=HealthStatus.DEGRADED,
            message="Slow response",
            response_time_ms=1500.0,
            details=details,
        )

        assert check.response_time_ms == 1500.0
        assert check.details == details


class TestHealthMonitor:
    """Test cases for HealthMonitor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.health_monitor = HealthMonitor()

    def test_initialization_without_servicenow_client(self):
        """Test HealthMonitor initialization without ServiceNow client."""
        monitor = HealthMonitor()

        assert monitor.servicenow_client is None
        assert "system_resources" in monitor.checks
        assert "credential_availability" in monitor.checks
        assert "servicenow_connectivity" not in monitor.checks

    def test_initialization_with_servicenow_client(self):
        """Test HealthMonitor initialization with ServiceNow client."""
        mock_client = Mock()
        monitor = HealthMonitor(servicenow_client=mock_client)

        assert monitor.servicenow_client == mock_client
        assert "system_resources" in monitor.checks
        assert "credential_availability" in monitor.checks
        assert "servicenow_connectivity" in monitor.checks

    def test_register_custom_check(self):
        """Test registering a custom health check."""

        def custom_check():
            return HealthCheck("custom", HealthStatus.HEALTHY, "Custom check passed")

        self.health_monitor.register_check("custom_check", custom_check)

        assert "custom_check" in self.health_monitor.checks
        assert self.health_monitor.checks["custom_check"] == custom_check

    def test_unregister_check(self):
        """Test unregistering a health check."""

        def custom_check():
            return HealthCheck("custom", HealthStatus.HEALTHY, "Custom check passed")

        self.health_monitor.register_check("custom_check", custom_check)
        assert "custom_check" in self.health_monitor.checks

        self.health_monitor.unregister_check("custom_check")
        assert "custom_check" not in self.health_monitor.checks

    def test_unregister_nonexistent_check(self):
        """Test unregistering a check that doesn't exist."""
        # Should not raise an exception
        self.health_monitor.unregister_check("nonexistent_check")

    @pytest.mark.asyncio
    async def test_run_all_checks_success(self):
        """Test running all health checks successfully."""

        def healthy_check():
            return HealthCheck("test", HealthStatus.HEALTHY, "All good")

        def degraded_check():
            return HealthCheck("test2", HealthStatus.DEGRADED, "Slow")

        self.health_monitor.checks = {
            "healthy": healthy_check,
            "degraded": degraded_check,
        }

        results = await self.health_monitor.run_all_checks()

        assert len(results) == 2
        assert results["healthy"].status == HealthStatus.HEALTHY
        assert results["degraded"].status == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_run_all_checks_with_exception(self):
        """Test running health checks when one throws an exception."""

        def healthy_check():
            return HealthCheck("test", HealthStatus.HEALTHY, "All good")

        def failing_check():
            raise ValueError("Check failed")

        self.health_monitor.checks = {
            "healthy": healthy_check,
            "failing": failing_check,
        }

        results = await self.health_monitor.run_all_checks()

        assert len(results) == 2
        assert results["healthy"].status == HealthStatus.HEALTHY
        assert results["failing"].status == HealthStatus.UNHEALTHY
        assert "Check failed" in results["failing"].message

    def test_run_all_checks_sync(self):
        """Test synchronous version of run_all_checks."""

        def healthy_check():
            return HealthCheck("test", HealthStatus.HEALTHY, "All good")

        self.health_monitor.checks = {"healthy": healthy_check}

        results = self.health_monitor.run_all_checks_sync()

        assert len(results) == 1
        assert results["healthy"].status == HealthStatus.HEALTHY

    def test_get_overall_status_all_healthy(self):
        """Test overall status when all checks are healthy."""
        checks = {
            "check1": HealthCheck("check1", HealthStatus.HEALTHY, "Good"),
            "check2": HealthCheck("check2", HealthStatus.HEALTHY, "Good"),
        }

        status = self.health_monitor.get_overall_status(checks)
        assert status == HealthStatus.HEALTHY

    def test_get_overall_status_with_degraded(self):
        """Test overall status when some checks are degraded."""
        checks = {
            "check1": HealthCheck("check1", HealthStatus.HEALTHY, "Good"),
            "check2": HealthCheck("check2", HealthStatus.DEGRADED, "Slow"),
        }

        status = self.health_monitor.get_overall_status(checks)
        assert status == HealthStatus.DEGRADED

    def test_get_overall_status_with_unhealthy(self):
        """Test overall status when some checks are unhealthy."""
        checks = {
            "check1": HealthCheck("check1", HealthStatus.HEALTHY, "Good"),
            "check2": HealthCheck("check2", HealthStatus.DEGRADED, "Slow"),
            "check3": HealthCheck("check3", HealthStatus.UNHEALTHY, "Failed"),
        }

        status = self.health_monitor.get_overall_status(checks)
        assert status == HealthStatus.UNHEALTHY

    def test_get_overall_status_empty_checks(self):
        """Test overall status with no checks."""
        status = self.health_monitor.get_overall_status({})
        assert status == HealthStatus.UNHEALTHY

    @patch("beast_dream_snow_loader.operations.health.psutil")
    def test_check_system_resources_healthy(self, mock_psutil):
        """Test system resources check when resources are healthy."""
        # Mock psutil responses
        mock_psutil.cpu_percent.return_value = 25.0

        mock_memory = Mock()
        mock_memory.percent = 40.0
        mock_memory.available = 8 * 1024 * 1024 * 1024  # 8GB
        mock_memory.total = 16 * 1024 * 1024 * 1024  # 16GB
        mock_psutil.virtual_memory.return_value = mock_memory

        mock_disk = Mock()
        mock_disk.used = 100 * 1024 * 1024 * 1024  # 100GB
        mock_disk.total = 500 * 1024 * 1024 * 1024  # 500GB
        mock_disk.free = 400 * 1024 * 1024 * 1024  # 400GB
        mock_psutil.disk_usage.return_value = mock_disk

        result = self.health_monitor.check_system_resources()

        assert result.name == "system_resources"
        assert result.status == HealthStatus.HEALTHY
        assert "System resources normal" in result.message
        assert result.details["cpu_percent"] == 25.0
        assert result.details["memory_percent"] == 40.0

    @patch("beast_dream_snow_loader.operations.health.psutil")
    def test_check_system_resources_degraded(self, mock_psutil):
        """Test system resources check when resources are degraded."""
        # Mock high resource usage
        mock_psutil.cpu_percent.return_value = 80.0

        mock_memory = Mock()
        mock_memory.percent = 75.0
        mock_memory.available = 2 * 1024 * 1024 * 1024  # 2GB
        mock_memory.total = 8 * 1024 * 1024 * 1024  # 8GB
        mock_psutil.virtual_memory.return_value = mock_memory

        mock_disk = Mock()
        mock_disk.used = 450 * 1024 * 1024 * 1024  # 450GB
        mock_disk.total = 500 * 1024 * 1024 * 1024  # 500GB
        mock_disk.free = 50 * 1024 * 1024 * 1024  # 50GB
        mock_psutil.disk_usage.return_value = mock_disk

        result = self.health_monitor.check_system_resources()

        assert result.name == "system_resources"
        assert result.status == HealthStatus.DEGRADED
        assert "Resource constraints detected" in result.message
        assert len(result.details["issues"]) > 0

    @patch("beast_dream_snow_loader.operations.health.psutil")
    def test_check_system_resources_exception(self, mock_psutil):
        """Test system resources check when psutil raises exception."""
        mock_psutil.cpu_percent.side_effect = Exception("psutil error")

        result = self.health_monitor.check_system_resources()

        assert result.name == "system_resources"
        assert result.status == HealthStatus.UNHEALTHY
        assert "Failed to check system resources" in result.message

    def test_check_servicenow_connectivity_no_client(self):
        """Test ServiceNow connectivity check without client."""
        monitor = HealthMonitor(servicenow_client=None)

        result = monitor.check_servicenow_connectivity()

        assert result.name == "servicenow_connectivity"
        assert result.status == HealthStatus.UNHEALTHY
        assert "ServiceNow client not configured" in result.message

    def test_check_servicenow_connectivity_success(self):
        """Test successful ServiceNow connectivity check."""
        mock_client = Mock()
        mock_client.instance = "test.service-now.com"
        mock_client.query_records.return_value = [{"sys_id": "123"}]

        monitor = HealthMonitor(servicenow_client=mock_client)

        with patch("time.time", side_effect=[0, 0.5]):  # 500ms response
            result = monitor.check_servicenow_connectivity()

        assert result.name == "servicenow_connectivity"
        assert result.status == HealthStatus.HEALTHY
        assert "responding normally" in result.message
        assert result.response_time_ms == 500.0
        assert result.details["instance"] == "test.service-now.com"

    def test_check_servicenow_connectivity_slow(self):
        """Test ServiceNow connectivity check with slow response."""
        mock_client = Mock()
        mock_client.instance = "test.service-now.com"
        mock_client.query_records.return_value = [{"sys_id": "123"}]

        monitor = HealthMonitor(servicenow_client=mock_client)

        with patch("time.time", side_effect=[0, 3.0]):  # 3000ms response
            result = monitor.check_servicenow_connectivity()

        assert result.name == "servicenow_connectivity"
        assert result.status == HealthStatus.DEGRADED
        assert "responding slowly" in result.message
        assert result.response_time_ms == 3000.0

    def test_check_servicenow_connectivity_failure(self):
        """Test ServiceNow connectivity check with connection failure."""
        mock_client = Mock()
        mock_client.instance = "test.service-now.com"
        mock_client.query_records.side_effect = Exception("Connection failed")

        monitor = HealthMonitor(servicenow_client=mock_client)

        result = monitor.check_servicenow_connectivity()

        assert result.name == "servicenow_connectivity"
        assert result.status == HealthStatus.UNHEALTHY
        assert "connection failed" in result.message
        assert "Connection failed" in result.details["error"]

    @patch("shutil.which")
    @patch("subprocess.run")
    @patch("os.getenv")
    def test_check_credential_availability_1password_available(
        self, mock_getenv, mock_subprocess, mock_which
    ):
        """Test credential availability check with 1Password available."""
        # Mock 1Password CLI available and signed in
        mock_which.return_value = "/usr/local/bin/op"

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "user@example.com"
        mock_subprocess.return_value = mock_result

        # Mock environment variables
        mock_getenv.side_effect = lambda key, default="": {
            "SERVICENOW_INSTANCE": "test.service-now.com",
            "SERVICENOW_USERNAME": "admin",
            "SERVICENOW_API_KEY": "test-key",
        }.get(key, default)

        result = self.health_monitor.check_credential_availability()

        assert result.name == "credential_availability"
        assert result.status == HealthStatus.HEALTHY
        assert "All credential sources available" in result.message
        assert result.details["1password_cli_installed"] is True
        assert result.details["1password_cli_signed_in"] is True
        assert result.details["auth_methods_available"]["api_key"] is True

    @patch("shutil.which")
    @patch("os.getenv")
    def test_check_credential_availability_no_1password(self, mock_getenv, mock_which):
        """Test credential availability check without 1Password."""
        # Mock 1Password CLI not available
        mock_which.return_value = None

        # Mock environment variables with complete auth
        mock_getenv.side_effect = lambda key, default="": {
            "SERVICENOW_INSTANCE": "test.service-now.com",
            "SERVICENOW_USERNAME": "admin",
            "SERVICENOW_API_KEY": "test-key",
        }.get(key, default)

        result = self.health_monitor.check_credential_availability()

        assert result.name == "credential_availability"
        assert result.status == HealthStatus.DEGRADED
        assert (
            "Environment variables available but 1Password CLI unavailable"
            in result.message
        )
        assert result.details["1password_cli_installed"] is False
        assert result.details["auth_methods_available"]["api_key"] is True

    @patch("shutil.which")
    @patch("os.getenv")
    def test_check_credential_availability_no_credentials(
        self, mock_getenv, mock_which
    ):
        """Test credential availability check with no credentials."""
        # Mock 1Password CLI not available
        mock_which.return_value = None

        # Mock no environment variables
        mock_getenv.return_value = ""

        result = self.health_monitor.check_credential_availability()

        assert result.name == "credential_availability"
        assert result.status == HealthStatus.UNHEALTHY
        assert "No credential sources available" in result.message
        assert result.details["1password_cli_installed"] is False
        assert not any(result.details["auth_methods_available"].values())

    def test_get_health_summary(self):
        """Test getting health summary."""

        def healthy_check():
            return HealthCheck(
                "test", HealthStatus.HEALTHY, "All good", response_time_ms=100.0
            )

        self.health_monitor.checks = {"test_check": healthy_check}

        summary = self.health_monitor.get_health_summary()

        assert summary["overall_status"] == "healthy"
        assert "timestamp" in summary
        assert "test_check" in summary["checks"]
        assert summary["checks"]["test_check"]["status"] == "healthy"
        assert summary["checks"]["test_check"]["response_time_ms"] == 100.0
        assert summary["summary"]["total_checks"] == 1
        assert summary["summary"]["healthy"] == 1
        assert summary["summary"]["degraded"] == 0
        assert summary["summary"]["unhealthy"] == 0
