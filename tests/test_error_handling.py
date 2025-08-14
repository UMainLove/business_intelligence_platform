"""
Tests for error handling and retry logic.
"""
import pytest
import time
from unittest.mock import Mock, patch
from src.error_handling import (
    BusinessIntelligenceError, DatabaseError, APIError, ModelError, ValidationError,
    retry_with_backoff, handle_errors, safe_execute, validate_input,
    ErrorTracker, track_errors, error_tracker
)

class TestCustomExceptions:
    """Test custom exception hierarchy."""
    
    def test_business_intelligence_error(self):
        """Test base exception."""
        error = BusinessIntelligenceError(
            "Test error",
            error_code="TEST_ERROR",
            details={"key": "value"}
        )
        
        assert str(error) == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.details == {"key": "value"}
        assert error.timestamp is not None
    
    def test_database_error(self):
        """Test database error inheritance."""
        error = DatabaseError("Database connection failed")
        assert isinstance(error, BusinessIntelligenceError)
        assert str(error) == "Database connection failed"
    
    def test_api_error(self):
        """Test API error inheritance."""
        error = APIError("API request failed")
        assert isinstance(error, BusinessIntelligenceError)
    
    def test_model_error(self):
        """Test model error inheritance."""
        error = ModelError("Model inference failed")
        assert isinstance(error, BusinessIntelligenceError)
    
    def test_validation_error(self):
        """Test validation error inheritance."""
        error = ValidationError("Input validation failed")
        assert isinstance(error, BusinessIntelligenceError)

