"""
Tests for database functionality.
"""

import sqlite3
from unittest.mock import Mock, patch

from src.database_config import DatabaseConfig
from src.tools.database_production import (
    ProductionBusinessDataDB,
    database_tool_executor,
)
from src.tools.database_tools import BusinessDataDB


class TestBusinessDataDB:
    """Test SQLite database functionality."""

    def test_init_database(self, test_db_path):
        """Test database initialization."""
        db = BusinessDataDB(test_db_path)
        assert db is not None  # Use the variable

        # Check that tables were created
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            "business_ventures",
            "industry_benchmarks",
            "market_events",
            "financial_metrics",
        ]

        for table in expected_tables:
            assert table in tables

        conn.close()

    def test_populate_sample_data(self, test_db_path):
        """Test sample data population."""
        db = BusinessDataDB(test_db_path)
        assert db is not None  # Use the variable

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Check ventures were added
        cursor.execute("SELECT COUNT(*) FROM business_ventures")
        venture_count = cursor.fetchone()[0]
        assert venture_count > 0

        # Check benchmarks were added
        cursor.execute("SELECT COUNT(*) FROM industry_benchmarks")
        benchmark_count = cursor.fetchone()[0]
        assert benchmark_count > 0

        conn.close()

    def test_query_industry_success_rates(self, test_db_path):
        """Test industry success rate queries."""
        db = BusinessDataDB(test_db_path)

        result = db.query_industry_success_rates("SaaS")

        assert "industry" in result
        assert result["industry"] == "SaaS"
        assert "total_ventures" in result
        assert "status_breakdown" in result
        assert "success_rate" in result
        assert isinstance(result["success_rate"], (int, float))

    def test_get_industry_benchmarks(self, test_db_path):
        """Test industry benchmark queries."""
        db = BusinessDataDB(test_db_path)

        result = db.get_industry_benchmarks("SaaS")

        assert "industry" in result
        assert result["industry"] == "SaaS"
        assert "metrics" in result
        assert isinstance(result["metrics"], list)

    def test_analyze_similar_ventures(self, test_db_path):
        """Test similar venture analysis."""
        db = BusinessDataDB(test_db_path)

        result = db.analyze_similar_ventures("SaaS", "subscription")

        assert "similar_ventures" in result
        assert "count" in result
        assert "success_rate" in result
        assert isinstance(result["similar_ventures"], list)

    def test_add_venture(self, test_db_path, sample_business_data):
        """Test adding new venture."""
        db = BusinessDataDB(test_db_path)

        venture_id = db.add_venture(sample_business_data)

        assert venture_id is not None
        assert isinstance(venture_id, int)

        # Verify venture was added
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM business_ventures WHERE id = ?", (venture_id,))
        result = cursor.fetchone()
        assert result[0] == sample_business_data["name"]
        conn.close()


class TestProductionBusinessDataDB:
    """Test production database adapter."""

    def test_init_with_sqlite_fallback(self):
        """Test initialization with SQLite fallback."""
        with patch("src.tools.database_production.db_config") as mock_config:
            mock_config.use_postgres = False
            mock_config.environment = "test"

            with patch("src.tools.database_production.BusinessDataDB") as mock_sqlite:
                db = ProductionBusinessDataDB()
                assert db is not None  # Use the variable
                mock_sqlite.assert_called_once()

    def test_query_with_sqlite_fallback(self):
        """Test queries with SQLite fallback."""
        with patch("src.tools.database_production.db_config") as mock_config:
            mock_config.use_postgres = False
            mock_config.environment = "test"

            with patch("src.tools.database_production.BusinessDataDB") as mock_sqlite:
                mock_sqlite_instance = Mock()
                mock_sqlite.return_value = mock_sqlite_instance
                mock_sqlite_instance.query_industry_success_rates.return_value = {
                    "industry": "SaaS",
                    "success_rate": 75.0,
                }

                db = ProductionBusinessDataDB()
                result = db.query_industry_success_rates("SaaS")

                assert result["industry"] == "SaaS"
                assert result["success_rate"] == 75.0
                mock_sqlite_instance.query_industry_success_rates.assert_called_once_with("SaaS")


class TestDatabaseToolExecutor:
    """Test database tool executor."""

    def test_success_rates_query(self, mock_database_config):
        """Test success rates query execution."""
        mock_database_config.use_postgres = False

        with patch("src.tools.database_production.ProductionBusinessDataDB") as mock_db:
            mock_instance = Mock()
            mock_db.return_value = mock_instance
            mock_instance.query_industry_success_rates.return_value = {
                "industry": "SaaS",
                "success_rate": 80.0,
            }

            result = database_tool_executor("success_rates", {"industry": "SaaS"})

            assert result["industry"] == "SaaS"
            assert result["success_rate"] == 80.0

    def test_benchmarks_query(self, mock_database_config):
        """Test benchmarks query execution."""
        mock_database_config.use_postgres = False

        with patch("src.tools.database_production.ProductionBusinessDataDB") as mock_db:
            mock_instance = Mock()
            mock_db.return_value = mock_instance
            mock_instance.get_industry_benchmarks.return_value = {
                "industry": "SaaS",
                "metrics": [{"name": "CAC", "value": 120}],
            }

            result = database_tool_executor("benchmarks", {"industry": "SaaS"})

            assert result["industry"] == "SaaS"
            assert len(result["metrics"]) == 1

    def test_unknown_query_type(self, mock_database_config):
        """Test handling of unknown query type."""
        result = database_tool_executor("unknown_operation", {})

        assert "error" in result
        assert "unknown_operation" in result["error"]


class TestDatabaseConfig:
    """Test database configuration."""

    def test_sqlite_environment(self):
        """Test SQLite configuration in development."""
        with patch.dict("os.environ", {"ENVIRONMENT": "development", "DATABASE_URL": ""}):
            with patch("src.database_config.HAS_POSTGRES", False):
                config = DatabaseConfig()
                assert config.environment == "development"
                assert not config.use_postgres

    def test_postgres_environment(self):
        """Test PostgreSQL configuration in production."""
        with patch.dict("os.environ", {"ENVIRONMENT": "production"}):
            with patch("src.database_config.HAS_POSTGRES", True):
                config = DatabaseConfig()
                assert config.environment == "production"
                assert config.use_postgres

    def test_database_url_override(self):
        """Test DATABASE_URL override."""
        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://test:test@localhost/test"}):
            with patch("src.database_config.HAS_POSTGRES", True):
                config = DatabaseConfig()
                assert config.use_postgres
                assert config.database_url == "postgresql://test:test@localhost/test"
