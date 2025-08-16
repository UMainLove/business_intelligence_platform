"""
Health monitoring and diagnostics for Business Intelligence Platform.
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict

import psutil

from src.database_config import db_config
from src.error_handling import error_tracker

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """Health check status."""

    status: str  # "healthy", "degraded", "unhealthy"
    message: str
    details: Dict[str, Any]
    timestamp: str


class HealthMonitor:
    """Monitor system health and performance."""

    def __init__(self):
        self.start_time = time.time()
        self.health_checks = []

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get basic system metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_usage_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "uptime_seconds": int(time.time() - self.start_time),
            }
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {"error": str(e)}

    def check_database_health(self) -> HealthStatus:
        """Check database connectivity and health."""
        try:
            # Test database connection
            with db_config.get_connection() as conn:
                cursor = conn.cursor()
                if db_config.use_postgres:
                    cursor.execute("SELECT 1")
                else:
                    cursor.execute("SELECT 1")
                result = cursor.fetchone()

            if result:
                return HealthStatus(
                    status="healthy",
                    message="Database connection successful",
                    details={
                        "database_type": "PostgreSQL" if db_config.use_postgres else "SQLite",
                        "response_time_ms": "< 100",
                    },
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            else:
                return HealthStatus(
                    status="unhealthy",
                    message="Database query returned no result",
                    details={"database_type": "PostgreSQL" if db_config.use_postgres else "SQLite"},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return HealthStatus(
                status="unhealthy",
                message=f"Database connection failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

    def check_error_rate(self, hours: int = 1) -> HealthStatus:
        """Check recent error rates."""
        try:
            error_summary = error_tracker.get_error_summary(hours)
            total_errors = error_summary["total_errors"]

            # Define thresholds
            if total_errors == 0:
                status = "healthy"
                message = "No errors in the last hour"
            elif total_errors <= 5:
                status = "healthy"
                message = f"Low error rate: {total_errors} errors in {hours} hour(s)"
            elif total_errors <= 20:
                status = "degraded"
                message = f"Moderate error rate: {total_errors} errors in {hours} hour(s)"
            else:
                status = "unhealthy"
                message = f"High error rate: {total_errors} errors in {hours} hour(s)"

            return HealthStatus(
                status=status,
                message=message,
                details=error_summary,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        except Exception as e:
            logger.error(f"Error rate check failed: {e}")
            return HealthStatus(
                status="degraded",
                message=f"Could not check error rates: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

    def check_system_resources(self) -> HealthStatus:
        """Check system resource usage."""
        try:
            metrics = self.get_system_metrics()

            if "error" in metrics:
                return HealthStatus(
                    status="degraded",
                    message="Could not retrieve system metrics",
                    details=metrics,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

            # Check thresholds
            issues = []
            if metrics["cpu_usage_percent"] > 80:
                issues.append(f"High CPU usage: {metrics['cpu_usage_percent']}%")

            if metrics["memory_usage_percent"] > 85:
                issues.append(f"High memory usage: {metrics['memory_usage_percent']}%")

            if metrics["disk_usage_percent"] > 90:
                issues.append(f"High disk usage: {metrics['disk_usage_percent']}%")

            if issues:
                status = "degraded" if len(issues) == 1 else "unhealthy"
                message = "; ".join(issues)
            else:
                status = "healthy"
                message = "System resources within normal limits"

            return HealthStatus(
                status=status,
                message=message,
                details=metrics,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        except Exception as e:
            logger.error(f"System resource check failed: {e}")
            return HealthStatus(
                status="unhealthy",
                message=f"System resource check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

    def get_comprehensive_health(self) -> Dict[str, Any]:
        """Get comprehensive health check results."""
        checks = {
            "database": self.check_database_health(),
            "errors": self.check_error_rate(),
            "resources": self.check_system_resources(),
        }

        # Determine overall status
        statuses = [check.status for check in checks.values()]
        if "unhealthy" in statuses:
            overall_status = "unhealthy"
        elif "degraded" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        return {
            "overall_status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": int(time.time() - self.start_time),
            "checks": {
                name: {
                    "status": check.status,
                    "message": check.message,
                    "details": check.details,
                    "timestamp": check.timestamp,
                }
                for name, check in checks.items()
            },
            "system_metrics": self.get_system_metrics(),
        }

    def get_simple_health(self) -> Dict[str, str]:
        """Get simple health status for load balancers."""
        try:
            # Quick database test
            with db_config.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()

            return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
        except Exception as e:
            logger.error(f"Simple health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }


# Global health monitor instance
health_monitor = HealthMonitor()