class TestRetryWithBackoff:
    """Test retry decorator functionality."""
    
    def test_successful_function(self):
        """Test retry decorator with successful function."""
        @retry_with_backoff(max_retries=3)
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"
    
    def test_function_succeeds_after_retries(self):
        """Test function that fails then succeeds."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = flaky_function()
        assert result == "success"
        assert call_count == 3
    
    def test_function_exhausts_retries(self):
        """Test function that always fails."""
        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        def failing_function():
            raise ConnectionError("Persistent failure")
        
        with pytest.raises(ConnectionError):
            failing_function()
    
    def test_specific_exceptions_only(self):
        """Test retry only catches specified exceptions."""
        @retry_with_backoff(max_retries=2, exceptions=(ConnectionError,))
        def function_with_different_error():
            raise ValueError("Different error")
        
        # Should not retry ValueError
        with pytest.raises(ValueError):
            function_with_different_error()
    
    def test_backoff_timing(self):
        """Test exponential backoff timing."""
        call_times = []
        
        @retry_with_backoff(max_retries=3, initial_delay=0.1, backoff_factor=2.0)
        def timed_function():
            call_times.append(time.time())
            raise ConnectionError("Timing test")
        
        with pytest.raises(ConnectionError):
            timed_function()
        
        # Should have made 4 attempts (initial + 3 retries)
        assert len(call_times) == 4
        
        # Check increasing delays (allowing some tolerance)
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        assert delay2 > delay1 * 1.5  # Exponential increase

class TestHandleErrors:
    """Test error handling decorator."""
    
    def test_successful_function(self):
        """Test error handler with successful function."""
        @handle_errors()
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"
    
    def test_maps_exceptions(self):
        """Test exception mapping."""
        @handle_errors(error_mapping={ValueError: ValidationError})
        def function_with_value_error():
            raise ValueError("Invalid value")
        
        with pytest.raises(ValidationError):
            function_with_value_error()
    
    def test_preserves_custom_exceptions(self):
        """Test that custom exceptions are preserved."""
        @handle_errors()
        def function_with_custom_error():
            raise DatabaseError("Custom database error")
        
        with pytest.raises(DatabaseError):
            function_with_custom_error()
    
    def test_default_error_mapping(self):
        """Test default error type for unmapped exceptions."""
        @handle_errors(default_error=APIError)
        def function_with_runtime_error():
            raise RuntimeError("Runtime error")
        
        with pytest.raises(APIError):
            function_with_runtime_error()

class TestSafeExecute:
    """Test safe execution utility."""
    
    def test_successful_execution(self):
        """Test safe execution with successful function."""
        def successful_function(x, y):
            return x + y
        
        result = safe_execute(successful_function, 2, 3)
        assert result == 5
    
    def test_execution_with_fallback(self):
        """Test safe execution with fallback value."""
        def failing_function():
            raise ValueError("Test error")
        
        result = safe_execute(
            failing_function,
            fallback_value="fallback",
            error_context="test context"
        )
        assert result == "fallback"
    
    def test_execution_with_kwargs(self):
        """Test safe execution with keyword arguments."""
        def function_with_kwargs(x, y=10):
            return x * y
        
        result = safe_execute(function_with_kwargs, 5, y=3)
        assert result == 15

class TestValidateInput:
    """Test input validation utility."""
    
    def test_valid_input(self):
        """Test validation with valid input."""
        data = {"name": "test", "value": 123}
        required_fields = ["name", "value"]
        field_types = {"name": str, "value": int}
        
        # Should not raise any exception
        validate_input(data, required_fields, field_types)
    
    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        data = {"name": "test"}
        required_fields = ["name", "value"]
        
        with pytest.raises(ValidationError) as exc_info:
            validate_input(data, required_fields)
        
        assert "Missing required fields" in str(exc_info.value)
        assert "value" in str(exc_info.value)
    
    def test_wrong_field_types(self):
        """Test validation with wrong field types."""
        data = {"name": 123, "value": "not_int"}
        required_fields = ["name", "value"]
        field_types = {"name": str, "value": int}
        
        with pytest.raises(ValidationError) as exc_info:
            validate_input(data, required_fields, field_types)
        
        assert "Type validation failed" in str(exc_info.value)
    
    def test_non_dict_input(self):
        """Test validation with non-dictionary input."""
        with pytest.raises(ValidationError) as exc_info:
            validate_input("not_a_dict", [])
        
        assert "must be a dictionary" in str(exc_info.value)

class TestErrorTracker:
    """Test error tracking functionality."""
    
    def test_record_error(self, clean_error_tracker):
        """Test recording errors."""
        error = ValueError("Test error")
        clean_error_tracker.record_error(error, {"context": "test"})
        
        assert len(clean_error_tracker.errors) == 1
        recorded = clean_error_tracker.errors[0]
        assert recorded["error_type"] == "ValueError"
        assert recorded["message"] == "Test error"
        assert recorded["context"] == {"context": "test"}
    
    def test_record_custom_error(self, clean_error_tracker):
        """Test recording custom business intelligence errors."""
        error = DatabaseError("DB error", "DB_001", {"table": "users"})
        clean_error_tracker.record_error(error)
        
        recorded = clean_error_tracker.errors[0]
        assert recorded["error_type"] == "DatabaseError"
        assert recorded["error_code"] == "DB_001"
        assert recorded["details"] == {"table": "users"}
    
    def test_error_summary(self, clean_error_tracker):
        """Test error summary generation."""
        # Record multiple errors
        clean_error_tracker.record_error(ValueError("Error 1"))
        clean_error_tracker.record_error(ValueError("Error 2"))
        clean_error_tracker.record_error(ConnectionError("Error 3"))
        
        summary = clean_error_tracker.get_error_summary(hours=24)
        
        assert summary["total_errors"] == 3
        assert summary["error_types"]["ValueError"] == 2
        assert summary["error_types"]["ConnectionError"] == 1
        assert len(summary["recent_errors"]) <= 10
    
    def test_max_errors_limit(self):
        """Test maximum error limit."""
        tracker = ErrorTracker(max_errors=5)
        
        # Record more errors than the limit
        for i in range(10):
            tracker.record_error(ValueError(f"Error {i}"))
        
        # Should only keep the last 5 errors
        assert len(tracker.errors) == 5
        assert tracker.errors[-1]["message"] == "Error 9"

class TestTrackErrorsDecorator:
    """Test error tracking decorator."""
    
    def test_successful_function(self, clean_error_tracker):
        """Test decorator with successful function."""
        @track_errors
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"
        assert len(clean_error_tracker.errors) == 0
    
    def test_function_with_error(self, clean_error_tracker):
        """Test decorator with failing function."""
        @track_errors
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_function()
        
        # Error should be tracked
        assert len(clean_error_tracker.errors) == 1
        recorded = clean_error_tracker.errors[0]
        assert recorded["error_type"] == "ValueError"
        assert recorded["context"]["function"] == "failing_function"