"""
Comprehensive error handling and logging for the monitoring stack.

This module provides robust error handling, logging configuration, and
monitoring-specific exceptions for better observability and debugging.
"""

import json
import logging
import traceback
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional


# Configure structured logging
class LogLevel(Enum):
    """Log levels for the monitoring stack."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class MonitoringError(Exception):
    """Base exception for monitoring stack errors."""

    def __init__(self, message: str, context: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
        }


class PrometheusError(MonitoringError):
    """Exception for Prometheus-related errors."""


class GrafanaError(MonitoringError):
    """Exception for Grafana-related errors."""


class AlertManagerError(MonitoringError):
    """Exception for AlertManager-related errors."""


class MetricsCollectionError(MonitoringError):
    """Exception for metrics collection errors."""


class ConfigurationError(MonitoringError):
    """Exception for configuration-related errors."""


class ConnectionError(MonitoringError):
    """Exception for connection-related errors."""


class ValidationError(MonitoringError):
    """Exception for validation errors."""


class MonitoringLogger:
    """
    Centralized logger for the monitoring stack with structured logging support.

    Provides consistent logging format, context injection, and error tracking.
    """

    def __init__(self, name: str = "monitoring", level: str = "INFO"):
        """Initialize the monitoring logger."""
        self.logger = logging.getLogger(name)
        self.set_level(level)
        self.error_count = 0
        self.warning_count = 0

        # Configure formatter for structured logging
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(component)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Add console handler if not already present
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def set_level(self, level: str):
        """Set logging level."""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        self.logger.setLevel(level_map.get(level.upper(), logging.INFO))

    def debug(self, message: str, component: str = "general", **kwargs):
        """Log debug message with context."""
        extra = {"component": component}
        self.logger.debug(self._format_message(message, kwargs), extra=extra)

    def info(self, message: str, component: str = "general", **kwargs):
        """Log info message with context."""
        extra = {"component": component}
        self.logger.info(self._format_message(message, kwargs), extra=extra)

    def warning(self, message: str, component: str = "general", **kwargs):
        """Log warning message with context."""
        self.warning_count += 1
        extra = {"component": component}
        self.logger.warning(self._format_message(message, kwargs), extra=extra)

    def error(self, message: str, component: str = "general", error: Exception = None, **kwargs):
        """Log error message with exception details."""
        self.error_count += 1
        extra = {"component": component}

        if error:
            kwargs["error_type"] = type(error).__name__
            kwargs["error_message"] = str(error)
            if hasattr(error, "context"):
                kwargs["error_context"] = error.context

        self.logger.error(self._format_message(message, kwargs), extra=extra)

        if error and self.logger.level == logging.DEBUG:
            self.logger.debug(f"Traceback: {traceback.format_exc()}", extra=extra)

    def critical(self, message: str, component: str = "general", error: Exception = None, **kwargs):
        """Log critical message with exception details."""
        self.error_count += 1
        extra = {"component": component}

        if error:
            kwargs["error_type"] = type(error).__name__
            kwargs["error_message"] = str(error)

        self.logger.critical(self._format_message(message, kwargs), extra=extra)

        if error:
            self.logger.critical(f"Traceback: {traceback.format_exc()}", extra=extra)

    def _format_message(self, message: str, context: Dict[str, Any]) -> str:
        """Format message with context."""
        if context:
            context_str = json.dumps(context, default=str)
            return f"{message} | Context: {context_str}"
        return message

    def get_stats(self) -> Dict[str, int]:
        """Get logging statistics."""
        return {"errors": self.error_count, "warnings": self.warning_count}

    def reset_stats(self):
        """Reset logging statistics."""
        self.error_count = 0
        self.warning_count = 0


# Global logger instance
monitoring_logger = MonitoringLogger("monitoring.stack")


def _handle_specific_error(error: Exception, func_name: str, component: str, raise_on_error: bool, default_return: Any):
    """Handle specific error types with appropriate logging."""
    if isinstance(error, MonitoringError):
        monitoring_logger.error(f"Monitoring error in {func_name}", component=component, error=error)
    elif isinstance(error, ConnectionError):
        monitoring_logger.error(f"Connection error in {func_name}", component=component, error=error, retry_possible=True)
    elif isinstance(error, ValidationError):
        monitoring_logger.warning(f"Validation error in {func_name}", component=component, error=error)
    else:
        monitoring_logger.critical(f"Unexpected error in {func_name}", component=component, error=error)

    if raise_on_error:
        raise
    return default_return


def with_error_handling(
    component: str = "general", raise_on_error: bool = False, default_return: Any = None
):
    """
    Decorator for adding comprehensive error handling to functions.

    Args:
        component: Component name for logging context
        raise_on_error: Whether to re-raise exceptions after logging
        default_return: Default value to return on error

    Example:
        @with_error_handling(component="prometheus", raise_on_error=False, default_return=[])
        def query_metrics():
            # function implementation
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            monitoring_logger.debug(
                f"Calling {func_name}",
                component=component,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys()),
            )

            try:
                result = func(*args, **kwargs)
                monitoring_logger.debug(f"Successfully completed {func_name}", component=component)
                return result
            except Exception as e:
                return _handle_specific_error(e, func_name, component, raise_on_error, default_return)

        return wrapper

    return decorator


