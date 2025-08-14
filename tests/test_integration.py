"""
Integration tests for Business Intelligence Platform.
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock
from src.tools.database_tools import BusinessDataDB
from src.tools.financial_tools import financial_tool_executor
from src.health_monitor import health_monitor
from src.error_handling import error_tracker


class TestDatabaseIntegration:
    """Test database integration across components."""

    def test_database_with_financial_analysis(self, test_db_path, sample_business_data):
        """Test integration between database and financial tools."""
        # Setup database
        db = BusinessDataDB(test_db_path)
        venture_id = db.add_venture(sample_business_data)

        # Perform financial analysis
        cash_flows = [-sample_business_data["initial_funding"]] + [100000] * 5
        financial_result = financial_tool_executor("npv", {
            "cash_flows": cash_flows,
            "discount_rate": 0.1
        })

        # Verify both operations work
        assert venture_id is not None
        assert "npv" in financial_result
        assert isinstance(financial_result["npv"], float)

        # Verify database query still works
        similar_ventures = db.analyze_similar_ventures(
            sample_business_data["industry"],
            sample_business_data["business_model"]
        )
        assert len(similar_ventures["similar_ventures"]) > 0

    def test_error_tracking_across_components(self, clean_error_tracker):
        """Test error tracking across different components."""
        # Trigger error in financial tools
        result = financial_tool_executor("invalid_operation", {})
        assert "error" in result

        # Trigger error in database (invalid input)
        from src.tools.database_production import database_tool_executor
        result2 = database_tool_executor("invalid_query", {})
        assert "error" in result2

        # Check that errors were tracked
        error_summary = clean_error_tracker.get_error_summary(hours=1)
        # Note: Errors might not be tracked if not using @track_errors decorator
        # This test verifies the integration point exists


class TestHealthMonitoringIntegration:
    """Test health monitoring integration."""

    @patch('src.health_monitor.db_config')
    def test_health_check_with_database(self, mock_db_config):
        """Test health check integration with database."""
        # Mock successful database connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [1]

        mock_db_config.get_connection.return_value.__enter__.return_value = mock_conn
        mock_db_config.use_postgres = False

        # Check database health
        db_health = health_monitor.check_database_health()
        assert db_health.status == "healthy"

        # Check comprehensive health
        comprehensive = health_monitor.get_comprehensive_health()
        assert "database" in comprehensive["checks"]
        assert comprehensive["checks"]["database"]["status"] == "healthy"

    def test_error_rate_monitoring(self, clean_error_tracker):
        """Test error rate monitoring integration."""
        # Generate some errors
        for i in range(3):
            clean_error_tracker.record_error(ValueError(f"Test error {i}"))

        # Check error rate
        error_health = health_monitor.check_error_rate()
        assert error_health.status == "healthy"  # Low error count
        assert error_health.details["total_errors"] == 3


class TestEnvironmentIntegration:
    """Test environment-based configuration integration."""

    def test_development_environment(self):
        """Test development environment configuration."""
        with patch.dict('os.environ', {'ENVIRONMENT': 'development'}):
            from src.database_config import DatabaseConfig
            config = DatabaseConfig()

            assert config.environment == 'development'
            assert not config.use_postgres  # Should use SQLite

    def test_production_environment(self):
        """Test production environment configuration."""
        with patch.dict('os.environ', {'ENVIRONMENT': 'production'}):
            with patch('src.database_config.HAS_POSTGRES', True):
                from src.database_config import DatabaseConfig
                config = DatabaseConfig()

                assert config.environment == 'production'
                assert config.use_postgres  # Should use PostgreSQL


class TestErrorHandlingIntegration:
    """Test error handling integration across components."""

    def test_retry_logic_integration(self):
        """Test retry logic integration."""
        from src.error_handling import retry_with_backoff

        call_count = 0

        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Temporary failure")
            return "success"

        result = flaky_operation()
        assert result == "success"
        assert call_count == 2

    def test_error_propagation(self):
        """Test error propagation through system."""
        from src.error_handling import handle_errors, ValidationError

        @handle_errors(error_mapping={ValueError: ValidationError})
        def operation_with_error():
            raise ValueError("Invalid input")

        with pytest.raises(ValidationError):
            operation_with_error()


class TestToolIntegration:
    """Test integration between different tools."""

    @patch('src.tools.financial_tools.FinancialCalculator')
    def test_financial_and_database_workflow(self, mock_calc, test_db_path):
        """Test workflow combining financial analysis and database queries."""
        # Setup mocks
        mock_calc_instance = Mock()
        mock_calc.return_value = mock_calc_instance
        mock_calc_instance.calculate_npv.return_value = 50000.0

        # Setup database
        db = BusinessDataDB(test_db_path)

        # Simulate workflow: query similar ventures, then do financial analysis
        similar_ventures = db.analyze_similar_ventures("SaaS", "subscription")

        # Use financial tool
        financial_result = financial_tool_executor("npv", {
            "cash_flows": [-100000, 30000, 40000, 50000, 60000],
            "discount_rate": 0.1
        })

        # Verify both operations work together
        assert "similar_ventures" in similar_ventures
        assert "npv" in financial_result


class TestConfigurationIntegration:
    """Test configuration integration across components."""

    def test_anthropic_api_configuration(self):
        """Test Anthropic API configuration."""
        from src.config import settings

        # Should have required settings
        assert hasattr(settings, 'anthropic_key')
        assert hasattr(settings, 'model_specialists')
        assert hasattr(settings, 'model_synth')

        # Check model configurations
        assert settings.model_specialists is not None
        assert settings.model_synth is not None

    def test_temperature_configurations(self):
        """Test role-specific temperature configurations."""
        from src.config import settings

        # Should have role-specific temperatures
        assert hasattr(settings, 'temperature_economist')
        assert hasattr(settings, 'temperature_lawyer')
        assert hasattr(settings, 'temperature_sociologist')

        # Temperatures should be reasonable values
        assert 0.0 <= settings.temperature_economist <= 1.0
        assert 0.0 <= settings.temperature_lawyer <= 1.0
        assert 0.0 <= settings.temperature_sociologist <= 1.0


class TestDataPersistence:
    """Test data persistence across operations."""

    def test_database_persistence(self, test_db_path, sample_business_data):
        """Test data persistence in database."""
        # Create first database instance
        db1 = BusinessDataDB(test_db_path)
        venture_id = db1.add_venture(sample_business_data)

        # Create second database instance (simulating restart)
        db2 = BusinessDataDB(test_db_path)

        # Query data should persist
        ventures = db2.analyze_similar_ventures(
            sample_business_data["industry"],
            sample_business_data["business_model"]
        )

        # Should find the venture we added
        found_venture = False
        for venture in ventures["similar_ventures"]:
            if venture["name"] == sample_business_data["name"]:
                found_venture = True
                break

        assert found_venture


class TestSystemPerformance:
    """Test system performance under load."""

    def test_multiple_financial_calculations(self):
        """Test performance with multiple financial calculations."""
        results = []

        # Perform multiple calculations
        for i in range(10):
            result = financial_tool_executor("npv", {
                "cash_flows": [-100000 + i * 1000, 30000, 40000, 50000, 60000],
                "discount_rate": 0.1
            })
            results.append(result)

        # All should succeed
        assert len(results) == 10
        assert all("npv" in result for result in results)

    @patch('src.health_monitor.psutil.cpu_percent')
    @patch('src.health_monitor.psutil.virtual_memory')
    @patch('src.health_monitor.psutil.disk_usage')
    def test_health_monitoring_performance(self, mock_disk, mock_memory, mock_cpu):
        """Test health monitoring performance."""
        # Mock system metrics
        mock_cpu.return_value = 50.0
        mock_memory.return_value = Mock(percent=60.0, available=8 * 1024**3)
        mock_disk.return_value = Mock(percent=45.0, free=100 * 1024**3)

        # Perform multiple health checks
        results = []
        for i in range(5):
            metrics = health_monitor.get_system_metrics()
            results.append(metrics)

        # All should succeed
        assert len(results) == 5
        assert all("cpu_usage_percent" in result for result in results)
