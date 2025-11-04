"""Configuration management and environment detection for operational resilience."""

import os
import platform
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, validator

from .logger import StructuredLogger


class Environment(Enum):
    """Deployment environment types."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    UNKNOWN = "unknown"


class LoggingConfig(BaseModel):
    """Logging configuration settings."""

    level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    format: str = Field(
        default="structured", description="Log format (structured, simple)"
    )
    console_output: bool = Field(default=True, description="Enable console output")
    file_output: str | None = Field(
        default=None, description="Log file path (optional)"
    )

    @validator("level")
    def validate_level(cls, v):
        """Validate logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(
                f"Invalid logging level: {v}. Must be one of {valid_levels}"
            )
        return v.upper()

    @validator("format")
    def validate_format(cls, v):
        """Validate log format."""
        valid_formats = {"structured", "simple"}
        if v.lower() not in valid_formats:
            raise ValueError(f"Invalid log format: {v}. Must be one of {valid_formats}")
        return v.lower()


class RetryConfig(BaseModel):
    """Retry policy configuration settings."""

    max_attempts: int = Field(
        default=3, ge=1, le=10, description="Maximum retry attempts"
    )
    base_delay_seconds: float = Field(
        default=1.0, ge=0.1, le=60.0, description="Base delay between retries"
    )
    max_delay_seconds: float = Field(
        default=60.0, ge=1.0, le=300.0, description="Maximum delay between retries"
    )
    exponential_base: float = Field(
        default=2.0, ge=1.1, le=10.0, description="Exponential backoff base"
    )
    jitter: bool = Field(
        default=True, description="Enable jitter to prevent thundering herd"
    )

    @validator("max_delay_seconds")
    def validate_max_delay(cls, v, values):
        """Validate max delay is greater than base delay."""
        if "base_delay_seconds" in values and v < values["base_delay_seconds"]:
            raise ValueError(
                "max_delay_seconds must be greater than base_delay_seconds"
            )
        return v


class CircuitBreakerConfig(BaseModel):
    """Circuit breaker configuration settings."""

    failure_threshold: int = Field(
        default=5, ge=1, le=100, description="Failures before opening circuit"
    )
    recovery_timeout_seconds: int = Field(
        default=60, ge=5, le=3600, description="Time before attempting recovery"
    )
    success_threshold: int = Field(
        default=1, ge=1, le=10, description="Successes needed to close circuit"
    )


class HealthCheckConfig(BaseModel):
    """Health check configuration settings."""

    interval_seconds: int = Field(
        default=300, ge=30, le=3600, description="Health check interval"
    )
    timeout_seconds: int = Field(
        default=30, ge=5, le=120, description="Health check timeout"
    )
    enabled_checks: list[str] = Field(
        default=["system_resources", "credential_availability"],
        description="List of enabled health checks",
    )


class MetricsConfig(BaseModel):
    """Metrics collection configuration settings."""

    collection_enabled: bool = Field(
        default=True, description="Enable metrics collection"
    )
    max_history_hours: int = Field(
        default=24, ge=1, le=168, description="Maximum metrics history retention"
    )
    cleanup_interval_minutes: int = Field(
        default=60, ge=5, le=1440, description="Cleanup interval for old metrics"
    )


class SecurityConfig(BaseModel):
    """Security and audit configuration settings."""

    audit_trail_enabled: bool = Field(
        default=True, description="Enable audit trail logging"
    )
    credential_cache_ttl_seconds: int = Field(
        default=300, ge=60, le=3600, description="Credential cache TTL"
    )
    secure_headers_enabled: bool = Field(
        default=True, description="Enable secure HTTP headers"
    )


