"""
Database integration for historical business data and benchmarks.
"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional


class BusinessDataDB:
    """Database for storing and querying historical business data."""

    def __init__(self, db_path: str = "data/business_intelligence.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def init_database(self):
        """Initialize database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Business ventures table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS business_ventures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                industry TEXT NOT NULL,
                founded_date DATE,
                status TEXT CHECK(status IN ('active', 'failed', 'acquired', 'ipo')),
                initial_funding REAL,
                total_funding REAL,
                valuation REAL,
                employees INTEGER,
                revenue REAL,
                region TEXT,
                business_model TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Industry benchmarks table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS industry_benchmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                industry TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL,
                metric_unit TEXT,
                percentile INTEGER,
                year INTEGER,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Market events table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS market_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_date DATE NOT NULL,
                event_type TEXT,
                industry TEXT,
                description TEXT,
                impact_level TEXT CHECK(impact_level IN ('low', 'medium', 'high')),
                affected_companies TEXT, -- JSON array
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Financial metrics table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS financial_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venture_id INTEGER,
                metric_date DATE,
                revenue REAL,
                profit_margin REAL,
                customer_count INTEGER,
                cac REAL, -- Customer Acquisition Cost
                ltv REAL, -- Customer Lifetime Value
                churn_rate REAL,
                burn_rate REAL,
                runway_months INTEGER,
                FOREIGN KEY (venture_id) REFERENCES business_ventures (id)
            )
        """
        )

        conn.commit()
        conn.close()

        # Populate with sample data
        self.populate_sample_data()

    def populate_sample_data(self):
        """Add sample historical data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM business_ventures")
        if cursor.fetchone()[0] > 0:
            conn.close()
            return

        # Sample business ventures
        ventures = [
            (
                "TechStart",
                "SaaS",
                "2019-01-15",
                "active",
                1000000,
                5000000,
                25000000,
                45,
                3000000,
                "North America",
                "subscription",
            ),
            (
                "EcommerceNow",
                "E-commerce",
                "2018-03-20",
                "acquired",
                500000,
                12000000,
                80000000,
                120,
                15000000,
                "Europe",
                "marketplace",
            ),
            (
                "FinTechInc",
                "FinTech",
                "2020-06-10",
                "active",
                2000000,
                15000000,
                100000000,
                80,
                8000000,
                "Asia",
                "B2B",
            ),
            (
                "FailedStartup",
                "HealthTech",
                "2017-08-05",
                "failed",
                800000,
                800000,
                0,
                0,
                0,
                "North America",
                "B2C",
            ),
            (
                "UnicornCorp",
                "AI/ML",
                "2016-12-01",
                "ipo",
                5000000,
                150000000,
                2000000000,
                500,
                50000000,
                "North America",
                "enterprise",
            ),
        ]

        cursor.executemany(
            """
            INSERT INTO business_ventures
            (name, industry, founded_date, status, initial_funding, total_funding, valuation, employees, revenue, region, business_model)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            ventures,
        )

        # Sample industry benchmarks
        benchmarks = [
            ("SaaS", "Customer Acquisition Cost", 120, "USD", 50, 2024, "Industry Report"),
            ("SaaS", "Customer Lifetime Value", 480, "USD", 50, 2024, "Industry Report"),
            ("SaaS", "Monthly Churn Rate", 5.2, "percent", 50, 2024, "Industry Report"),
            ("SaaS", "Revenue Growth Rate", 25, "percent", 75, 2024, "Industry Report"),
            ("E-commerce", "Conversion Rate", 2.8, "percent", 50, 2024, "E-commerce Study"),
            ("E-commerce", "Average Order Value", 85, "USD", 50, 2024, "E-commerce Study"),
            ("FinTech", "Customer Acquisition Cost", 180, "USD", 50, 2024, "FinTech Analysis"),
        ]

        cursor.executemany(
            """
            INSERT INTO industry_benchmarks
            (industry, metric_name, metric_value, metric_unit, percentile, year, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            benchmarks,
        )

        conn.commit()
        conn.close()

    def query_industry_success_rates(self, industry: str) -> Dict[str, Any]:
        """Get success rates for a specific industry."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                status,
                COUNT(*) as count,
                AVG(total_funding) as avg_funding,
                AVG(valuation) as avg_valuation
            FROM business_ventures
            WHERE industry = ?
            GROUP BY status
        """,
            (industry,),
        )

        results = cursor.fetchall()
        conn.close()

        total_ventures = sum(row[1] for row in results)
        analysis = {
            "industry": industry,
            "total_ventures": total_ventures,
            "status_breakdown": {},
            "success_rate": 0,
            "avg_funding_by_status": {},
        }

        for status, count, avg_funding, avg_valuation in results:
            percentage = (count / total_ventures * 100) if total_ventures > 0 else 0
            analysis["status_breakdown"][status] = {
                "count": count,
                "percentage": round(percentage, 1),
            }
            analysis["avg_funding_by_status"][status] = {
                "funding": avg_funding or 0,
                "valuation": avg_valuation or 0,
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT metric_name, metric_value, metric_unit, percentile, source
            FROM industry_benchmarks
            WHERE industry = ?
            ORDER BY metric_name
        """,
            (industry,),
        )

        results = cursor.fetchall()
        conn.close()

        benchmarks: Dict[str, Any] = {"industry": industry, "metrics": []}

        for metric_name, value, unit, percentile, source in results:
            benchmarks["metrics"].append(
                {
                    "name": metric_name,
                    "value": value,
                    "unit": unit,
                    "percentile": f"{percentile}th",
                    "source": source,
                }
            )

        return benchmarks

    def analyze_similar_ventures(
        self, industry: str, business_model: str, region: Optional[str] = None
    ) -> Dict[str, Any]:
        """Find and analyze similar ventures."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT name, status, initial_funding, total_funding, valuation, employees, revenue
            FROM business_ventures
            WHERE industry = ? AND business_model = ?
        """
        params = [industry, business_model]

        if region:
            query += " AND region = ?"
            params.append(region)

        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()

        if not results:
            return {"similar_ventures": [], "analysis": "No similar ventures found in database"}

        ventures = []
        total_funding_sum = 0
        successful_ventures = 0

        for name, status, initial, total, valuation, employees, revenue in results:
            ventures.append(
                {
                    "name": name,
                    "status": status,
                    "initial_funding": initial or 0,
                    "total_funding": total or 0,
                    "valuation": valuation or 0,
                    "employees": employees or 0,
                    "revenue": revenue or 0,
                }
            )

            if total:
                total_funding_sum += total

            if status in ["active", "acquired", "ipo"]:
                successful_ventures += 1

        return {
            "similar_ventures": ventures,
            "count": len(ventures),
            "success_rate": round((successful_ventures / len(ventures) * 100), 1),
            "avg_total_funding": round(total_funding_sum / len(ventures), 0) if ventures else 0,
            "analysis": f"Found {len(ventures)} similar ventures with {round((successful_ventures / len(ventures) * 100), 1)}% success rate",
        }

    def add_venture(self, venture_data: Dict[str, Any]) -> int:
        """Add a new venture to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO business_ventures
            (name, industry, founded_date, status, initial_funding, total_funding,
             valuation, employees, revenue, region, business_model)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

        venture_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return venture_id or 0


def create_database_tool_spec():
    """Create tool specification for AG2 integration."""
    return {
        "name": "business_database",
        "description": "Query historical business data and benchmarks",
        "parameters": {
            "type": "object",
            "properties": {
                "query_type": {
                    "type": "string",
                    "enum": ["success_rates", "benchmarks", "similar_ventures", "add_venture"],
                    "description": "Type of database query to perform",
                },
                "params": {
                    "type": "object",
                    "description": "Parameters specific to the query type",
                },
            },
            "required": ["query_type", "params"],
        },
    }


def database_tool_executor(query_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute database operations for AG2."""
    db = BusinessDataDB()

    if query_type == "success_rates":
        return db.query_industry_success_rates(params["industry"])

    elif query_type == "benchmarks":
        return db.get_industry_benchmarks(params["industry"])

    elif query_type == "similar_ventures":
        return db.analyze_similar_ventures(
            params["industry"],
            params["business_model"],
            params.get("region") if "region" in params else None,
        )

    elif query_type == "add_venture":
        venture_id = db.add_venture(params["venture_data"])
        return {"success": True, "venture_id": venture_id}

    else:
        return {"error": f"Unknown query type: {query_type}"}
