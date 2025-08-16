"""
Focused tests for health_monitor.py to achieve 95%+ coverage.
"""

import time
from unittest.mock import Mock, patch

from src.health_monitor import HealthMonitor, HealthStatus, health_monitor


class TestHealthStatus:
    """Test HealthStatus dataclass."""

    def test_health_status_creation(self):
        """Test creating a HealthStatus with all fields."""
        status = HealthStatus(
            status="healthy",
            message="All systems operational",
            details={"cpu": 50, "memory": 60},
            timestamp="2024-01-01T00:00:00",
        )

        assert status.status == "healthy"
        assert status.message == "All systems operational"
        assert status.details["cpu"] == 50
        assert status.details["memory"] == 60
        assert status.timestamp == "2024-01-01T00:00:00"

    def test_health_status_different_statuses(self):
        """Test HealthStatus with different status values."""
        healthy = HealthStatus("healthy", "OK", {}, "2024-01-01")
        degraded = HealthStatus("degraded", "Warning", {}, "2024-01-01")
        unhealthy = HealthStatus("unhealthy", "Error", {}, "2024-01-01")

        assert healthy.status == "healthy"
        assert degraded.status == "degraded"
        assert unhealthy.status == "unhealthy"


class TestHealthMonitor:
    """Test HealthMonitor class."""

    def test_initialization(self):
        """Test HealthMonitor initialization."""
        monitor = HealthMonitor()

        assert monitor.start_time is not None
        assert isinstance(monitor.start_time, float)
        assert monitor.health_checks == []
        assert monitor.start_time <= time.time()

    @patch("src.health_monitor.psutil")
    def test_get_system_metrics_success(self, mock_psutil):
        """Test successful system metrics retrieval."""
        # Setup mocks
        mock_psutil.cpu_percent.return_value = 45.5

        mock_memory = Mock()
        mock_memory.percent = 60.0
        mock_memory.available = 8 * 1024**3  # 8 GB
        mock_psutil.virtual_memory.return_value = mock_memory

        mock_disk = Mock()
        mock_disk.percent = 75.0
        mock_disk.free = 100 * 1024**3  # 100 GB
        mock_psutil.disk_usage.return_value = mock_disk

        monitor = HealthMonitor()
        original_start_time = monitor.start_time
        monitor.start_time = time.time() - 100  # Set 100 seconds ago

        metrics = monitor.get_system_metrics()

        assert metrics["cpu_usage_percent"] == 45.5
        assert metrics["memory_usage_percent"] == 60.0
        assert metrics["memory_available_gb"] == 8.0
        assert metrics["disk_usage_percent"] == 75.0
        assert metrics["disk_free_gb"] == 100.0
        assert metrics["uptime_seconds"] >= 100

        mock_psutil.cpu_percent.assert_called_once_with(interval=1)
        mock_psutil.virtual_memory.assert_called_once()
        mock_psutil.disk_usage.assert_called_once_with("/")

    @patch("src.health_monitor.psutil")
    @patch("src.health_monitor.logger")
    def test_get_system_metrics_exception(self, mock_logger, mock_psutil):
        """Test system metrics retrieval with exception."""
        mock_psutil.cpu_percent.side_effect = Exception("CPU error")

        monitor = HealthMonitor()
        metrics = monitor.get_system_metrics()

        assert "error" in metrics
        assert metrics["error"] == "CPU error"
        mock_logger.error.assert_called_once()

    @patch("src.health_monitor.db_config")
    def test_check_database_health_success_postgres(self, mock_db_config):
        """Test successful database health check with PostgreSQL."""
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)

        mock_db_config.get_connection.return_value = mock_conn
        mock_db_config.use_postgres = True

        monitor = HealthMonitor()
        status = monitor.check_database_health()

        assert isinstance(status, HealthStatus)
        assert status.status == "healthy"
        assert status.message == "Database connection successful"
        assert status.details["database_type"] == "PostgreSQL"
        assert status.details["response_time_ms"] == "< 100"

        mock_cursor.execute.assert_called_once_with("SELECT 1")
        mock_cursor.fetchone.assert_called_once()

    @patch("src.health_monitor.db_config")
    def test_check_database_health_success_sqlite(self, mock_db_config):
        """Test successful database health check with SQLite."""
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)

        mock_db_config.get_connection.return_value = mock_conn
        mock_db_config.use_postgres = False

        monitor = HealthMonitor()
        status = monitor.check_database_health()

        assert status.status == "healthy"
        assert status.details["database_type"] == "SQLite"

    @patch("src.health_monitor.db_config")
    def test_check_database_health_no_result(self, mock_db_config):
        """Test database health check with no result."""
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)

        mock_db_config.get_connection.return_value = mock_conn
        mock_db_config.use_postgres = False

        monitor = HealthMonitor()
        status = monitor.check_database_health()

        assert status.status == "unhealthy"
        assert status.message == "Database query returned no result"

    @patch("src.health_monitor.db_config")
    @patch("src.health_monitor.logger")
    def test_check_database_health_exception(self, mock_logger, mock_db_config):
        """Test database health check with exception."""
        mock_db_config.get_connection.side_effect = Exception("Connection failed")

        monitor = HealthMonitor()
        status = monitor.check_database_health()

        assert status.status == "unhealthy"
        assert "Database connection failed" in status.message
        assert status.details["error"] == "Connection failed"
        mock_logger.error.assert_called_once()

    @patch("src.health_monitor.error_tracker")
    def test_check_error_rate_no_errors(self, mock_error_tracker):
        """Test error rate check with no errors."""
        mock_error_tracker.get_error_summary.return_value = {
            "total_errors": 0,
            "errors_by_type": {},
        }

        monitor = HealthMonitor()
        status = monitor.check_error_rate(hours=1)

        assert status.status == "healthy"
        assert status.message == "No errors in the last hour"
        assert status.details["total_errors"] == 0

    @patch("src.health_monitor.error_tracker")
    def test_check_error_rate_low_errors(self, mock_error_tracker):
        """Test error rate check with low errors."""
        mock_error_tracker.get_error_summary.return_value = {
            "total_errors": 3,
            "errors_by_type": {"ValueError": 2, "TypeError": 1},
        }

        monitor = HealthMonitor()
        status = monitor.check_error_rate(hours=2)

        assert status.status == "healthy"
        assert "Low error rate: 3 errors in 2 hour(s)" in status.message

    @patch("src.health_monitor.error_tracker")
    def test_check_error_rate_moderate_errors(self, mock_error_tracker):
        """Test error rate check with moderate errors."""
        mock_error_tracker.get_error_summary.return_value = {
            "total_errors": 15,
            "errors_by_type": {"APIError": 10, "DBError": 5},
        }

        monitor = HealthMonitor()
        status = monitor.check_error_rate(hours=1)

        assert status.status == "degraded"
        assert "Moderate error rate: 15 errors in 1 hour(s)" in status.message

    @patch("src.health_monitor.error_tracker")
    def test_check_error_rate_high_errors(self, mock_error_tracker):
        """Test error rate check with high errors."""
        mock_error_tracker.get_error_summary.return_value = {
            "total_errors": 50,
            "errors_by_type": {"CriticalError": 50},
        }

        monitor = HealthMonitor()
        status = monitor.check_error_rate(hours=1)

        assert status.status == "unhealthy"
        assert "High error rate: 50 errors in 1 hour(s)" in status.message

    @patch("src.health_monitor.error_tracker")
    @patch("src.health_monitor.logger")
    def test_check_error_rate_exception(self, mock_logger, mock_error_tracker):
        """Test error rate check with exception."""
        mock_error_tracker.get_error_summary.side_effect = Exception("Tracker error")

        monitor = HealthMonitor()
        status = monitor.check_error_rate()

        assert status.status == "degraded"
        assert "Could not check error rates" in status.message
        assert status.details["error"] == "Tracker error"
        mock_logger.error.assert_called_once()

    def test_check_system_resources_healthy(self):
        """Test system resource check with healthy metrics."""
        monitor = HealthMonitor()

        # Mock get_system_metrics to return healthy values
        monitor.get_system_metrics = Mock(
            return_value={
                "cpu_usage_percent": 50,
                "memory_usage_percent": 60,
                "disk_usage_percent": 70,
                "memory_available_gb": 8.0,
                "disk_free_gb": 100.0,
                "uptime_seconds": 3600,
            }
        )

        status = monitor.check_system_resources()

        assert status.status == "healthy"
        assert status.message == "System resources within normal limits"
        assert status.details["cpu_usage_percent"] == 50

    def test_check_system_resources_high_cpu(self):
        """Test system resource check with high CPU usage."""
        monitor = HealthMonitor()

        monitor.get_system_metrics = Mock(
            return_value={
                "cpu_usage_percent": 85,
                "memory_usage_percent": 60,
                "disk_usage_percent": 70,
                "memory_available_gb": 8.0,
                "disk_free_gb": 100.0,
                "uptime_seconds": 3600,
            }
        )

        status = monitor.check_system_resources()

        assert status.status == "degraded"
        assert "High CPU usage: 85%" in status.message

    def test_check_system_resources_high_memory(self):
        """Test system resource check with high memory usage."""
        monitor = HealthMonitor()

        monitor.get_system_metrics = Mock(
            return_value={
                "cpu_usage_percent": 50,
                "memory_usage_percent": 90,
                "disk_usage_percent": 70,
                "memory_available_gb": 1.0,
                "disk_free_gb": 100.0,
                "uptime_seconds": 3600,
            }
        )

        status = monitor.check_system_resources()

        assert status.status == "degraded"
        assert "High memory usage: 90%" in status.message

    def test_check_system_resources_high_disk(self):
        """Test system resource check with high disk usage."""
        monitor = HealthMonitor()

        monitor.get_system_metrics = Mock(
            return_value={
                "cpu_usage_percent": 50,
                "memory_usage_percent": 60,
                "disk_usage_percent": 95,
                "memory_available_gb": 8.0,
                "disk_free_gb": 5.0,
                "uptime_seconds": 3600,
            }
        )

        status = monitor.check_system_resources()

        assert status.status == "degraded"
        assert "High disk usage: 95%" in status.message

    def test_check_system_resources_multiple_issues(self):
        """Test system resource check with multiple issues."""
        monitor = HealthMonitor()

        monitor.get_system_metrics = Mock(
            return_value={
                "cpu_usage_percent": 85,
                "memory_usage_percent": 90,
                "disk_usage_percent": 95,
                "memory_available_gb": 1.0,
                "disk_free_gb": 5.0,
                "uptime_seconds": 3600,
            }
        )

        status = monitor.check_system_resources()

        assert status.status == "unhealthy"
        assert "High CPU usage" in status.message
        assert "High memory usage" in status.message
        assert "High disk usage" in status.message

    def test_check_system_resources_metrics_error(self):
        """Test system resource check when metrics have error."""
        monitor = HealthMonitor()

        monitor.get_system_metrics = Mock(return_value={"error": "Failed to get metrics"})

        status = monitor.check_system_resources()

        assert status.status == "degraded"
        assert status.message == "Could not retrieve system metrics"
        assert status.details["error"] == "Failed to get metrics"

    @patch("src.health_monitor.logger")
    def test_check_system_resources_exception(self, mock_logger):
        """Test system resource check with exception."""
        monitor = HealthMonitor()

        monitor.get_system_metrics = Mock(side_effect=Exception("Metrics error"))

        status = monitor.check_system_resources()

        assert status.status == "unhealthy"
        assert "System resource check failed" in status.message
        assert status.details["error"] == "Metrics error"
        mock_logger.error.assert_called_once()

    def test_get_comprehensive_health_all_healthy(self):
        """Test comprehensive health check with all systems healthy."""
        monitor = HealthMonitor()

        # Mock all check methods
        monitor.check_database_health = Mock(
            return_value=HealthStatus("healthy", "DB OK", {}, "2024-01-01")
        )
        monitor.check_error_rate = Mock(
            return_value=HealthStatus("healthy", "No errors", {}, "2024-01-01")
        )
        monitor.check_system_resources = Mock(
            return_value=HealthStatus("healthy", "Resources OK", {}, "2024-01-01")
        )
        monitor.get_system_metrics = Mock(return_value={"cpu_usage_percent": 50})

        result = monitor.get_comprehensive_health()

        assert result["overall_status"] == "healthy"
        assert "timestamp" in result
        assert "uptime_seconds" in result
        assert "checks" in result
        assert "system_metrics" in result

        assert result["checks"]["database"]["status"] == "healthy"
        assert result["checks"]["errors"]["status"] == "healthy"
        assert result["checks"]["resources"]["status"] == "healthy"

    def test_get_comprehensive_health_degraded(self):
        """Test comprehensive health check with degraded status."""
        monitor = HealthMonitor()

        monitor.check_database_health = Mock(
            return_value=HealthStatus("healthy", "DB OK", {}, "2024-01-01")
        )
        monitor.check_error_rate = Mock(
            return_value=HealthStatus("degraded", "Some errors", {"total_errors": 10}, "2024-01-01")
        )
        monitor.check_system_resources = Mock(
            return_value=HealthStatus("healthy", "Resources OK", {}, "2024-01-01")
        )
        monitor.get_system_metrics = Mock(return_value={})

        result = monitor.get_comprehensive_health()

        assert result["overall_status"] == "degraded"
        assert result["checks"]["errors"]["status"] == "degraded"

    def test_get_comprehensive_health_unhealthy(self):
        """Test comprehensive health check with unhealthy status."""
        monitor = HealthMonitor()

        monitor.check_database_health = Mock(
            return_value=HealthStatus(
                "unhealthy", "DB Error", {"error": "Connection failed"}, "2024-01-01"
            )
        )
        monitor.check_error_rate = Mock(
            return_value=HealthStatus("degraded", "Some errors", {}, "2024-01-01")
        )
        monitor.check_system_resources = Mock(
            return_value=HealthStatus("healthy", "Resources OK", {}, "2024-01-01")
        )
        monitor.get_system_metrics = Mock(return_value={})

        result = monitor.get_comprehensive_health()

        assert result["overall_status"] == "unhealthy"
        assert result["checks"]["database"]["status"] == "unhealthy"

    def test_get_comprehensive_health_all_unhealthy(self):
        """Test comprehensive health check with all systems unhealthy."""
        monitor = HealthMonitor()

        monitor.check_database_health = Mock(
            return_value=HealthStatus("unhealthy", "DB Error", {}, "2024-01-01")
        )
        monitor.check_error_rate = Mock(
            return_value=HealthStatus("unhealthy", "High errors", {}, "2024-01-01")
        )
        monitor.check_system_resources = Mock(
            return_value=HealthStatus("unhealthy", "Resources critical", {}, "2024-01-01")
        )
        monitor.get_system_metrics = Mock(return_value={})

        result = monitor.get_comprehensive_health()

        assert result["overall_status"] == "unhealthy"
        assert all(
            result["checks"][check]["status"] == "unhealthy"
            for check in ["database", "errors", "resources"]
        )

    @patch("src.health_monitor.db_config")
    def test_get_simple_health_success(self, mock_db_config):
        """Test simple health check success."""
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)

        mock_db_config.get_connection.return_value = mock_conn

        monitor = HealthMonitor()
        result = monitor.get_simple_health()

        assert result["status"] == "healthy"
        assert "timestamp" in result

        mock_cursor.execute.assert_called_once_with("SELECT 1")
        mock_cursor.fetchone.assert_called_once()

    @patch("src.health_monitor.db_config")
    @patch("src.health_monitor.logger")
    def test_get_simple_health_failure(self, mock_logger, mock_db_config):
        """Test simple health check failure."""
        mock_db_config.get_connection.side_effect = Exception("DB Error")

        monitor = HealthMonitor()
        result = monitor.get_simple_health()

        assert result["status"] == "unhealthy"
        assert result["error"] == "DB Error"
        assert "timestamp" in result
        mock_logger.error.assert_called_once()


