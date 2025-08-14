"""
Production database adapter for PostgreSQL with fallback to SQLite.
Maintains the same interface as BusinessDataDB for seamless integration.
"""

from typing import Dict, Any
import logging
from src.database_config import db_config
from src.tools.database_tools import BusinessDataDB
from src.error_handling import (
    DatabaseError,
    handle_errors,
    retry_with_backoff,
    DATABASE_RETRY_CONFIG,
    validate_input,
    safe_execute,
    track_errors,
)

logger = logging.getLogger(__name__)


class ProductionBusinessDataDB:
    """Production database adapter with PostgreSQL/SQLite support."""

    def __init__(self):
        self.db_config = db_config

        # Use appropriate database based on environment
        if self.db_config.use_postgres:
            logger.info("Using PostgreSQL for production database")
        else:
            logger.info("Using SQLite for development database")
            # Fallback to original SQLite implementation
            self._sqlite_db = BusinessDataDB()

        self.init_database()

    @retry_with_backoff(**DATABASE_RETRY_CONFIG)
    @handle_errors(error_mapping={ConnectionError: DatabaseError, TimeoutError: DatabaseError})
    @track_errors
    def init_database(self):
        """Initialize database with required tables."""
        try:
            if self.db_config.use_postgres:
                self.db_config.init_database()
                self.populate_sample_data()
            else:
                # SQLite initialization is handled by BusinessDataDB
                pass
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise DatabaseError(f"Failed to initialize database: {str(e)}")

    def populate_sample_data(self):
        """Add sample historical data."""
        if not self.db_config.use_postgres:
            # SQLite sample data is handled by BusinessDataDB
            return

        with self.db_config.get_connection() as conn:
            cursor = conn.cursor()

            # Check if data already exists
            cursor.execute("SELECT COUNT(*) FROM business_ventures")
            result = cursor.fetchone()
            if result and result[0] > 0:
                return

            # Sample business ventures - PostgreSQL version with proper types
            ventures = [
                (
                    "TechStart",
                    "SaaS",
                    "2019-01-15",
                    "active",
                    1000000.00,
                    5000000.00,
                    25000000.00,
                    45,
                    3000000.00,
                    "North America",
                    "subscription",
                ),
                (
                    "EcommerceNow",
                    "E-commerce",
                    "2018-03-20",
                    "acquired",
                    500000.00,
                    12000000.00,
                    80000000.00,
                    120,
                    15000000.00,
                    "Europe",
                    "marketplace",
                ),
                (
                    "FinTechInc",
                    "FinTech",
                    "2020-06-10",
                    "active",
                    2000000.00,
                    15000000.00,
                    100000000.00,
                    80,
                    8000000.00,
                    "Asia",
                    "B2B",
                ),
                (
                    "FailedStartup",
                    "HealthTech",
                    "2017-08-05",
                    "failed",
                    800000.00,
                    800000.00,
                    0.00,
                    0,
                    0.00,
                    "North America",
                    "B2C",
                ),
                (
                    "UnicornCorp",
                    "AI/ML",
                    "2016-12-01",
                    "ipo",
                    5000000.00,
                    150000000.00,
                    2000000000.00,
                    500,
                    50000000.00,
                    "North America",
                    "enterprise",
                ),
            ]

            cursor.executemany(
                """
                INSERT INTO business_ventures
                (name, industry, founded_date, status, initial_funding, total_funding, valuation, employees, revenue, region, business_model)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
                ventures,
            )

            # Sample industry benchmarks
            benchmarks = [
                ("SaaS", "Customer Acquisition Cost", 120.00, "USD", 50, 2024, "Industry Report"),
                ("SaaS", "Customer Lifetime Value", 480.00, "USD", 50, 2024, "Industry Report"),
                ("SaaS", "Monthly Churn Rate", 5.20, "percent", 50, 2024, "Industry Report"),
                ("SaaS", "Revenue Growth Rate", 25.00, "percent", 75, 2024, "Industry Report"),
                ("E-commerce", "Conversion Rate", 2.80, "percent", 50, 2024, "E-commerce Study"),
                ("E-commerce", "Average Order Value", 85.00, "USD", 50, 2024, "E-commerce Study"),
                (
                    "FinTech",
                    "Customer Acquisition Cost",
                    180.00,
                    "USD",
                    50,
                    2024,
                    "FinTech Analysis",
                ),
            ]

            cursor.executemany(
                """
                INSERT INTO industry_benchmarks
                (industry, metric_name, metric_value, metric_unit, percentile, year, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
                benchmarks,
            )

            conn.commit()

    @retry_with_backoff(**DATABASE_RETRY_CONFIG)
    @handle_errors(error_mapping={ConnectionError: DatabaseError, TimeoutError: DatabaseError})
    @track_errors
    def query_industry_success_rates(self, industry: str) -> Dict[str, Any]:
        """Get success rates for a specific industry."""
        validate_input({"industry": industry}, ["industry"], {"industry": str})

        if not self.db_config.use_postgres:
            return safe_execute(
                self._sqlite_db.query_industry_success_rates,
                industry,
                fallback_value={"error": "Database query failed", "industry": industry},
                error_context=f"SQLite query for industry: {industry}",
            )

        with self.db_config.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    status,
                    COUNT(*) as count,
                    AVG(total_funding) as avg_funding,
                    AVG(valuation) as avg_valuation
                FROM business_ventures
                WHERE industry = %s
                GROUP BY status
            """,
                (industry,),
            )

            results = cursor.fetchall()

        total_ventures = sum(row["count"] for row in results)
        analysis = {
            "industry": industry,
            "total_ventures": total_ventures,
            "status_breakdown": {},
            "success_rate": 0,
            "avg_funding_by_status": {},
        }

        for row in results:
            status = row["status"]
            count = row["count"]
            avg_funding = row["avg_funding"]
            avg_valuation = row["avg_valuation"]

            percentage = (count / total_ventures * 100) if total_ventures > 0 else 0
            analysis["status_breakdown"][status] = {
                "count": count,
                "percentage": round(percentage, 1),
            }
            analysis["avg_funding_by_status"][status] = {
                "funding": float(avg_funding or 0),
                "valuation": float(avg_valuation or 0),
            }

        # Calculate success rate (active + acquired + ipo)
        success_statuses = ["active", "acquired", "ipo"]
        success_count = sum(
            analysis["status_breakdown"].get(status, {}).get("count", 0)
            for status in success_statuses
        )
        analysis["success_rate"] = (
            round((success_count / total_ventures * 100), 1) if total_ventures > 0 else 0
        )

        return analysis

    def get_industry_benchmarks(self, industry: str) -> Dict[str, Any]:
        """Get industry benchmarks for comparison."""
        if not self.db_config.use_postgres:
            return self._sqlite_db.get_industry_benchmarks(industry)

        with self.db_config.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT metric_name, metric_value, metric_unit, percentile, source
                FROM industry_benchmarks
                WHERE industry = %s
                ORDER BY metric_name
            """,
                (industry,),
            )

            results = cursor.fetchall()

        benchmarks = {"industry": industry, "metrics": []}

        for row in results:
            benchmarks["metrics"].append(
                {
                    "name": row["metric_name"],
                    "value": float(row["metric_value"]),
                    "unit": row["metric_unit"],
                    "percentile": f"{row['percentile']}th",
                    "source": row["source"],
                }
            )

        return benchmarks

    def analyze_similar_ventures(
        self, industry: str, business_model: str, region: str = None
    ) -> Dict[str, Any]:
        """Find and analyze similar ventures."""
        if not self.db_config.use_postgres:
            return self._sqlite_db.analyze_similar_ventures(industry, business_model, region)

        with self.db_config.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT name, status, initial_funding, total_funding, valuation, employees, revenue
                FROM business_ventures
                WHERE industry = %s AND business_model = %s
            """
            params = [industry, business_model]

            if region:
                query += " AND region = %s"
                params.append(region)

            cursor.execute(query, params)
            results = cursor.fetchall()

        if not results:
            return {"similar_ventures": [], "analysis": "No similar ventures found in database"}

        ventures = []
        total_funding_sum = 0
        successful_ventures = 0

        for row in results:
            venture = {
                "name": row["name"],
                "status": row["status"],
                "initial_funding": float(row["initial_funding"] or 0),
                "total_funding": float(row["total_funding"] or 0),
                "valuation": float(row["valuation"] or 0),
                "employees": row["employees"] or 0,
                "revenue": float(row["revenue"] or 0),
            }
            ventures.append(venture)

            if row["total_funding"]:
                total_funding_sum += float(row["total_funding"])

            if row["status"] in ["active", "acquired", "ipo"]:
                successful_ventures += 1

        return {
            "similar_ventures": ventures,
            "count": len(ventures),
            "success_rate": round((successful_ventures / len(ventures) * 100), 1),
            "avg_total_funding": round(total_funding_sum / len(ventures), 0) if ventures else 0,
            "analysis": f"Found {len(ventures)} similar ventures with {round((successful_ventures / len(ventures) * 100), 1)}% success rate",
        }

    def add_venture(self, venture_data: Dict[str, Any]) -> str:
        """Add a new venture to the database."""
        if not self.db_config.use_postgres:
            return str(self._sqlite_db.add_venture(venture_data))

        with self.db_config.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO business_ventures
                (name, industry, founded_date, status, initial_funding, total_funding,
                 valuation, employees, revenue, region, business_model)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """,
                (
                    venture_data["name"],
                    venture_data["industry"],
                    venture_data.get("founded_date"),
                    venture_data.get("status", "active"),
                    venture_data.get("initial_funding"),
                    venture_data.get("total_funding"),
                    venture_data.get("valuation"),
                    venture_data.get("employees"),
                    venture_data.get("revenue"),
                    venture_data.get("region"),
                    venture_data.get("business_model"),
                ),
            )

            result = cursor.fetchone()
            venture_id = str(result["id"])
            conn.commit()

        return venture_id


def database_tool_executor(query_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute database operations for AG2 with production database support."""
    db = ProductionBusinessDataDB()

    if query_type == "success_rates":
        return db.query_industry_success_rates(params["industry"])

    elif query_type == "benchmarks":
        return db.get_industry_benchmarks(params["industry"])

    elif query_type == "similar_ventures":
        return db.analyze_similar_ventures(
            params["industry"], params["business_model"], params.get("region")
        )

    elif query_type == "add_venture":
        venture_id = db.add_venture(params["venture_data"])
        return {"success": True, "venture_id": venture_id}

    else:
        return {"error": f"Unknown query type: {query_type}"}