def validate_config(config: Dict[str, Any], required_fields: list) -> bool:
    """
    Validate configuration dictionary has required fields.

    Args:
        config: Configuration dictionary to validate
        required_fields: List of required field names

    Returns:
        True if valid, raises ValidationError otherwise
    """
    missing_fields = [field for field in required_fields if field not in config]

    if missing_fields:
        raise ValidationError(
            f"Missing required configuration fields: {missing_fields}",
            context={"provided_fields": list(config.keys()), "required_fields": required_fields},
        )

    return True


class ErrorAggregator:
    """
    Aggregates errors for batch reporting and analysis.

    Useful for collecting multiple errors during operations and
    reporting them together.
    """

    def __init__(self, component: str = "general"):
        self.component = component
        self.errors = []
        self.warnings = []

    def add_error(self, error: Exception, context: Dict[str, Any] = None):
        """Add an error to the aggregator."""
        self.errors.append({"error": error, "context": context or {}, "timestamp": datetime.now()})

    def add_warning(self, message: str, context: Dict[str, Any] = None):
        """Add a warning to the aggregator."""
        self.warnings.append(
            {"message": message, "context": context or {}, "timestamp": datetime.now()}
        )

    def has_errors(self) -> bool:
        """Check if any errors have been collected."""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if any warnings have been collected."""
        return len(self.warnings) > 0

    def log_all(self, logger: Optional[MonitoringLogger] = None):
        """Log all collected errors and warnings."""
        logger = logger or monitoring_logger

        for warning in self.warnings:
            logger.warning(warning["message"], component=self.component, **warning["context"])

        for error_info in self.errors:
            logger.error(
                "Aggregated error",
                component=self.component,
                error=error_info["error"],
                **error_info["context"],
            )

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of collected errors and warnings."""
        return {
            "component": self.component,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": [str(e["error"]) for e in self.errors],
            "warnings": [w["message"] for w in self.warnings],
        }

    def clear(self):
        """Clear all collected errors and warnings."""
        self.errors = []
        self.warnings = []


class CircuitBreaker:
    """
    Circuit breaker pattern for handling repeated failures.

    Prevents repeated calls to failing services and provides
    graceful degradation.
    """

    def __init__(self, failure_threshold: int = 5, timeout: int = 60, component: str = "general"):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.component = component
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False

    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.is_open:
            if self._should_attempt_reset():
                self.is_open = False
                monitoring_logger.info("Circuit breaker reset", component=self.component)
            else:
                raise ConnectionError(
                    "Circuit breaker is open",
                    context={"component": self.component, "failure_count": self.failure_count},
                )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            monitoring_logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures",
                component=self.component,
            )

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        if not self.last_failure_time:
            return True

        time_since_failure = (datetime.now() - self.last_failure_time).seconds
        return time_since_failure >= self.timeout

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        return {
            "component": self.component,
            "is_open": self.is_open,
            "failure_count": self.failure_count,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
        }
