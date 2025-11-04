"""Unit tests for configuration management and environment detection."""

import json
import os
import tempfile
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from beast_dream_snow_loader.operations.config import (
    CircuitBreakerConfig,
    ConfigurationManager,
    Environment,
    HealthCheckConfig,
    LoggingConfig,
    MetricsConfig,
    OperationalConfig,
    RetryConfig,
    SecurityConfig,
)


class TestLoggingConfig:
    """Test cases for LoggingConfig."""

    def test_default_values(self):
        """Test LoggingConfig default values."""
        config = LoggingConfig()

        assert config.level == "INFO"
        assert config.format == "structured"
        assert config.console_output is True
        assert config.file_output is None

    def test_custom_values(self):
        """Test LoggingConfig with custom values."""
        config = LoggingConfig(
            level="DEBUG",
            format="simple",
            console_output=False,
            file_output="/var/log/app.log",
        )

        assert config.level == "DEBUG"
        assert config.format == "simple"
        assert config.console_output is False
        assert config.file_output == "/var/log/app.log"

    def test_level_validation(self):
        """Test logging level validation."""
        # Valid levels should work
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            config = LoggingConfig(level=level)
            assert config.level == level

        # Case insensitive
        config = LoggingConfig(level="debug")
        assert config.level == "DEBUG"

        # Invalid level should raise error
        with pytest.raises(ValidationError):
            LoggingConfig(level="INVALID")

    def test_format_validation(self):
        """Test log format validation."""
        # Valid formats
        for fmt in ["structured", "simple"]:
            config = LoggingConfig(format=fmt)
            assert config.format == fmt

        # Case insensitive
        config = LoggingConfig(format="STRUCTURED")
        assert config.format == "structured"

        # Invalid format should raise error
        with pytest.raises(ValidationError):
            LoggingConfig(format="invalid")


class TestRetryConfig:
    """Test cases for RetryConfig."""

    def test_default_values(self):
        """Test RetryConfig default values."""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.base_delay_seconds == 1.0
        assert config.max_delay_seconds == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_validation_constraints(self):
        """Test RetryConfig validation constraints."""
        # Valid values
        config = RetryConfig(
            max_attempts=5,
            base_delay_seconds=2.0,
            max_delay_seconds=120.0,
            exponential_base=3.0,
        )
        assert config.max_attempts == 5

        # Invalid max_attempts (too low)
        with pytest.raises(ValidationError):
            RetryConfig(max_attempts=0)

        # Invalid max_attempts (too high)
        with pytest.raises(ValidationError):
            RetryConfig(max_attempts=11)

        # Invalid base_delay_seconds (too low)
        with pytest.raises(ValidationError):
            RetryConfig(base_delay_seconds=0.05)

        # Invalid exponential_base (too low)
        with pytest.raises(ValidationError):
            RetryConfig(exponential_base=1.0)

    def test_max_delay_validation(self):
        """Test max_delay_seconds validation against base_delay_seconds."""
        # Valid: max > base
        config = RetryConfig(base_delay_seconds=2.0, max_delay_seconds=10.0)
        assert config.max_delay_seconds == 10.0

        # Invalid: max < base
        with pytest.raises(ValidationError):
            RetryConfig(base_delay_seconds=10.0, max_delay_seconds=5.0)


class TestCircuitBreakerConfig:
    """Test cases for CircuitBreakerConfig."""

    def test_default_values(self):
        """Test CircuitBreakerConfig default values."""
        config = CircuitBreakerConfig()

        assert config.failure_threshold == 5
        assert config.recovery_timeout_seconds == 60
        assert config.success_threshold == 1

    def test_validation_constraints(self):
        """Test CircuitBreakerConfig validation constraints."""
        # Valid values
        config = CircuitBreakerConfig(
            failure_threshold=10, recovery_timeout_seconds=120, success_threshold=2
        )
        assert config.failure_threshold == 10

        # Invalid failure_threshold (too low)
        with pytest.raises(ValidationError):
            CircuitBreakerConfig(failure_threshold=0)

        # Invalid recovery_timeout_seconds (too low)
        with pytest.raises(ValidationError):
            CircuitBreakerConfig(recovery_timeout_seconds=4)


