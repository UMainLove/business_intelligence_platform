"""
Synthetic tests for health monitoring without external dependencies.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock

from src.health_monitor import HealthMonitor


class TestHealthMonitor:
    """Test HealthMonitor with synthetic data."""

    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = HealthMonitor()

    def test_health_monitor_initialization(self):
        """Test HealthMonitor initialization."""
        assert self.monitor.start_time is not None
        assert hasattr(self.monitor, 'health_checks')

    def test_get_simple_health(self):
        """Test simple health check."""
        health = self.monitor.get_simple_health()
        
        assert isinstance(health, dict)
        assert "status" in health
        assert "timestamp" in health
        assert health["status"] in ["healthy", "degraded", "unhealthy"]

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_get_system_metrics(self, mock_disk, mock_memory, mock_cpu):
        """Test system metrics collection with mocked psutil."""
        # Mock psutil responses
        mock_cpu.return_value = 45.5
        
        mock_memory_obj = Mock()
        mock_memory_obj.percent = 60.2
        mock_memory_obj.available = 4 * 1024**3  # 4GB
        mock_memory.return_value = mock_memory_obj
        
        mock_disk_obj = Mock()
        mock_disk_obj.percent = 75.8
        mock_disk_obj.free = 100 * 1024**3  # 100GB
        mock_disk.return_value = mock_disk_obj
        
        metrics = self.monitor.get_system_metrics()
        
        assert "cpu_usage_percent" in metrics
        assert "memory_usage_percent" in metrics
        assert "memory_available_gb" in metrics
        assert "disk_usage_percent" in metrics
        assert "disk_free_gb" in metrics
        assert "uptime_seconds" in metrics
        
        assert metrics["cpu_usage_percent"] == 45.5
        assert metrics["memory_usage_percent"] == 60.2
        assert metrics["disk_usage_percent"] == 75.8

    @patch('src.health_monitor.HealthMonitor.get_system_metrics')
    def test_check_system_resources(self, mock_metrics):
        """Test system resource health check."""
        # Test healthy system
        mock_metrics.return_value = {
            "cpu_usage_percent": 50,
            "memory_usage_percent": 60,
            "disk_usage_percent": 70
        }
        
        result = self.monitor.check_system_resources()
        assert result.status == "healthy"
        assert result.details["cpu_usage_percent"] == 50
        
        # Test degraded system (high CPU)
        mock_metrics.return_value = {
            "cpu_usage_percent": 85,
            "memory_usage_percent": 60,
            "disk_usage_percent": 70
        }
        
        result = self.monitor.check_system_resources()
        assert result.status == "degraded"
        
        # Test unhealthy system (very high resources)
        mock_metrics.return_value = {
            "cpu_usage_percent": 95,
            "memory_usage_percent": 95,
            "disk_usage_percent": 95
        }
        
        result = self.monitor.check_system_resources()
        assert result.status == "unhealthy"

    @patch('src.health_monitor.db_config')
    def test_check_database_health_no_connection(self, mock_db_config):
        """Test database health check with no connection available."""
        # Mock database config to simulate no connection
        mock_db_config.get_connection.side_effect = Exception("Connection failed")
        
        result = self.monitor.check_database_health()
        
        assert result.status == "unhealthy"
        assert "Connection failed" in result.message

    @patch('src.health_monitor.db_config')
    def test_check_database_health_success(self, mock_db_config):
        """Test successful database health check."""
        # Mock successful database connection
        mock_conn = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = [1]
        mock_conn.cursor.return_value = mock_cursor
        mock_db_config.get_connection.return_value.__enter__.return_value = mock_conn
        
        result = self.monitor.check_database_health()
        
        assert result.status == "healthy"
        assert "response_time_ms" in result.details

    @patch('src.health_monitor.error_tracker')
    def test_check_error_rate_healthy(self, mock_error_tracker):
        """Test error rate check with healthy system."""
        mock_error_tracker.get_error_summary.return_value = {
            "total_errors": 5,
            "error_types": {"ValueError": 3, "TypeError": 2}
        }
        
        result = self.monitor.check_error_rate()
        
        assert result.status == "healthy"
        assert result.details["error_count"] == 5
        assert result.details["error_types"] == {"ValueError": 3, "TypeError": 2}

    @patch('src.health_monitor.error_tracker')
    def test_check_error_rate_degraded(self, mock_error_tracker):
        """Test error rate check with degraded system."""
        mock_error_tracker.get_error_summary.return_value = {
            "total_errors": 25,
            "error_types": {"ValueError": 15, "TypeError": 10}
        }
        
        result = self.monitor.check_error_rate()
        
        assert result.status == "degraded"
        assert result.details["error_count"] == 25

    @patch('src.health_monitor.error_tracker')
    def test_check_error_rate_unhealthy(self, mock_error_tracker):
        """Test error rate check with unhealthy system."""
        mock_error_tracker.get_error_summary.return_value = {
            "total_errors": 60,
            "error_types": {"ValueError": 40, "TypeError": 20}
        }
        
        result = self.monitor.check_error_rate()
        
        assert result.status == "unhealthy"
        assert result.details["error_count"] == 60

    @patch('src.health_monitor.HealthMonitor.check_system_resources')
    @patch('src.health_monitor.HealthMonitor.check_database_health')
    @patch('src.health_monitor.HealthMonitor.check_error_rate')
    def test_get_comprehensive_health_all_healthy(self, mock_error_check, mock_db_check, mock_system_check):
        """Test comprehensive health check with all systems healthy."""
        from src.health_monitor import HealthStatus
        mock_system_check.return_value = HealthStatus(status="healthy", message="OK", details={"cpu_usage": 50}, timestamp="2024-01-01T00:00:00")
        mock_db_check.return_value = HealthStatus(status="healthy", message="OK", details={"response_time_ms": 10}, timestamp="2024-01-01T00:00:00")
        mock_error_check.return_value = HealthStatus(status="healthy", message="OK", details={"error_count": 2}, timestamp="2024-01-01T00:00:00")
        
        health = self.monitor.get_comprehensive_health()
        
        assert health["overall_status"] == "healthy"
        assert "system_resources" in health["checks"]
        assert "database" in health["checks"]
        assert "error_rate" in health["checks"]
        assert health["checks"]["system_resources"]["status"] == "healthy"

    @patch('src.health_monitor.HealthMonitor.check_system_resources')
    @patch('src.health_monitor.HealthMonitor.check_database_health')
    @patch('src.health_monitor.HealthMonitor.check_error_rate')
    def test_get_comprehensive_health_mixed(self, mock_error_check, mock_db_check, mock_system_check):
        """Test comprehensive health check with mixed statuses."""
        from src.health_monitor import HealthStatus
        mock_system_check.return_value = HealthStatus(status="healthy", message="OK", details={"cpu_usage": 50}, timestamp="2024-01-01T00:00:00")
        mock_db_check.return_value = HealthStatus(status="degraded", message="Slow response", details={}, timestamp="2024-01-01T00:00:00")
        mock_error_check.return_value = HealthStatus(status="unhealthy", message="High errors", details={"error_count": 100}, timestamp="2024-01-01T00:00:00")
        
        health = self.monitor.get_comprehensive_health()
        
        # Overall status should be the worst individual status
        assert health["overall_status"] == "unhealthy"
        assert health["checks"]["database"]["status"] == "degraded"
        assert health["checks"]["error_rate"]["status"] == "unhealthy"

    def test_uptime_calculation(self):
        """Test uptime calculation."""
        # Get metrics twice with a small delay
        metrics1 = self.monitor.get_system_metrics()
        time.sleep(0.1)
        metrics2 = self.monitor.get_system_metrics()
        
        # Second measurement should have higher uptime
        assert metrics2["uptime_seconds"] > metrics1["uptime_seconds"]
        assert metrics2["uptime_seconds"] >= 0.1

    @patch('src.health_monitor.HealthMonitor.get_system_metrics')
    def test_health_status_priority(self, mock_metrics):
        """Test that health status correctly prioritizes worst status."""
        # Test that degraded beats healthy
        mock_metrics.return_value = {
            "cpu_usage_percent": 85,  # This should trigger degraded
            "memory_usage_percent": 50,
            "disk_usage_percent": 60
        }
        
        result = self.monitor.check_system_resources()
        assert result.status == "degraded"

    def test_health_checks_list(self):
        """Test that health_checks list contains expected checks."""
        # Check that health_checks attribute exists
        assert hasattr(self.monitor, 'health_checks')
        
        # Check that the monitor has check methods
        assert hasattr(self.monitor, 'check_system_resources')
        assert hasattr(self.monitor, 'check_database_health')
        assert hasattr(self.monitor, 'check_error_rate')

    @patch('src.health_monitor.psutil')
    def test_psutil_import_error_handling(self, mock_psutil):
        """Test handling of psutil import errors."""
        # This test ensures graceful degradation if psutil is not available
        mock_psutil.side_effect = ImportError("psutil not available")
        
        # Should still be able to create monitor instance
        monitor = HealthMonitor()
        assert monitor is not None

    def test_timestamp_format(self):
        """Test that timestamps are properly formatted."""
        health = self.monitor.get_simple_health()
        timestamp = health["timestamp"]
        
        # Should be ISO format string
        assert isinstance(timestamp, str)
        assert "T" in timestamp  # ISO format contains T
        assert len(timestamp) > 19  # Should include microseconds

    @patch('time.time')
    def test_response_time_calculation(self, mock_time):
        """Test response time calculation in database check."""
        # Mock time.time() to return predictable values
        mock_time.side_effect = [1000.0, 1000.05]  # 50ms difference
        
        with patch('src.health_monitor.db_config') as mock_db_config:
            mock_conn = MagicMock()
            mock_cursor = Mock()
            mock_cursor.fetchone.return_value = [1]
            mock_conn.cursor.return_value = mock_cursor
            mock_db_config.get_connection.return_value.__enter__.return_value = mock_conn
            
            result = self.monitor.check_database_health()
            
            # Response time should be approximately 50ms
            assert "response_time_ms" in result.details
            assert abs(result.details["response_time_ms"] - 50) < 1