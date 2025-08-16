"""
Error handling and retry logic for Business Intelligence Platform.
"""

import functools
import logging
import time
import traceback
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


class BusinessIntelligenceError(Exception):
    """Base exception for Business Intelligence Platform."""

    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc)


class DatabaseError(BusinessIntelligenceError):
    """Database operation errors."""


class APIError(BusinessIntelligenceError):
    """External API errors."""


class ModelError(BusinessIntelligenceError):
    """AI model errors."""


class ValidationError(BusinessIntelligenceError):
    """Input validation errors."""


class ConfigurationError(BusinessIntelligenceError):
    """Configuration and setup errors."""


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None,
):
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback function called on each retry
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries: {str(e)}",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt + 1,
                                "max_retries": max_retries,
                                "error": str(e),
                                "traceback": traceback.format_exc(),
                            },
                        )
                        raise

                    logger.warning(
                        f"Function {func.__name__} failed on attempt {attempt + 1}/"
                        f"{max_retries + 1}: {str(e)}. "
                        f"Retrying in {delay:.2f} seconds...",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                            "delay": delay,
                            "error": str(e),
                        },
                    )

                    if on_retry:
                        try:
                            on_retry(attempt + 1, e, delay)
                        except Exception as retry_error:
                            logger.error(f"Error in retry callback: {retry_error}")

                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)

            # This should never be reached, but just in case
            raise last_exception

        return wrapper

    return decorator


def handle_errors(
    error_mapping: Optional[Dict[Type[Exception], Type[BusinessIntelligenceError]]] = None,
    default_error: Type[BusinessIntelligenceError] = BusinessIntelligenceError,
    log_errors: bool = True,
):
    """
    Decorator for standardized error handling and logging.

    Args:
        error_mapping: Map of original exceptions to custom exceptions
        default_error: Default exception type for unmapped errors
        log_errors: Whether to log errors
    """
    if error_mapping is None:
        error_mapping = {
            ConnectionError: DatabaseError,
            TimeoutError: APIError,
            ValueError: ValidationError,
            KeyError: ConfigurationError,
        }

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BusinessIntelligenceError:
                # Re-raise our custom exceptions as-is
                raise
            except Exception as e:
                # Map to appropriate custom exception
                custom_exception_type = error_mapping.get(type(e), default_error)

                error_details = {
                    "function": func.__name__,
                    "original_error": str(e),
                    "error_type": type(e).__name__,
                    "func_args": str(args)[:200],  # Truncate for logging
                    "func_kwargs": str(kwargs)[:200],
                }

                if log_errors:
                    logger.error(
                        f"Error in {func.__name__}: {str(e)}", extra=error_details, exc_info=True
                    )

                # Create and raise custom exception
                custom_error = custom_exception_type(
                    message=f"Error in {func.__name__}: {str(e)}",
                    error_code=f"{func.__name__}_{type(e).__name__}".upper(),
                    details=error_details,
                )
                raise custom_error from e

        return wrapper

    return decorator


def safe_execute(
    func: Callable,
    *args,
    fallback_value: Any = None,
    error_context: str = "",
    log_level: str = "error",
    **kwargs,
) -> Any:
    """
    Safely execute a function with error handling and fallback.

    Args:
        func: Function to execute
        *args: Arguments for the function
        fallback_value: Value to return if function fails
        error_context: Additional context for error logging
        log_level: Logging level for errors
        **kwargs: Keyword arguments for the function

    Returns:
        Function result or fallback_value if function fails
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_msg = f"Safe execution failed for {func.__name__}"
        if error_context:
            error_msg += f" ({error_context})"
        error_msg += f": {str(e)}"

        getattr(logger, log_level)(
            error_msg,
            extra={
                "function": func.__name__,
                "error_context": error_context,
                "error": str(e),
                "fallback_used": True,
                "fallback_value": str(fallback_value),
            },
            exc_info=log_level == "error",
        )

        return fallback_value


def validate_input(
    data: Dict[str, Any], required_fields: List[str], field_types: Dict[str, Type] = None
) -> None:
    """
    Validate input data with required fields and types.

    Args:
        data: Input data to validate
        required_fields: List of required field names
        field_types: Optional mapping of field names to expected types

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValidationError("Input data must be a dictionary")

    # Check required fields
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing_fields)}",
            error_code="MISSING_FIELDS",
            details={"missing_fields": missing_fields},
        )

    # Check field types
    if field_types:
        type_errors = []
        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                type_errors.append(
                    f"{field}: expected {expected_type.__name__}, got {type(data[field]).__name__}"
                )

        if type_errors:
            raise ValidationError(
                f"Type validation failed: {'; '.join(type_errors)}",
                error_code="TYPE_VALIDATION_FAILED",
                details={"type_errors": type_errors},
            )


class ErrorTracker:
    """Track and analyze errors for monitoring."""

    def __init__(self, max_errors: int = 100):
        self.max_errors = max_errors
        self.errors: List[Dict[str, Any]] = []

    def record_error(self, error: Exception, context: Dict[str, Any] = None):
        """Record an error for tracking."""
        error_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error_type": type(error).__name__,
            "message": str(error),
            "context": context or {},
        }

        if isinstance(error, BusinessIntelligenceError):
            error_record.update({"error_code": error.error_code, "details": error.details})

        self.errors.append(error_record)

        # Keep only recent errors
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors :]

    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of recent errors."""
        cutoff_time = datetime.now(timezone.utc).timestamp() - (hours * 3600)

        recent_errors = [
            error
            for error in self.errors
            if datetime.fromisoformat(error["timestamp"]).timestamp() > cutoff_time
        ]

        error_counts = {}
        for error in recent_errors:
            error_type = error["error_type"]
            error_counts[error_type] = error_counts.get(error_type, 0) + 1

        return {
            "total_errors": len(recent_errors),
            "error_types": error_counts,
            "recent_errors": recent_errors[-10:],  # Last 10 errors
            "time_window_hours": hours,
        }


# Global error tracker instance
error_tracker = ErrorTracker()


def track_errors(func: Callable) -> Callable:
    """Decorator to automatically track errors."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_tracker.record_error(
                e, context={"function": func.__name__, "module": func.__module__}
            )
            raise

    return wrapper


# Common retry configurations
API_RETRY_CONFIG = {
    "max_retries": 3,
    "initial_delay": 1.0,
    "max_delay": 30.0,
    "exceptions": (APIError, ConnectionError, TimeoutError),
}

DATABASE_RETRY_CONFIG = {
    "max_retries": 2,
    "initial_delay": 0.5,
    "max_delay": 10.0,
    "exceptions": (DatabaseError, ConnectionError),
}

MODEL_RETRY_CONFIG = {
    "max_retries": 2,
    "initial_delay": 2.0,
    "max_delay": 60.0,
    "exceptions": (ModelError, TimeoutError),
}
