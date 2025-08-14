"""
Tests for health monitoring functionality.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
from src.health_monitor import HealthMonitor, HealthStatus, health_monitor
from src.error_handling import error_tracker


class TestHealthStatus:
    """Test HealthStatus dataclass."""

    def test_health_status_creation(self):
        """Test creating health status object."""
        status = HealthStatus(
            status="healthy",
            message="All systems operational",
            details={"uptime": 3600},
            timestamp="2024-01-01T00:00:00",
        )

        assert status.status == "healthy"
        assert status.message == "All systems operational"
        assert status.details == {"uptime": 3600}
        assert status.timestamp == "2024-01-01T00:00:00"


class TestHealthMonitor:
    """Test health monitoring functionality."""

    def test_initialization(self):
        """Test health monitor initialization."""
        monitor = HealthMonitor()

        assert monitor.start_time is not None
        assert monitor.health_checks == []

    @patch("psutil.cpu_percent")
    @patch("psutil.virtual_memory")
    @patch("psutil.disk_usage")
    def test_get_system_metrics(self, mock_disk, mock_memory, mock_cpu):
        """Test system metrics collection."""
        # Mock psutil functions
        mock_cpu.return_value = 25.5

        mock_memory_obj = Mock()
        mock_memory_obj.percent = 60.0
        mock_memory_obj.available = 8 * 1024**3  # 8GB
        mock_memory.return_value = mock_memory_obj

        mock_disk_obj = Mock()
        mock_disk_obj.percent = 45.0
        mock_disk_obj.free = 100 * 1024**3  # 100GB
        mock_disk.return_value = mock_disk_obj

        monitor = HealthMonitor()
        metrics = monitor.get_system_metrics()

        assert metrics["cpu_usage_percent"] == 25.5
        assert metrics["memory_usage_percent"] == 60.0
        assert metrics["memory_available_gb"] == 8.0
        assert metrics["disk_usage_percent"] == 45.0
        assert metrics["disk_free_gb"] == 100.0
        assert "uptime_seconds" in metrics

    @patch("psutil.cpu_percent")
    def test_get_system_metrics_error(self, mock_cpu):
        """Test system metrics collection with error."""
        mock_cpu.side_effect = Exception("psutil error")

        monitor = HealthMonitor()
        metrics = monitor.get_system_metrics()

        assert "error" in metrics
        assert "psutil error" in metrics["error"]

    @patch("src.health_monitor.db_config")
    def test_check_database_health_success(self, mock_db_config):
        """Test successful database health check."""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [1]

        mock_db_config.get_connection.return_value.__enter__.return_value = mock_conn
        mock_db_config.use_postgres = False

        monitor = HealthMonitor()
        status = monitor.check_database_health()

        assert status.status == "healthy"
        assert "Database connection successful" in status.message
        assert status.details["database_type"] == "SQLite"

    @patch("src.health_monitor.db_config")
    def test_check_database_health_failure(self, mock_db_config):
        """Test failed database health check."""
        mock_db_config.get_connection.side_effect = Exception("Connection failed")

        monitor = HealthMonitor()
        status = monitor.check_database_health()

        assert status.status == "unhealthy"
        assert "Database connection failed" in status.message
        assert "Connection failed" in status.details["error"]

    def test_check_error_rate_no_errors(self, clean_error_tracker):
        """Test error rate check with no errors."""
        monitor = HealthMonitor()
        status = monitor.check_error_rate()

        assert status.status == "healthy"
        assert "No errors" in status.message
        assert status.details["total_errors"] == 0

    def test_check_error_rate_low_errors(self, clean_error_tracker):
        """Test error rate check with low error count."""
        # Add a few errors
        for i in range(3):
            clean_error_tracker.record_error(ValueError(f"Error {i}"))

        monitor = HealthMonitor()
        status = monitor.check_error_rate()

        assert status.status == "healthy"
        assert "Low error rate" in status.message
        assert status.details["total_errors"] == 3

    def test_check_error_rate_high_errors(self, clean_error_tracker):
        """Test error rate check with high error count."""
        # Add many errors
        for i in range(25):
            clean_error_tracker.record_error(ValueError(f"Error {i}"))

        monitor = HealthMonitor()
        status = monitor.check_error_rate()

        assert status.status == "unhealthy"
        assert "High error rate" in status.message
        assert status.details["total_errors"] == 25

    @patch.object(HealthMonitor, "get_system_metrics")
    def test_check_system_resources_healthy(self, mock_metrics):
        """Test system resource check with healthy metrics."""
        mock_metrics.return_value = {
            "cpu_usage_percent": 50.0,
            "memory_usage_percent": 60.0,
            "disk_usage_percent": 70.0,
        }

        monitor = HealthMonitor()
        status = monitor.check_system_resources()

        assert status.status == "healthy"
        assert "within normal limits" in status.message

    @patch.object(HealthMonitor, "get_system_metrics")
    def test_check_system_resources_degraded(self, mock_metrics):
        """Test system resource check with degraded metrics."""
        mock_metrics.return_value = {
            "cpu_usage_percent": 85.0,  # High CPU
            "memory_usage_percent": 60.0,
            "disk_usage_percent": 70.0,
        }

        monitor = HealthMonitor()
        status = monitor.check_system_resources()

        assert status.status == "degraded"
        assert "High CPU usage" in status.message

    @patch.object(HealthMonitor, "get_system_metrics")
    def test_check_system_resources_unhealthy(self, mock_metrics):
        """Test system resource check with unhealthy metrics."""
        mock_metrics.return_value = {
            "cpu_usage_percent": 85.0,  # High CPU
            "memory_usage_percent": 90.0,  # High memory
            "disk_usage_percent": 95.0,  # High disk
        }

        monitor = HealthMonitor()
        status = monitor.check_system_resources()

        assert status.status == "unhealthy"
        assert "High CPU usage" in status.message
        assert "High memory usage" in status.message
        assert "High disk usage" in status.message

    @patch.object(HealthMonitor, "check_database_health")
    @patch.object(HealthMonitor, "check_error_rate")
    @patch.object(HealthMonitor, "check_system_resources")
    @patch.object(HealthMonitor, "get_system_metrics")
    def test_get_comprehensive_health_healthy(
        self, mock_metrics, mock_resources, mock_errors, mock_db
    ):
        """Test comprehensive health check with all systems healthy."""
        # Mock all checks as healthy
        mock_db.return_value = HealthStatus("healthy", "DB OK", {}, "2024-01-01")
        mock_errors.return_value = HealthStatus("healthy", "No errors", {}, "2024-01-01")
        mock_resources.return_value = HealthStatus("healthy", "Resources OK", {}, "2024-01-01")
        mock_metrics.return_value = {"cpu_usage_percent": 50}

        monitor = HealthMonitor()
        health = monitor.get_comprehensive_health()

        assert health["overall_status"] == "healthy"
        assert "checks" in health
        assert len(health["checks"]) == 3
        assert all(check["status"] == "healthy" for check in health["checks"].values())

    @patch.object(HealthMonitor, "check_database_health")
    @patch.object(HealthMonitor, "check_error_rate")
    @patch.object(HealthMonitor, "check_system_resources")
    @patch.object(HealthMonitor, "get_system_metrics")
    def test_get_comprehensive_health_degraded(
        self, mock_metrics, mock_resources, mock_errors, mock_db
    ):
        """Test comprehensive health check with degraded status."""
        mock_db.return_value = HealthStatus("healthy", "DB OK", {}, "2024-01-01")
        mock_errors.return_value = HealthStatus("degraded", "Some errors", {}, "2024-01-01")
        mock_resources.return_value = HealthStatus("healthy", "Resources OK", {}, "2024-01-01")
        mock_metrics.return_value = {"cpu_usage_percent": 50}

        monitor = HealthMonitor()
        health = monitor.get_comprehensive_health()

        assert health["overall_status"] == "degraded"

    @patch.object(HealthMonitor, "check_database_health")
    @patch.object(HealthMonitor, "check_error_rate")
    @patch.object(HealthMonitor, "check_system_resources")
    @patch.object(HealthMonitor, "get_system_metrics")
    def test_get_comprehensive_health_unhealthy(
        self, mock_metrics, mock_resources, mock_errors, mock_db
    ):
        """Test comprehensive health check with unhealthy status."""
        mock_db.return_value = HealthStatus("unhealthy", "DB Down", {}, "2024-01-01")
        mock_errors.return_value = HealthStatus("healthy", "No errors", {}, "2024-01-01")
        mock_resources.return_value = HealthStatus("healthy", "Resources OK", {}, "2024-01-01")
        mock_metrics.return_value = {"cpu_usage_percent": 50}

        monitor = HealthMonitor()
        health = monitor.get_comprehensive_health()

        assert health["overall_status"] == "unhealthy"

    @patch("src.health_monitor.db_config")
    def test_get_simple_health_success(self, mock_db_config):
        """Test simple health check success."""
        mock_conn = MagicMock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [1]

        mock_db_config.get_connection.return_value.__enter__.return_value = mock_conn

        monitor = HealthMonitor()
        health = monitor.get_simple_health()

        assert health["status"] == "healthy"
        assert "timestamp" in health

    @patch("src.health_monitor.db_config")
    def test_get_simple_health_failure(self, mock_db_config):
        """Test simple health check failure."""
        mock_db_config.get_connection.side_effect = Exception("DB error")

        monitor = HealthMonitor()
        health = monitor.get_simple_health()

        assert health["status"] == "unhealthy"
        assert "error" in health
        assert "DB error" in health["error"]


class TestGlobalHealthMonitor:
    """Test global health monitor instance."""

    def test_global_instance_exists(self):
        """Test that global health monitor instance exists."""
        assert health_monitor is not None
        assert isinstance(health_monitor, HealthMonitor)

    def test_global_instance_methods(self):
        """Test that global instance has required methods."""
        assert hasattr(health_monitor, "get_comprehensive_health")
        assert hasattr(health_monitor, "get_simple_health")
        assert hasattr(health_monitor, "check_database_health")
        assert hasattr(health_monitor, "check_error_rate")
        assert hasattr(health_monitor, "check_system_resources")