class OperationalConfig(BaseModel):
    """Complete operational configuration."""

    environment: Environment = Field(
        default=Environment.UNKNOWN, description="Deployment environment"
    )
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    circuit_breaker: CircuitBreakerConfig = Field(default_factory=CircuitBreakerConfig)
    health_check: HealthCheckConfig = Field(default_factory=HealthCheckConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True


class ConfigurationManager:
    """Manages operational configuration and environment detection."""

    def __init__(self):
        self.logger = StructuredLogger("config_manager")
        self._config: OperationalConfig | None = None
        self._environment_info: dict[str, Any] = {}

    def _get_environment(self, environment: Environment | None = None) -> Environment:
        """Get environment with explicit specification or from BEAST_ENVIRONMENT."""
        if environment is not None:
            return environment

        env_var = os.getenv("BEAST_ENVIRONMENT")
        if not env_var:
            raise ValueError(
                "Environment must be explicitly specified via BEAST_ENVIRONMENT "
                "environment variable or load_configuration(environment=...) parameter"
            )

        try:
            return Environment(env_var.lower())
        except ValueError as e:
            raise ValueError(
                f"Invalid BEAST_ENVIRONMENT value: {env_var}. "
                f"Must be one of: {[e.value for e in Environment]}"
            ) from e

    def collect_environment_info(self) -> dict[str, Any]:
        """Collect comprehensive environment information."""
        info = {
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "node": platform.node(),
                "python_version": platform.python_version(),
                "python_implementation": platform.python_implementation(),
            },
            "process": {
                "pid": os.getpid(),
                "ppid": os.getppid() if hasattr(os, "getppid") else None,
                "cwd": os.getcwd(),
                "user": os.getenv("USER") or os.getenv("USERNAME"),
            },
            "environment_variables": {
                key: value
                for key, value in os.environ.items()
                if not any(
                    sensitive in key.lower()
                    for sensitive in [
                        "password",
                        "key",
                        "token",
                        "secret",
                        "auth",
                        "credential",
                    ]
                )
            },
            "paths": {
                "executable": os.path.abspath(__file__),
                "home": os.path.expanduser("~"),
                "temp": (
                    os.path.abspath(os.path.expandvars("$TMPDIR"))
                    if os.getenv("TMPDIR")
                    else "/tmp"
                ),
            },
            "features": {
                "git_repository": os.path.exists(".git"),
                "docker_container": os.path.exists("/.dockerenv"),
                "ci_environment": os.getenv("CI") is not None,
                "virtual_environment": os.getenv("VIRTUAL_ENV") is not None,
            },
        }

        self._environment_info = info
        return info

    def load_configuration(
        self,
        config_file: str | None = None,
        environment_overrides: bool = True,
        environment: Environment | None = None,
    ) -> OperationalConfig:
        """Load operational configuration from file and environment."""
        # Start with default configuration
        config_data = {}

        # Load from file if specified
        if config_file and os.path.exists(config_file):
            try:
                import json

                with open(config_file) as f:
                    file_config = json.load(f)
                config_data.update(file_config)

                self.logger.info(
                    f"Loaded configuration from file: {config_file}",
                    config_file=config_file,
                    configuration_event=True,
                )
            except Exception as e:
                self.logger.error(
                    f"Failed to load configuration file: {config_file}",
                    config_file=config_file,
                    error=str(e),
                    configuration_event=True,
                )
                raise ValueError(f"Invalid configuration file: {config_file}") from e

        # Apply environment variable overrides
        if environment_overrides:
            env_config = self._load_from_environment()
            self._merge_config(config_data, env_config)

        # Get environment (explicit or from BEAST_ENVIRONMENT)
        if "environment" not in config_data:
            env = self._get_environment(environment)
            config_data["environment"] = env.value

        # Apply environment-specific defaults
        self._apply_environment_defaults(config_data)

        try:
            self._config = OperationalConfig(**config_data)

            self.logger.info(
                "Configuration loaded successfully",
                environment=(
                    self._config.environment.value
                    if hasattr(self._config.environment, "value")
                    else str(self._config.environment)
                ),
                logging_level=self._config.logging.level,
                configuration_event=True,
            )

            return self._config

        except Exception as e:
            self.logger.error(
                "Configuration validation failed",
                error=str(e),
                config_data=config_data,
                configuration_event=True,
            )
            raise ValueError(f"Invalid configuration: {e}") from e

    def _load_from_environment(self) -> dict[str, Any]:
        """Load configuration from environment variables."""
        env_config = {}

        # Environment detection
        if os.getenv("BEAST_ENVIRONMENT"):
            env_config["environment"] = os.getenv("BEAST_ENVIRONMENT")

        # Logging configuration
        logging_config = {}
        if os.getenv("BEAST_LOG_LEVEL"):
            logging_config["level"] = os.getenv("BEAST_LOG_LEVEL")
        if os.getenv("BEAST_LOG_FORMAT"):
            logging_config["format"] = os.getenv("BEAST_LOG_FORMAT")
        if os.getenv("BEAST_LOG_FILE"):
            logging_config["file_output"] = os.getenv("BEAST_LOG_FILE")
        if os.getenv("BEAST_LOG_CONSOLE"):
            logging_config["console_output"] = (
                os.getenv("BEAST_LOG_CONSOLE").lower() == "true"
            )

        if logging_config:
            env_config["logging"] = logging_config

        # Retry configuration
        retry_config = {}
        if os.getenv("BEAST_RETRY_MAX_ATTEMPTS"):
            retry_config["max_attempts"] = int(os.getenv("BEAST_RETRY_MAX_ATTEMPTS"))
        if os.getenv("BEAST_RETRY_BASE_DELAY"):
            retry_config["base_delay_seconds"] = float(
                os.getenv("BEAST_RETRY_BASE_DELAY")
            )
        if os.getenv("BEAST_RETRY_MAX_DELAY"):
            retry_config["max_delay_seconds"] = float(
                os.getenv("BEAST_RETRY_MAX_DELAY")
            )

        if retry_config:
            env_config["retry"] = retry_config

        # Circuit breaker configuration
        circuit_config = {}
        if os.getenv("BEAST_CIRCUIT_FAILURE_THRESHOLD"):
            circuit_config["failure_threshold"] = int(
                os.getenv("BEAST_CIRCUIT_FAILURE_THRESHOLD")
            )
        if os.getenv("BEAST_CIRCUIT_RECOVERY_TIMEOUT"):
            circuit_config["recovery_timeout_seconds"] = int(
                os.getenv("BEAST_CIRCUIT_RECOVERY_TIMEOUT")
            )

        if circuit_config:
            env_config["circuit_breaker"] = circuit_config

        # Metrics configuration
        metrics_config = {}
        if os.getenv("BEAST_METRICS_ENABLED"):
            metrics_config["collection_enabled"] = (
                os.getenv("BEAST_METRICS_ENABLED").lower() == "true"
            )
        if os.getenv("BEAST_METRICS_HISTORY_HOURS"):
            metrics_config["max_history_hours"] = int(
                os.getenv("BEAST_METRICS_HISTORY_HOURS")
            )

        if metrics_config:
            env_config["metrics"] = metrics_config

        return env_config

    def _merge_config(self, base: dict[str, Any], override: dict[str, Any]) -> None:
        """Merge configuration dictionaries recursively."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def _apply_environment_defaults(self, config_data: dict[str, Any]) -> None:
        """Apply environment-specific configuration defaults."""
        environment = config_data.get("environment", Environment.UNKNOWN)

        if isinstance(environment, str):
            try:
                environment = Environment(environment)
            except ValueError:
                environment = Environment.UNKNOWN

        # Apply environment-specific defaults
        if environment == Environment.DEVELOPMENT:
            # Development: More verbose logging, shorter timeouts
            config_data.setdefault("logging", {}).setdefault("level", "DEBUG")
            config_data.setdefault("retry", {}).setdefault("max_attempts", 2)
            config_data.setdefault("circuit_breaker", {}).setdefault(
                "failure_threshold", 3
            )

        elif environment == Environment.TESTING:
            # Testing: Minimal logging, fast failures
            config_data.setdefault("logging", {}).setdefault("level", "WARNING")
            config_data.setdefault("retry", {}).setdefault("max_attempts", 1)
            config_data.setdefault("circuit_breaker", {}).setdefault(
                "failure_threshold", 2
            )
            config_data.setdefault("metrics", {}).setdefault(
                "collection_enabled", False
            )

        elif environment == Environment.PRODUCTION:
            # Production: Conservative settings, full monitoring
            config_data.setdefault("logging", {}).setdefault("level", "INFO")
            config_data.setdefault("retry", {}).setdefault("max_attempts", 5)
            config_data.setdefault("circuit_breaker", {}).setdefault(
                "failure_threshold", 10
            )
            config_data.setdefault("metrics", {}).setdefault("max_history_hours", 72)

        # UNKNOWN and STAGING use base defaults (INFO logging, 3 retry attempts, etc.)

    def get_configuration(self) -> OperationalConfig | None:
        """Get current configuration."""
        return self._config

    def validate_configuration(self, config: OperationalConfig) -> list[str]:
        """Validate configuration and return list of issues."""
        issues = []

        # Check logging configuration
        if config.logging.file_output:
            try:
                # Check if directory exists and is writable
                log_dir = os.path.dirname(config.logging.file_output)
                if log_dir and not os.path.exists(log_dir):
                    issues.append(f"Log directory does not exist: {log_dir}")
                elif log_dir and not os.access(log_dir, os.W_OK):
                    issues.append(f"Log directory is not writable: {log_dir}")
            except Exception as e:
                issues.append(f"Invalid log file path: {e}")

        # Check retry configuration consistency
        if config.retry.max_delay_seconds < config.retry.base_delay_seconds:
            issues.append("max_delay_seconds must be greater than base_delay_seconds")

        # Check circuit breaker configuration
        if config.circuit_breaker.recovery_timeout_seconds < 5:
            issues.append(
                "Circuit breaker recovery timeout should be at least 5 seconds"
            )

        # Check health check configuration
        if config.health_check.timeout_seconds >= config.health_check.interval_seconds:
            issues.append("Health check timeout should be less than interval")

        return issues

    def get_environment_info(self) -> dict[str, Any]:
        """Get collected environment information."""
        if not self._environment_info:
            self.collect_environment_info()
        return self._environment_info