class TestGlobalHealthMonitor:
    """Test global health monitor instance."""

    def test_global_health_monitor_exists(self):
        """Test that global health_monitor instance exists."""
        assert health_monitor is not None
        assert isinstance(health_monitor, HealthMonitor)
        assert hasattr(health_monitor, "start_time")
        assert hasattr(health_monitor, "health_checks")


class TestIntegration:
    """Test integration scenarios."""

    @patch("src.health_monitor.psutil")
    @patch("src.health_monitor.db_config")
    @patch("src.health_monitor.error_tracker")
    def test_full_health_check_workflow(self, mock_error_tracker, mock_db_config, mock_psutil):
        """Test complete health check workflow."""
        # Setup psutil mocks
        mock_psutil.cpu_percent.return_value = 45.0
        mock_memory = Mock(percent=60.0, available=8 * 1024**3)
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_disk = Mock(percent=70.0, free=100 * 1024**3)
        mock_psutil.disk_usage.return_value = mock_disk

        # Setup database mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db_config.get_connection.return_value = mock_conn
        mock_db_config.use_postgres = False

        # Setup error tracker mocks
        mock_error_tracker.get_error_summary.return_value = {
            "total_errors": 2,
            "errors_by_type": {"ValueError": 2},
        }

        monitor = HealthMonitor()

        # Test individual checks
        db_status = monitor.check_database_health()
        assert db_status.status == "healthy"

        error_status = monitor.check_error_rate()
        assert error_status.status == "healthy"

        resource_status = monitor.check_system_resources()
        assert resource_status.status == "healthy"

        # Test comprehensive health
        full_health = monitor.get_comprehensive_health()
        assert full_health["overall_status"] == "healthy"
        assert len(full_health["checks"]) == 3

        # Test simple health
        simple_health = monitor.get_simple_health()
        assert simple_health["status"] == "healthy"

    def test_uptime_calculation(self):
        """Test uptime calculation accuracy."""
        monitor = HealthMonitor()
        original_start = monitor.start_time

        # Set start time to 60 seconds ago
        monitor.start_time = time.time() - 60

        metrics = monitor.get_system_metrics()
        assert metrics["uptime_seconds"] >= 60
        assert metrics["uptime_seconds"] < 65  # Allow some variance

        comprehensive = monitor.get_comprehensive_health()
        assert comprehensive["uptime_seconds"] >= 60
        assert comprehensive["uptime_seconds"] < 65

    @patch("src.health_monitor.datetime")
    def test_timestamp_formatting(self, mock_datetime):
        """Test that timestamps are properly formatted."""
        mock_now = Mock()
        mock_now.isoformat.return_value = "2024-01-01T12:00:00"
        mock_datetime.utcnow.return_value = mock_now

        status = HealthStatus(
            status="healthy",
            message="Test",
            details={},
            timestamp=mock_datetime.utcnow().isoformat(),
        )

        assert status.timestamp == "2024-01-01T12:00:00"

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        monitor = HealthMonitor()

        # Test with exactly threshold values
        monitor.get_system_metrics = Mock(
            return_value={
                "cpu_usage_percent": 80.0,  # Exactly at threshold
                "memory_usage_percent": 85.0,  # Exactly at threshold
                "disk_usage_percent": 90.0,  # Exactly at threshold
                "memory_available_gb": 1.0,
                "disk_free_gb": 10.0,
                "uptime_seconds": 0,
            }
        )

        status = monitor.check_system_resources()
        # Should not trigger high usage warnings at exact thresholds
        assert status.status == "healthy"

        # Test with just over thresholds
        monitor.get_system_metrics = Mock(
            return_value={
                "cpu_usage_percent": 80.1,
                "memory_usage_percent": 85.1,
                "disk_usage_percent": 90.1,
                "memory_available_gb": 1.0,
                "disk_free_gb": 10.0,
                "uptime_seconds": 0,
            }
        )

        status = monitor.check_system_resources()
        assert status.status == "unhealthy"  # Multiple issues
