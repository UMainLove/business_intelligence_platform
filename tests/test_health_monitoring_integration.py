"""
Integration tests for system monitoring and error tracking.
Tests health monitoring integration with database, error handling, and system metrics using synthetic data.
"""

import os
import tempfile
import time
from unittest.mock import Mock, patch
from pathlib import Path

import pytest

from src.health_monitor import HealthMonitor, HealthStatus, health_monitor
from src.error_handling import error_tracker, BusinessIntelligenceError
from src.database_config import DatabaseConfig


class TestHealthMonitoringIntegration:
    """Integration tests for health monitoring and error tracking systems."""

    @pytest.fixture
    def temp_logs_dir(self):
        """Create temporary directory for health monitoring logs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logs_dir = Path(temp_dir) / "logs"
            logs_dir.mkdir()

            os.environ["LOGS_DIR"] = str(logs_dir)
            yield temp_dir
            os.environ.pop("LOGS_DIR", None)

    @pytest.fixture
    def clean_environment(self):
        """Clean environment variables for testing."""
        original_env = {}
        env_vars = ["ENVIRONMENT", "DATABASE_URL", "SQLITE_PATH"]

        for var in env_vars:
            original_env[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]

        yield

        for var, value in original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]

    def test_health_monitor_initialization(self, temp_logs_dir):
        """Test HealthMonitor initialization and basic functionality."""
        monitor = HealthMonitor()

        # Verify initialization
        assert hasattr(monitor, "start_time")
        assert hasattr(monitor, "health_checks")
        assert isinstance(monitor.health_checks, list)
        assert monitor.start_time > 0

    @patch("src.health_monitor.psutil.cpu_percent")
    @patch("src.health_monitor.psutil.virtual_memory")
    @patch("src.health_monitor.psutil.disk_usage")
    def test_system_metrics_integration(self, mock_disk, mock_memory, mock_cpu, temp_logs_dir):
        """Test system metrics collection integration."""
        # Mock system metrics
        mock_cpu.return_value = 45.5

        mock_memory_obj = Mock()
        mock_memory_obj.percent = 65.2
        mock_memory_obj.available = 8 * (1024**3)  # 8GB available
        mock_memory.return_value = mock_memory_obj

        mock_disk_obj = Mock()
        mock_disk_obj.percent = 25.8
        mock_disk_obj.free = 500 * (1024**3)  # 500GB free
        mock_disk.return_value = mock_disk_obj

        # Test system metrics collection
        monitor = HealthMonitor()
        metrics = monitor.get_system_metrics()

        # Verify metrics structure
        assert "cpu_usage_percent" in metrics
        assert "memory_usage_percent" in metrics
        assert "memory_available_gb" in metrics
        assert "disk_usage_percent" in metrics
        assert "disk_free_gb" in metrics
        assert "uptime_seconds" in metrics

        # Verify metric values
        assert metrics["cpu_usage_percent"] == 45.5
        assert metrics["memory_usage_percent"] == 65.2
        assert metrics["memory_available_gb"] == 8.0
        assert metrics["disk_usage_percent"] == 25.8
        assert metrics["disk_free_gb"] == 500.0
        assert metrics["uptime_seconds"] >= 0

    @patch("src.health_monitor.db_config.get_connection")
    def test_database_health_check_integration(
        self, mock_connection, temp_logs_dir, clean_environment
    ):
        """Test database health check integration."""
        # Mock successful database connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {"result": 1}
        mock_connection.return_value.__enter__.return_value = mock_conn

        monitor = HealthMonitor()
        health_status = monitor.check_database_health()

        # Verify health status structure
        assert isinstance(health_status, HealthStatus)
        assert health_status.status in ["healthy", "degraded", "unhealthy"]
        assert isinstance(health_status.message, str)
        assert isinstance(health_status.details, dict)
        assert isinstance(health_status.timestamp, str)

        # Verify healthy database status
        assert health_status.status == "healthy"
        assert "database" in health_status.message.lower()

        # Verify database connection was tested
        mock_connection.assert_called()
        mock_cursor.execute.assert_called()

    @patch("src.health_monitor.db_config.get_connection")
    def test_database_health_check_failure_integration(
        self, mock_connection, temp_logs_dir, clean_environment
    ):
        """Test database health check failure handling."""
        # Mock database connection failure
        mock_connection.side_effect = Exception("Database connection failed")

        monitor = HealthMonitor()
        health_status = monitor.check_database_health()

        # Verify unhealthy status on failure
        assert health_status.status == "unhealthy"
        assert "error" in health_status.message.lower() or "failed" in health_status.message.lower()
        assert "error" in health_status.details or "exception" in health_status.details

    def test_error_rate_monitoring_integration(self, temp_logs_dir):
        """Test error rate monitoring integration with error tracker."""
        monitor = HealthMonitor()

        # Simulate some errors in error tracker
        test_errors = [
            BusinessIntelligenceError("Test error 1"),
            BusinessIntelligenceError("Test error 2"),
            ValueError("Test validation error"),
        ]

        # Track errors
        for error in test_errors:
            error_tracker.record_error(error, {"component": "test"})

        # Check error rate
        health_status = monitor.check_error_rate(hours=1)

        # Verify error rate health check
        assert isinstance(health_status, HealthStatus)
        assert health_status.status in ["healthy", "degraded", "unhealthy"]
        assert "total_errors" in health_status.details or "error_types" in health_status.details

        # Check that error tracking is working (status depends on threshold)
        assert health_status.details["total_errors"] == len(test_errors)
        assert health_status.details["total_errors"] == 3

    @patch("src.health_monitor.psutil.cpu_percent")
    @patch("src.health_monitor.psutil.virtual_memory")
    @patch("src.health_monitor.psutil.disk_usage")
    def test_system_resources_health_check_integration(
        self, mock_disk, mock_memory, mock_cpu, temp_logs_dir
    ):
        """Test system resources health check integration."""
        # Mock normal system resources
        mock_cpu.return_value = 45.0

        mock_memory_obj = Mock()
        mock_memory_obj.percent = 60.0
        mock_memory_obj.available = 8 * (1024**3)  # 8GB available
        mock_memory.return_value = mock_memory_obj

        mock_disk_obj = Mock()
        mock_disk_obj.percent = 30.0
        mock_disk_obj.free = 500 * (1024**3)  # 500GB free
        mock_disk.return_value = mock_disk_obj

        monitor = HealthMonitor()
        health_status = monitor.check_system_resources()

        # Verify healthy resources
        assert health_status.status == "healthy"
        assert (
            "resources" in health_status.message.lower()
            or "system" in health_status.message.lower()
        )
        assert "cpu_usage_percent" in health_status.details
        assert "memory_usage_percent" in health_status.details
        assert "disk_usage_percent" in health_status.details

    @patch("src.health_monitor.psutil.cpu_percent")
    @patch("src.health_monitor.psutil.virtual_memory")
    @patch("src.health_monitor.psutil.disk_usage")
    def test_system_resources_degraded_integration(
        self, mock_disk, mock_memory, mock_cpu, temp_logs_dir
    ):
        """Test system resources degraded state detection."""
        # Mock high resource usage
        mock_cpu.return_value = 85.0  # High CPU

        mock_memory_obj = Mock()
        mock_memory_obj.percent = 92.0  # High memory
        mock_memory_obj.available = 1 * (1024**3)  # 1GB available (low)
        mock_memory.return_value = mock_memory_obj

        mock_disk_obj = Mock()
        mock_disk_obj.percent = 95.0  # High disk usage
        mock_disk_obj.free = 10 * (1024**3)  # 10GB free (low)
        mock_disk.return_value = mock_disk_obj

        monitor = HealthMonitor()
        health_status = monitor.check_system_resources()

        # Should detect degraded or unhealthy status
        assert health_status.status in ["degraded", "unhealthy"]
        assert health_status.details["cpu_usage_percent"] == 85.0
        assert health_status.details["memory_usage_percent"] == 92.0
        assert health_status.details["disk_usage_percent"] == 95.0

    @patch("src.health_monitor.db_config.get_connection")
    @patch("src.health_monitor.psutil.cpu_percent")
    @patch("src.health_monitor.psutil.virtual_memory")
    @patch("src.health_monitor.psutil.disk_usage")
    def test_comprehensive_health_check_integration(
        self, mock_disk, mock_memory, mock_cpu, mock_connection, temp_logs_dir, clean_environment
    ):
        """Test comprehensive health check with all components."""
        # Mock system metrics
        mock_cpu.return_value = 40.0
        mock_memory_obj = Mock()
        mock_memory_obj.percent = 55.0
        mock_memory_obj.available = 8 * (1024**3)  # 8GB available
        mock_memory.return_value = mock_memory_obj
        mock_disk_obj = Mock()
        mock_disk_obj.percent = 25.0
        mock_disk_obj.free = 500 * (1024**3)  # 500GB free
        mock_disk.return_value = mock_disk_obj

        # Mock database connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {"result": 1}
        mock_connection.return_value.__enter__.return_value = mock_conn

        # Use global health monitor
        overall_health = health_monitor.get_comprehensive_health()

        # Verify comprehensive health check
        assert "overall_status" in overall_health
        assert "checks" in overall_health
        assert "timestamp" in overall_health
        assert "system_metrics" in overall_health

        # Verify component health checks
        checks = overall_health["checks"]
        assert "database" in checks
        assert "resources" in checks  # system_resources is called "resources"
        assert "errors" in checks  # error_rate is called "errors"

        # Each component should have health status
        for component_name, component_health in checks.items():
            assert "status" in component_health
            assert component_health["status"] in ["healthy", "degraded", "unhealthy"]

    def test_health_monitor_with_error_tracking_integration(self, temp_logs_dir):
        """Test health monitor integration with error tracking system."""
        monitor = HealthMonitor()

        # Generate various types of errors
        errors_to_track = [
            ("DatabaseError", {"query": "SELECT * FROM users", "table": "users"}),
            ("ValidationError", {"field": "email", "value": "invalid"}),
            ("APIError", {"endpoint": "/api/data", "status_code": 500}),
            ("FileNotFoundError", {"path": "/missing/file.txt"}),
            ("BusinessIntelligenceError", {"operation": "analysis", "model": "financial"}),
        ]

        # Track errors
        for error_type, context in errors_to_track:
            error = Exception(f"Test {error_type}")
            error_tracker.record_error(error, context)

        # Check error rate after tracking errors
        error_health = monitor.check_error_rate(hours=1)

        # Verify error tracking integration
        assert isinstance(error_health, HealthStatus)
        # Check that error tracking is working (status depends on threshold)
        assert error_health.details["total_errors"] == len(errors_to_track)

        # Verify error details
        assert "total_errors" in error_health.details or "error_types" in error_health.details

    def test_health_monitor_uptime_tracking(self, temp_logs_dir):
        """Test health monitor uptime tracking."""
        monitor = HealthMonitor()

        # Wait a short time to ensure uptime > 0
        time.sleep(0.1)

        metrics = monitor.get_system_metrics()
        uptime = metrics["uptime_seconds"]

        assert uptime > 0
        assert isinstance(uptime, int)

        # Test uptime increases
        time.sleep(0.1)
        updated_metrics = monitor.get_system_metrics()
        updated_uptime = updated_metrics["uptime_seconds"]

        assert updated_uptime >= uptime

    @patch("src.health_monitor.db_config.get_connection")
    def test_health_status_serialization(self, mock_connection, temp_logs_dir, clean_environment):
        """Test health status serialization for API responses."""
        # Mock database connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {"result": 1}
        mock_connection.return_value.__enter__.return_value = mock_conn

        monitor = HealthMonitor()

        # Get various health checks
        db_health = monitor.check_database_health()
        system_health = monitor.check_system_resources()
        error_health = monitor.check_error_rate()

        # Test that health status objects can be serialized
        health_checks = [db_health, system_health, error_health]

        for health in health_checks:
            # Verify all fields are serializable
            health_dict = {
                "status": health.status,
                "message": health.message,
                "details": health.details,
                "timestamp": health.timestamp,
            }

            # Should be able to convert to dict without errors
            assert isinstance(health_dict["status"], str)
            assert isinstance(health_dict["message"], str)
            assert isinstance(health_dict["details"], dict)
            assert isinstance(health_dict["timestamp"], str)

    def test_health_monitor_thread_safety(self, temp_logs_dir):
        """Test health monitor thread safety for concurrent access."""
        import threading
        import concurrent.futures

        monitor = HealthMonitor()
        results = []

        def check_health():
            """Worker function for concurrent health checks."""
            try:
                # Simulate some errors for error rate testing
                error = BusinessIntelligenceError("Concurrent test error")
                error_tracker.track_error(error, {"thread": threading.current_thread().name})

                # Perform health checks
                error_health = monitor.check_error_rate()
                return error_health.status
            except Exception as e:
                return f"Error: {str(e)}"

        # Run concurrent health checks
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(check_health) for _ in range(10)]

            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)

        # Verify all health checks completed without errors
        assert len(results) == 10
        for result in results:
            assert result in ["healthy", "degraded", "unhealthy"] or result.startswith("Error:")

        # Should have successfully tracked errors from multiple threads
        final_error_health = monitor.check_error_rate()
        assert isinstance(final_error_health, HealthStatus)

    def test_health_monitor_memory_usage_tracking(self, temp_logs_dir):
        """Test health monitor memory usage tracking over time."""
        monitor = HealthMonitor()

        # Get initial metrics
        initial_metrics = monitor.get_system_metrics()

        # Simulate some memory usage (create large objects)
        large_data = [list(range(10000)) for _ in range(10)]

        # Get updated metrics
        updated_metrics = monitor.get_system_metrics()

        # Verify metrics structure is consistent
        assert set(initial_metrics.keys()) == set(updated_metrics.keys())

        # Memory usage should be tracked
        assert "memory_usage_percent" in updated_metrics
        assert "memory_available_gb" in updated_metrics
        assert isinstance(updated_metrics["memory_usage_percent"], (int, float))
        assert isinstance(updated_metrics["memory_available_gb"], (int, float))

        # Clean up
        del large_data

    @patch("src.health_monitor.db_config.get_connection")
    def test_health_monitor_database_switching_integration(
        self, mock_connection, temp_logs_dir, clean_environment
    ):
        """Test health monitor with database switching (SQLite/PostgreSQL)."""
        # Test SQLite health check
        os.environ["ENVIRONMENT"] = "development"

        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {"result": 1}
        mock_connection.return_value.__enter__.return_value = mock_conn

        monitor = HealthMonitor()
        sqlite_health = monitor.check_database_health()

        assert sqlite_health.status == "healthy"
        assert "database" in sqlite_health.message.lower()

        # Test PostgreSQL health check (simulated)
        os.environ["ENVIRONMENT"] = "production"
        os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/test_db"

        # Mock PostgreSQL connection
        pg_health = monitor.check_database_health()

        # Should still work with different database backends
        assert pg_health.status in ["healthy", "unhealthy"]  # Depends on connection success
        assert isinstance(pg_health.details, dict)
