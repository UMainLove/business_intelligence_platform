"""
Synthetic tests for error handling without external dependencies.
"""

import pytest

from src.error_handling import (
    APIError,
    BusinessIntelligenceError,
    ConfigurationError,
    DatabaseError,
    ErrorTracker,
    ModelError,
    ValidationError,
    error_tracker,
    handle_errors,
    retry_with_backoff,
    safe_execute,
    validate_input,
)


class TestBusinessIntelligenceErrors:
    """Test custom exception classes."""

    def test_business_intelligence_error_creation(self):
        """Test base exception creation."""
        error = BusinessIntelligenceError(
            message="Test error", error_code="TEST_ERROR", details={"key": "value"}
        )

        assert str(error) == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.details == {"key": "value"}
        assert error.timestamp is not None

    def test_specific_error_types(self):
        """Test specific error type inheritance."""
        db_error = DatabaseError("DB error")
        api_error = APIError("API error")
        model_error = ModelError("Model error")
        validation_error = ValidationError("Validation error")
        config_error = ConfigurationError("Config error")

        assert isinstance(db_error, BusinessIntelligenceError)
        assert isinstance(api_error, BusinessIntelligenceError)
        assert isinstance(model_error, BusinessIntelligenceError)
        assert isinstance(validation_error, BusinessIntelligenceError)
        assert isinstance(config_error, BusinessIntelligenceError)


class TestRetryWithBackoff:
    """Test retry decorator with synthetic failures."""

    def test_successful_function_no_retry(self):
        """Test function that succeeds on first try."""

        @retry_with_backoff(max_retries=3, initial_delay=0.001)
        def success_function():
            return "success"

        result = success_function()
        assert result == "success"

    def test_retry_with_eventual_success(self):
        """Test function that fails then succeeds."""
        call_count = [0]

        @retry_with_backoff(max_retries=3, initial_delay=0.001)
        def eventually_success():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = eventually_success()
        assert result == "success"
        assert call_count[0] == 3

    def test_retry_exhaustion(self):
        """Test function that always fails."""

        @retry_with_backoff(max_retries=2, initial_delay=0.001)
        def always_fails():
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            always_fails()

    def test_retry_with_callback(self):
        """Test retry with callback function."""
        callback_calls = []

        def retry_callback(attempt, error, delay):
            callback_calls.append((attempt, str(error), delay))

        @retry_with_backoff(max_retries=2, initial_delay=0.001, on_retry=retry_callback)
        def fails_twice():
            if len(callback_calls) < 2:
                raise ValueError("Failing")
            return "success"

        result = fails_twice()
        assert result == "success"
        assert len(callback_calls) == 2


class TestHandleErrors:
    """Test error handling decorator."""

    def test_successful_function(self):
        """Test decorator with successful function."""

        @handle_errors()
        def success_function():
            return "success"

        result = success_function()
        assert result == "success"

    def test_error_mapping(self):
        """Test error mapping functionality."""

        @handle_errors(error_mapping={ValueError: ValidationError})
        def raises_value_error():
            raise ValueError("Original error")

        with pytest.raises(ValidationError) as exc_info:
            raises_value_error()

        assert "Original error" in str(exc_info.value)

    def test_unmapped_error(self):
        """Test handling of unmapped errors."""

        @handle_errors(default_error=ConfigurationError)
        def raises_unmapped_error():
            raise RuntimeError("Unmapped error")

        with pytest.raises(ConfigurationError) as exc_info:
            raises_unmapped_error()

        assert "Unmapped error" in str(exc_info.value)

    def test_business_intelligence_error_passthrough(self):
        """Test that BI errors pass through unchanged."""

        @handle_errors()
        def raises_bi_error():
            raise ValidationError("BI error")

        with pytest.raises(ValidationError, match="BI error"):
            raises_bi_error()


class TestSafeExecute:
    """Test safe execution functionality."""

    def test_safe_execute_success(self):
        """Test safe execution with successful function."""

        def success_function():
            return "success"

        result = safe_execute(success_function, fallback_value="fallback")
        assert result == "success"

    def test_safe_execute_with_fallback(self):
        """Test safe execution with fallback on error."""

        def failing_function():
            raise ValueError("Test error")

        result = safe_execute(failing_function, fallback_value="fallback")
        assert result == "fallback"

    def test_safe_execute_with_args(self):
        """Test safe execution with arguments."""

        def add_numbers(a, b):
            return a + b

        result = safe_execute(add_numbers, 2, 3, fallback_value=0)
        assert result == 5

    def test_safe_execute_with_kwargs(self):
        """Test safe execution with keyword arguments."""

        def multiply_numbers(a, b=2):
            return a * b

        result = safe_execute(multiply_numbers, 5, b=3, fallback_value=0)
        assert result == 15