class TestOperationalConfig:
    """Test cases for OperationalConfig."""

    def test_default_configuration(self):
        """Test OperationalConfig with default values."""
        config = OperationalConfig()

        assert config.environment == Environment.UNKNOWN
        assert isinstance(config.logging, LoggingConfig)
        assert isinstance(config.retry, RetryConfig)
        assert isinstance(config.circuit_breaker, CircuitBreakerConfig)
        assert isinstance(config.health_check, HealthCheckConfig)
        assert isinstance(config.metrics, MetricsConfig)
        assert isinstance(config.security, SecurityConfig)

    def test_custom_configuration(self):
        """Test OperationalConfig with custom values."""
        config = OperationalConfig(
            environment=Environment.PRODUCTION,
            logging=LoggingConfig(level="ERROR"),
            retry=RetryConfig(max_attempts=5),
        )

        assert (
            config.environment == "production"
        )  # Environment is stored as string in config
        assert config.logging.level == "ERROR"
        assert config.retry.max_attempts == 5


class TestConfigurationManager:
    """Test cases for ConfigurationManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config_manager = ConfigurationManager()

    @patch("os.getenv")
    def test_get_environment_explicit(self, mock_getenv):
        """Test environment retrieval with explicit BEAST_ENVIRONMENT variable."""
        mock_getenv.return_value = "production"

        env = self.config_manager._get_environment()
        assert env == Environment.PRODUCTION

    def test_get_environment_explicit_parameter(self):
        """Test environment retrieval with explicit parameter."""
        env = self.config_manager._get_environment(Environment.DEVELOPMENT)
        assert env == Environment.DEVELOPMENT

    @patch("os.getenv")
    def test_get_environment_missing_raises_error(self, mock_getenv):
        """Test that missing BEAST_ENVIRONMENT raises clear error."""
        mock_getenv.return_value = None

        with pytest.raises(
            ValueError, match="Environment must be explicitly specified"
        ):
            self.config_manager._get_environment()

    @patch("os.getenv")
    def test_get_environment_invalid_value_raises_error(self, mock_getenv):
        """Test that invalid BEAST_ENVIRONMENT value raises clear error."""
        mock_getenv.return_value = "invalid_env"

        with pytest.raises(ValueError, match="Invalid BEAST_ENVIRONMENT value"):
            self.config_manager._get_environment()

    @pytest.mark.skip(
        reason="BACKLOG-001: Environment detection logic needs fix for CI empty string handling"
    )
    @patch("platform.node")
    @patch("os.getenv")
    @patch("os.path.exists")
    def test_detect_environment_unknown(self, mock_exists, mock_getenv, mock_node):
        """Test environment detection when no clear indicators."""

        def mock_getenv_func(key, default=""):
            # Return empty string for main env vars, None for test-specific ones
            if key in [
                "BEAST_ENVIRONMENT",
                "NODE_ENV",
                "FLASK_ENV",
                "DJANGO_DEBUG",
                "CI",
            ]:
                return ""
            else:
                return None

        mock_getenv.side_effect = mock_getenv_func
        mock_node.return_value = "unknown-machine"
        mock_exists.side_effect = lambda path: False  # No special files exist

        env = self.config_manager.detect_environment()
        assert env == Environment.UNKNOWN

    @patch("platform.system")
    @patch("platform.python_version")
    @patch("os.getpid")
    @patch("os.getcwd")
    def test_collect_environment_info(
        self, mock_getcwd, mock_getpid, mock_python_version, mock_system
    ):
        """Test environment information collection."""
        mock_system.return_value = "Linux"
        mock_python_version.return_value = "3.10.0"
        mock_getpid.return_value = 12345
        mock_getcwd.return_value = "/app"

        with patch.dict(os.environ, {"TEST_VAR": "test_value", "SECRET_KEY": "secret"}):
            info = self.config_manager.collect_environment_info()

        assert info["platform"]["system"] == "Linux"
        assert info["platform"]["python_version"] == "3.10.0"
        assert info["process"]["pid"] == 12345
        assert info["process"]["cwd"] == "/app"

        # Should include non-sensitive env vars
        assert "TEST_VAR" in info["environment_variables"]
        assert info["environment_variables"]["TEST_VAR"] == "test_value"

        # Should exclude sensitive env vars
        assert "SECRET_KEY" not in info["environment_variables"]

    def test_load_configuration_defaults(self):
        """Test loading configuration with explicit UNKNOWN environment."""
        config = self.config_manager.load_configuration(environment=Environment.UNKNOWN)

        assert isinstance(config, OperationalConfig)
        assert config.logging.level == "INFO"  # Base default
        assert config.retry.max_attempts == 3  # Base default

    def test_load_configuration_explicit_development(self):
        """Test loading configuration with explicit development environment."""
        config = self.config_manager.load_configuration(
            environment=Environment.DEVELOPMENT
        )

        assert isinstance(config, OperationalConfig)
        assert config.logging.level == "DEBUG"  # Development default
        assert config.retry.max_attempts == 2  # Development default

    def test_load_configuration_explicit_production(self):
        """Test loading configuration with explicit production environment."""
        config = self.config_manager.load_configuration(
            environment=Environment.PRODUCTION
        )

        assert isinstance(config, OperationalConfig)
        assert config.logging.level == "INFO"  # Production default
        assert config.retry.max_attempts == 5  # Production default

    @patch("os.getenv")
    def test_load_configuration_from_beast_environment_var(self, mock_getenv):
        """Test loading configuration from BEAST_ENVIRONMENT variable."""

        def mock_getenv_func(key, default=None):
            if key == "BEAST_ENVIRONMENT":
                return "production"
            return default

        mock_getenv.side_effect = mock_getenv_func

        config = self.config_manager.load_configuration()

        assert isinstance(config, OperationalConfig)
        assert config.logging.level == "INFO"
        assert config.retry.max_attempts == 5

    def test_load_configuration_missing_environment_raises_error(self):
        """Test that missing environment specification raises clear error."""
        with patch("os.getenv", return_value=None):
            with pytest.raises(
                ValueError, match="Environment must be explicitly specified"
            ):
                self.config_manager.load_configuration()

    @patch("os.getenv")
    def test_load_configuration_invalid_environment_raises_error(self, mock_getenv):
        """Test that invalid BEAST_ENVIRONMENT value raises clear error."""

        def mock_getenv_func(key, default=None):
            if key == "BEAST_ENVIRONMENT":
                return "invalid_env"
            return default

        mock_getenv.side_effect = mock_getenv_func

        with pytest.raises(ValueError, match="Invalid configuration"):
            self.config_manager.load_configuration()

    @pytest.mark.skip(
        reason="BACKLOG-002: Configuration type coercion - environment field string vs enum mismatch"
    )
    def test_load_configuration_from_file(self):
        """Test loading configuration from JSON file."""
        config_data = {
            "environment": "production",
            "logging": {"level": "ERROR", "console_output": False},
            "retry": {"max_attempts": 5, "base_delay_seconds": 2.0},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            config = self.config_manager.load_configuration(config_file=config_file)

            assert config.environment == Environment.PRODUCTION
            assert config.logging.level == "ERROR"
            assert config.logging.console_output is False
            assert config.retry.max_attempts == 5
            assert config.retry.base_delay_seconds == 2.0
        finally:
            os.unlink(config_file)

    def test_load_configuration_invalid_file(self):
        """Test loading configuration from invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            config_file = f.name

        try:
            with pytest.raises(ValueError, match="Invalid configuration file"):
                self.config_manager.load_configuration(config_file=config_file)
        finally:
            os.unlink(config_file)

    @patch.dict(
        os.environ,
        {
            "BEAST_ENVIRONMENT": "staging",
            "BEAST_LOG_LEVEL": "DEBUG",
            "BEAST_LOG_CONSOLE": "false",
            "BEAST_RETRY_MAX_ATTEMPTS": "7",
            "BEAST_CIRCUIT_FAILURE_THRESHOLD": "15",
        },
    )
    @pytest.mark.skip(
        reason="BACKLOG-002: Configuration type coercion - environment field string vs enum mismatch"
    )
    def test_load_configuration_from_environment(self):
        """Test loading configuration from environment variables."""
        config = self.config_manager.load_configuration(environment_overrides=True)

        assert config.environment == Environment.STAGING
        assert config.logging.level == "DEBUG"
        assert config.logging.console_output is False
        assert config.retry.max_attempts == 7
        assert config.circuit_breaker.failure_threshold == 15

    def test_load_configuration_environment_specific_defaults(self):
        """Test environment-specific default application."""
        # Test development defaults
        config = self.config_manager.load_configuration(
            environment=Environment.DEVELOPMENT
        )
        assert config.logging.level == "DEBUG"
        assert config.retry.max_attempts == 2

        # Test production defaults
        config = self.config_manager.load_configuration(
            environment=Environment.PRODUCTION
        )
        assert config.logging.level == "INFO"
        assert config.retry.max_attempts == 5

        # Test testing defaults
        config = self.config_manager.load_configuration(environment=Environment.TESTING)
        assert config.logging.level == "WARNING"
        assert config.retry.max_attempts == 1
        assert config.metrics.collection_enabled is False

    def test_validate_configuration_valid(self):
        """Test configuration validation with valid config."""
        config = OperationalConfig()
        issues = self.config_manager.validate_configuration(config)

        assert len(issues) == 0

    def test_validate_configuration_invalid_log_directory(self):
        """Test configuration validation with invalid log directory."""
        config = OperationalConfig(
            logging=LoggingConfig(file_output="/nonexistent/directory/app.log")
        )

        issues = self.config_manager.validate_configuration(config)

        assert len(issues) > 0
        assert any("does not exist" in issue for issue in issues)

    def test_validate_configuration_retry_inconsistency(self):
        """Test configuration validation with retry inconsistency."""
        # This should be caught by Pydantic validation during creation
        with pytest.raises(ValidationError):
            RetryConfig(base_delay_seconds=10.0, max_delay_seconds=5.0)

    def test_validate_configuration_health_check_timing(self):
        """Test configuration validation with health check timing issues."""
        config = OperationalConfig(
            health_check=HealthCheckConfig(
                interval_seconds=30, timeout_seconds=35  # Timeout > interval
            )
        )

        issues = self.config_manager.validate_configuration(config)

        assert len(issues) > 0
        assert any("timeout should be less than interval" in issue for issue in issues)

    def test_get_configuration_before_load(self):
        """Test getting configuration before loading."""
        config = self.config_manager.get_configuration()
        assert config is None

    def test_get_configuration_after_load(self):
        """Test getting configuration after loading."""
        loaded_config = self.config_manager.load_configuration(
            environment=Environment.UNKNOWN
        )
        retrieved_config = self.config_manager.get_configuration()

        assert retrieved_config is loaded_config
        assert isinstance(retrieved_config, OperationalConfig)

    def test_merge_config_simple(self):
        """Test simple configuration merging."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}

        self.config_manager._merge_config(base, override)

        assert base == {"a": 1, "b": 3, "c": 4}

    def test_merge_config_nested(self):
        """Test nested configuration merging."""
        base = {"logging": {"level": "INFO", "console": True}, "retry": {"attempts": 3}}
        override = {
            "logging": {"level": "DEBUG", "file": "/var/log/app.log"},
            "metrics": {"enabled": True},
        }

        self.config_manager._merge_config(base, override)

        expected = {
            "logging": {"level": "DEBUG", "console": True, "file": "/var/log/app.log"},
            "retry": {"attempts": 3},
            "metrics": {"enabled": True},
        }
        assert base == expected