class TestValidateInput:
    """Test input validation functionality."""

    def test_valid_input(self):
        """Test validation with valid input."""
        data = {"name": "test", "value": 42}
        required_fields = ["name", "value"]
        field_types = {"name": str, "value": int}

        # Should not raise any exception
        validate_input(data, required_fields, field_types)

    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        data = {"name": "test"}
        required_fields = ["name", "value"]

        with pytest.raises(ValidationError, match="Missing required fields: value"):
            validate_input(data, required_fields)

    def test_wrong_field_types(self):
        """Test validation with wrong field types."""
        data = {"name": 123, "value": "not_int"}
        required_fields = ["name", "value"]
        field_types = {"name": str, "value": int}

        with pytest.raises(ValidationError, match="Type validation failed"):
            validate_input(data, required_fields, field_types)

    def test_non_dict_input(self):
        """Test validation with non-dictionary input."""
        with pytest.raises(ValidationError, match="Input data must be a dictionary"):
            validate_input("not a dict", [])


class TestErrorTracker:
    """Test error tracking functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tracker = ErrorTracker(max_errors=5)

    def test_record_error(self):
        """Test recording an error."""
        error = ValueError("Test error")
        self.tracker.record_error(error, {"context": "test"})

        assert len(self.tracker.errors) == 1
        assert self.tracker.errors[0]["error_type"] == "ValueError"
        assert self.tracker.errors[0]["message"] == "Test error"

    def test_record_bi_error(self):
        """Test recording a BusinessIntelligence error."""
        error = ValidationError(
            message="Validation failed", error_code="VALIDATION_FAILED", details={"field": "test"}
        )
        self.tracker.record_error(error)

        assert len(self.tracker.errors) == 1
        assert self.tracker.errors[0]["error_code"] == "VALIDATION_FAILED"
        assert self.tracker.errors[0]["details"] == {"field": "test"}

    def test_max_errors_limit(self):
        """Test maximum errors limit."""
        for i in range(10):
            self.tracker.record_error(ValueError(f"Error {i}"))

        # Should only keep the last 5 errors
        assert len(self.tracker.errors) == 5
        assert self.tracker.errors[-1]["message"] == "Error 9"

    def test_get_error_summary(self):
        """Test getting error summary."""
        # Record some errors
        self.tracker.record_error(ValueError("Error 1"))
        self.tracker.record_error(ValueError("Error 2"))
        self.tracker.record_error(TypeError("Error 3"))

        summary = self.tracker.get_error_summary(hours=24)

        assert summary["total_errors"] == 3
        assert summary["error_types"]["ValueError"] == 2
        assert summary["error_types"]["TypeError"] == 1
        assert len(summary["recent_errors"]) == 3


class TestGlobalErrorTracker:
    """Test global error tracker."""

    def test_track_errors_decorator(self):
        """Test track_errors decorator."""
        from src.error_handling import track_errors

        @track_errors
        def failing_function():
            raise ValueError("Tracked error")

        # Clear any existing errors
        error_tracker.errors.clear()

        with pytest.raises(ValueError):
            failing_function()

        assert len(error_tracker.errors) >= 1
        assert any("Tracked error" in error["message"] for error in error_tracker.errors)


class TestRetryConfigurations:
    """Test predefined retry configurations."""

    def test_api_retry_config_exists(self):
        """Test API retry configuration."""
        from src.error_handling import API_RETRY_CONFIG

        assert "max_retries" in API_RETRY_CONFIG
        assert "initial_delay" in API_RETRY_CONFIG
        assert "exceptions" in API_RETRY_CONFIG

    def test_database_retry_config_exists(self):
        """Test database retry configuration."""
        from src.error_handling import DATABASE_RETRY_CONFIG

        assert "max_retries" in DATABASE_RETRY_CONFIG
        assert "initial_delay" in DATABASE_RETRY_CONFIG
        assert "exceptions" in DATABASE_RETRY_CONFIG

    def test_model_retry_config_exists(self):
        """Test model retry configuration."""
        from src.error_handling import MODEL_RETRY_CONFIG

        assert "max_retries" in MODEL_RETRY_CONFIG
        assert "initial_delay" in MODEL_RETRY_CONFIG
        assert "exceptions" in MODEL_RETRY_CONFIG
