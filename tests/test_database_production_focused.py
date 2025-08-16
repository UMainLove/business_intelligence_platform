"""
Focused tests for database_production.py to achieve 95%+ coverage.
"""

from unittest.mock import Mock, patch

import pytest

from src.error_handling import DatabaseError
from src.tools.database_production import ProductionBusinessDataDB, database_tool_executor


class TestProductionBusinessDataDB:
    """Test ProductionBusinessDataDB class."""

    @patch("src.tools.database_production.db_config")
    @patch("src.tools.database_production.BusinessDataDB")
    @patch("src.tools.database_production.logger")
    def test_initialization_postgres(self, mock_logger, mock_sqlite_db_class, mock_db_config):
        """Test initialization with PostgreSQL."""
        mock_db_config.use_postgres = True
        mock_db_config.init_database = Mock()

        # Mock get_connection to return a proper mock connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (1,)  # Existing data to skip population
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db_config.get_connection.return_value = mock_conn

        db = ProductionBusinessDataDB()

        assert db.db_config == mock_db_config
        mock_logger.info.assert_called_with("Using PostgreSQL for production database")
        # Should not create SQLite fallback
        mock_sqlite_db_class.assert_not_called()

    @patch("src.tools.database_production.db_config")
    @patch("src.tools.database_production.BusinessDataDB")
    @patch("src.tools.database_production.logger")
    def test_initialization_sqlite(self, mock_logger, mock_sqlite_db_class, mock_db_config):
        """Test initialization with SQLite fallback."""
        mock_db_config.use_postgres = False
        mock_sqlite_instance = Mock()
        mock_sqlite_db_class.return_value = mock_sqlite_instance

        db = ProductionBusinessDataDB()

        assert db.db_config == mock_db_config
        mock_logger.info.assert_called_with("Using SQLite for development database")
        mock_sqlite_db_class.assert_called_once()
        assert db._sqlite_db == mock_sqlite_instance

    @patch("src.tools.database_production.db_config")
    @patch("src.tools.database_production.logger")
    def test_init_database_postgres_success(self, mock_logger, mock_db_config):
        """Test successful database initialization with PostgreSQL."""
        mock_db_config.use_postgres = True
        mock_db_config.init_database = Mock()

        # Mock the populate_sample_data method to avoid complex setup
        with patch.object(ProductionBusinessDataDB, "populate_sample_data"):
            db = ProductionBusinessDataDB()

        mock_db_config.init_database.assert_called_once()

    @patch("src.tools.database_production.db_config")
    @patch("src.tools.database_production.BusinessDataDB")
    @patch("src.tools.database_production.logger")
    def test_init_database_sqlite_success(self, mock_logger, mock_sqlite_db_class, mock_db_config):
        """Test successful database initialization with SQLite."""
        mock_db_config.use_postgres = False

        db = ProductionBusinessDataDB()

        # SQLite initialization should be handled by BusinessDataDB
        mock_sqlite_db_class.assert_called_once()

    @patch("src.tools.database_production.db_config")
    @patch("src.tools.database_production.logger")
    def test_init_database_postgres_failure(self, mock_logger, mock_db_config):
        """Test database initialization failure with PostgreSQL."""
        mock_db_config.use_postgres = True
        mock_db_config.init_database.side_effect = Exception("Connection failed")

        with pytest.raises(DatabaseError, match="Failed to initialize database"):
            ProductionBusinessDataDB()

        mock_logger.error.assert_called()

    @patch("src.tools.database_production.db_config")
    def test_populate_sample_data_sqlite_skip(self, mock_db_config):
        """Test populate_sample_data skips for SQLite."""
        mock_db_config.use_postgres = False

        with patch("src.tools.database_production.BusinessDataDB"):
            db = ProductionBusinessDataDB()

        # Should return early for SQLite
        result = db.populate_sample_data()
        assert result is None

    @patch("src.tools.database_production.db_config")
    def test_populate_sample_data_postgres_existing_data(self, mock_db_config):
        """Test populate_sample_data with existing data in PostgreSQL."""
        mock_db_config.use_postgres = True

        # Mock connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (5,)  # Existing data
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db_config.get_connection.return_value = mock_conn
        mock_db_config.init_database = Mock()

        with patch.object(ProductionBusinessDataDB, "populate_sample_data"):
            db = ProductionBusinessDataDB()

        # Call populate_sample_data directly
        db.populate_sample_data()

        # Should check count and return early
        mock_cursor.execute.assert_called_with("SELECT COUNT(*) FROM business_ventures")
        mock_cursor.executemany.assert_not_called()

    @patch("src.tools.database_production.db_config")
    def test_populate_sample_data_postgres_insert_data(self, mock_db_config):
        """Test populate_sample_data inserts data in PostgreSQL."""
        mock_db_config.use_postgres = True

        # Mock connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (0,)  # No existing data
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db_config.get_connection.return_value = mock_conn
        mock_db_config.init_database = Mock()

        with patch.object(ProductionBusinessDataDB, "populate_sample_data"):
            db = ProductionBusinessDataDB()

        # Call populate_sample_data directly
        db.populate_sample_data()

        # Should insert both ventures and benchmarks
        assert mock_cursor.executemany.call_count == 2
        mock_conn.commit.assert_called_once()

    @patch("src.tools.database_production.db_config")
    @patch("src.tools.database_production.BusinessDataDB")
    def test_query_industry_success_rates_sqlite(self, mock_sqlite_db_class, mock_db_config):
        """Test query_industry_success_rates with SQLite."""
        mock_db_config.use_postgres = False
        mock_sqlite_db = Mock()
        mock_sqlite_db.query_industry_success_rates.return_value = {
            "industry": "SaaS",
            "success_rate": 75.0,
        }
        mock_sqlite_db_class.return_value = mock_sqlite_db

        db = ProductionBusinessDataDB()
        result = db.query_industry_success_rates("SaaS")

        mock_sqlite_db.query_industry_success_rates.assert_called_once_with("SaaS")
        assert result["industry"] == "SaaS"

    @patch("src.tools.database_production.db_config")
    @patch("src.tools.database_production.validate_input")
    def test_query_industry_success_rates_postgres(self, mock_validate, mock_db_config):
        """Test query_industry_success_rates with PostgreSQL."""
        mock_db_config.use_postgres = True
        mock_db_config.init_database = Mock()

        # Mock connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {"status": "active", "count": 3, "avg_funding": 1000000.0, "avg_valuation": 5000000.0},
            {"status": "failed", "count": 1, "avg_funding": 500000.0, "avg_valuation": 0.0},
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db_config.get_connection.return_value = mock_conn

        with patch.object(ProductionBusinessDataDB, "populate_sample_data"):
            db = ProductionBusinessDataDB()

        result = db.query_industry_success_rates("SaaS")

        mock_validate.assert_called_once()
        assert result["industry"] == "SaaS"
        assert result["total_ventures"] == 4
        assert result["success_rate"] == 75.0  # 3 out of 4 successful
        assert "active" in result["status_breakdown"]
        assert "failed" in result["status_breakdown"]

    @patch("src.tools.database_production.db_config")
    def test_query_industry_success_rates_postgres_no_results(self, mock_db_config):
        """Test query_industry_success_rates with no results."""
        mock_db_config.use_postgres = True
        mock_db_config.init_database = Mock()

        # Mock connection with empty results
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db_config.get_connection.return_value = mock_conn

        with patch.object(ProductionBusinessDataDB, "populate_sample_data"):
            db = ProductionBusinessDataDB()

        result = db.query_industry_success_rates("NonExistent")

        assert result["industry"] == "NonExistent"
        assert result["total_ventures"] == 0
        assert result["success_rate"] == 0

    @patch("src.tools.database_production.db_config")
    @patch("src.tools.database_production.BusinessDataDB")
    def test_get_industry_benchmarks_sqlite(self, mock_sqlite_db_class, mock_db_config):
        """Test get_industry_benchmarks with SQLite."""
        mock_db_config.use_postgres = False
        mock_sqlite_db = Mock()
        mock_sqlite_db.get_industry_benchmarks.return_value = {"industry": "SaaS", "metrics": []}
        mock_sqlite_db_class.return_value = mock_sqlite_db

        db = ProductionBusinessDataDB()
        result = db.get_industry_benchmarks("SaaS")

        mock_sqlite_db.get_industry_benchmarks.assert_called_once_with("SaaS")
        assert result["industry"] == "SaaS"

    @patch("src.tools.database_production.db_config")
    def test_get_industry_benchmarks_postgres(self, mock_db_config):
        """Test get_industry_benchmarks with PostgreSQL."""
        mock_db_config.use_postgres = True
        mock_db_config.init_database = Mock()

        # Mock connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {
                "metric_name": "CAC",
                "metric_value": 120.0,
                "metric_unit": "USD",
                "percentile": 50,
                "source": "Industry Report",
            }
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db_config.get_connection.return_value = mock_conn

        with patch.object(ProductionBusinessDataDB, "populate_sample_data"):
            db = ProductionBusinessDataDB()

        result = db.get_industry_benchmarks("SaaS")

        assert result["industry"] == "SaaS"
        assert len(result["metrics"]) == 1
        metric = result["metrics"][0]
        assert metric["name"] == "CAC"
        assert metric["value"] == 120.0
        assert metric["percentile"] == "50th"

    @patch("src.tools.database_production.db_config")
    @patch("src.tools.database_production.BusinessDataDB")
    def test_analyze_similar_ventures_sqlite(self, mock_sqlite_db_class, mock_db_config):
        """Test analyze_similar_ventures with SQLite."""
        mock_db_config.use_postgres = False
        mock_sqlite_db = Mock()
        mock_sqlite_db.analyze_similar_ventures.return_value = {"similar_ventures": [], "count": 0}
        mock_sqlite_db_class.return_value = mock_sqlite_db

        db = ProductionBusinessDataDB()
        result = db.analyze_similar_ventures("SaaS", "subscription", "US")

        mock_sqlite_db.analyze_similar_ventures.assert_called_once_with(
            "SaaS", "subscription", "US"
        )
        assert result["count"] == 0

    @patch("src.tools.database_production.db_config")
    def test_analyze_similar_ventures_postgres_with_region(self, mock_db_config):
        """Test analyze_similar_ventures with PostgreSQL and region filter."""
        mock_db_config.use_postgres = True
        mock_db_config.init_database = Mock()

        # Mock connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {
                "name": "SimilarCorp",
                "status": "active",
                "initial_funding": 1000000.0,
                "total_funding": 5000000.0,
                "valuation": 25000000.0,
                "employees": 50,
                "revenue": 3000000.0,
            }
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db_config.get_connection.return_value = mock_conn

        with patch.object(ProductionBusinessDataDB, "populate_sample_data"):
            db = ProductionBusinessDataDB()

        result = db.analyze_similar_ventures("SaaS", "subscription", "North America")

        # Verify query includes region filter
        call_args = mock_cursor.execute.call_args[0]
        assert "AND region = %s" in call_args[0]
        assert "North America" in call_args[1]

        assert result["count"] == 1
        assert result["success_rate"] == 100.0
        assert len(result["similar_ventures"]) == 1

    @patch("src.tools.database_production.db_config")
    def test_analyze_similar_ventures_postgres_no_region(self, mock_db_config):
        """Test analyze_similar_ventures with PostgreSQL without region filter."""
        mock_db_config.use_postgres = True
        mock_db_config.init_database = Mock()

        # Mock connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db_config.get_connection.return_value = mock_conn

        with patch.object(ProductionBusinessDataDB, "populate_sample_data"):
            db = ProductionBusinessDataDB()

        result = db.analyze_similar_ventures("SaaS", "subscription")

        # Verify query doesn't include region filter
        call_args = mock_cursor.execute.call_args[0]
        assert "AND region = %s" not in call_args[0]
        assert len(call_args[1]) == 2  # Only industry and business_model

        assert result["similar_ventures"] == []
        assert "No similar ventures found" in result["analysis"]

    @patch("src.tools.database_production.db_config")
    def test_analyze_similar_ventures_postgres_mixed_statuses(self, mock_db_config):
        """Test analyze_similar_ventures with mixed venture statuses."""
        mock_db_config.use_postgres = True
        mock_db_config.init_database = Mock()

        # Mock connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {
                "name": "SuccessfulCorp",
                "status": "acquired",
                "initial_funding": 1000000.0,
                "total_funding": 5000000.0,
                "valuation": 25000000.0,
                "employees": 50,
                "revenue": 3000000.0,
            },
            {
                "name": "FailedCorp",
                "status": "failed",
                "initial_funding": 500000.0,
                "total_funding": 500000.0,
                "valuation": 0.0,
                "employees": 0,
                "revenue": 0.0,
            },
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db_config.get_connection.return_value = mock_conn

        with patch.object(ProductionBusinessDataDB, "populate_sample_data"):
            db = ProductionBusinessDataDB()

        result = db.analyze_similar_ventures("SaaS", "subscription")

        assert result["count"] == 2
        assert result["success_rate"] == 50.0  # 1 out of 2 successful
        assert result["avg_total_funding"] == 2750000  # (5000000 + 500000) / 2

    @patch("src.tools.database_production.db_config")
    def test_analyze_similar_ventures_null_values(self, mock_db_config):
        """Test analyze_similar_ventures with null values in data."""
        mock_db_config.use_postgres = True
        mock_db_config.init_database = Mock()

        # Mock connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {
                "name": "NullValuesCorp",
                "status": "active",
                "initial_funding": None,
                "total_funding": None,
                "valuation": None,
                "employees": None,
                "revenue": None,
            }
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db_config.get_connection.return_value = mock_conn

        with patch.object(ProductionBusinessDataDB, "populate_sample_data"):
            db = ProductionBusinessDataDB()

        result = db.analyze_similar_ventures("SaaS", "subscription")

        venture = result["similar_ventures"][0]
        assert venture["initial_funding"] == 0.0
        assert venture["total_funding"] == 0.0
        assert venture["valuation"] == 0.0
        assert venture["employees"] == 0
        assert venture["revenue"] == 0.0

    @patch("src.tools.database_production.db_config")
    @patch("src.tools.database_production.BusinessDataDB")
    def test_add_venture_sqlite(self, mock_sqlite_db_class, mock_db_config):
        """Test add_venture with SQLite."""
        mock_db_config.use_postgres = False
        mock_sqlite_db = Mock()
        mock_sqlite_db.add_venture.return_value = 123
        mock_sqlite_db_class.return_value = mock_sqlite_db

        db = ProductionBusinessDataDB()
        venture_data = {"name": "TestVenture", "industry": "Tech"}

        result = db.add_venture(venture_data)

        mock_sqlite_db.add_venture.assert_called_once_with(venture_data)
        assert result == "123"

    @patch("src.tools.database_production.db_config")
    def test_add_venture_postgres(self, mock_db_config):
        """Test add_venture with PostgreSQL."""
        mock_db_config.use_postgres = True
        mock_db_config.init_database = Mock()

        # Mock connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {"id": 456}
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db_config.get_connection.return_value = mock_conn

        with patch.object(ProductionBusinessDataDB, "populate_sample_data"):
            db = ProductionBusinessDataDB()

        venture_data = {
            "name": "PostgresVenture",
            "industry": "FinTech",
            "founded_date": "2024-01-01",
            "status": "active",
            "initial_funding": 1000000,
            "total_funding": 5000000,
            "valuation": 25000000,
            "employees": 50,
            "revenue": 3000000,
            "region": "North America",
            "business_model": "SaaS",
        }

        result = db.add_venture(venture_data)

        assert result == "456"
        mock_conn.commit.assert_called_once()

        # Verify all data was passed correctly
        call_args = mock_cursor.execute.call_args[0]
        assert "PostgresVenture" in call_args[1]
        assert "FinTech" in call_args[1]

    @patch("src.tools.database_production.db_config")
    def test_add_venture_postgres_minimal_data(self, mock_db_config):
        """Test add_venture with minimal data."""
        mock_db_config.use_postgres = True
        mock_db_config.init_database = Mock()

        # Mock connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {"id": 789}
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db_config.get_connection.return_value = mock_conn

        with patch.object(ProductionBusinessDataDB, "populate_sample_data"):
            db = ProductionBusinessDataDB()

        venture_data = {"name": "MinimalVenture", "industry": "Tech"}

        result = db.add_venture(venture_data)

        assert result == "789"

        # Verify defaults are applied
        call_args = mock_cursor.execute.call_args[0]
        execute_params = call_args[1]
        assert execute_params[3] == "active"  # Default status


class TestDatabaseToolExecutor:
    """Test database_tool_executor function."""

    @patch("src.tools.database_production.ProductionBusinessDataDB")
    def test_success_rates_executor(self, mock_db_class):
        """Test executor for success rates query."""
        mock_db = Mock()
        mock_db.query_industry_success_rates.return_value = {
            "industry": "SaaS",
            "success_rate": 80.0,
        }
        mock_db_class.return_value = mock_db

        result = database_tool_executor("success_rates", {"industry": "SaaS"})

        assert result["industry"] == "SaaS"
        assert result["success_rate"] == 80.0
        mock_db.query_industry_success_rates.assert_called_once_with("SaaS")

    @patch("src.tools.database_production.ProductionBusinessDataDB")
    def test_benchmarks_executor(self, mock_db_class):
        """Test executor for benchmarks query."""
        mock_db = Mock()
        mock_db.get_industry_benchmarks.return_value = {"industry": "FinTech", "metrics": []}
        mock_db_class.return_value = mock_db

        result = database_tool_executor("benchmarks", {"industry": "FinTech"})

        assert result["industry"] == "FinTech"
        mock_db.get_industry_benchmarks.assert_called_once_with("FinTech")

    @patch("src.tools.database_production.ProductionBusinessDataDB")
    def test_similar_ventures_executor(self, mock_db_class):
        """Test executor for similar ventures query."""
        mock_db = Mock()
        mock_db.analyze_similar_ventures.return_value = {"similar_ventures": [], "count": 0}
        mock_db_class.return_value = mock_db

        result = database_tool_executor(
            "similar_ventures", {"industry": "AI", "business_model": "B2B", "region": "Europe"}
        )

        assert result["count"] == 0
        mock_db.analyze_similar_ventures.assert_called_once_with("AI", "B2B", "Europe")

    @patch("src.tools.database_production.ProductionBusinessDataDB")
    def test_similar_ventures_executor_no_region(self, mock_db_class):
        """Test executor for similar ventures query without region."""
        mock_db = Mock()
        mock_db.analyze_similar_ventures.return_value = {"similar_ventures": [], "count": 0}
        mock_db_class.return_value = mock_db

        result = database_tool_executor(
            "similar_ventures", {"industry": "Crypto", "business_model": "DeFi"}
        )

        mock_db.analyze_similar_ventures.assert_called_once_with("Crypto", "DeFi", None)

    @patch("src.tools.database_production.ProductionBusinessDataDB")
    def test_add_venture_executor(self, mock_db_class):
        """Test executor for add venture operation."""
        mock_db = Mock()
        mock_db.add_venture.return_value = "123"
        mock_db_class.return_value = mock_db

        venture_data = {"name": "NewVenture", "industry": "Tech"}
        result = database_tool_executor("add_venture", {"venture_data": venture_data})

        assert result["success"] is True
        assert result["venture_id"] == "123"
        mock_db.add_venture.assert_called_once_with(venture_data)

    def test_unknown_query_type_executor(self):
        """Test executor with unknown query type."""
        result = database_tool_executor("unknown_type", {})

        assert "error" in result
        assert "Unknown query type: unknown_type" in result["error"]


class TestErrorHandling:
    """Test error handling and edge cases."""

    @patch("src.tools.database_production.db_config")
    @patch("src.tools.database_production.BusinessDataDB")
    @patch("src.tools.database_production.safe_execute")
    def test_query_industry_success_rates_sqlite_error(
        self, mock_safe_execute, mock_sqlite_db_class, mock_db_config
    ):
        """Test error handling in SQLite query."""
        mock_db_config.use_postgres = False
        mock_sqlite_db = Mock()
        mock_sqlite_db_class.return_value = mock_sqlite_db

        # Mock safe_execute to return fallback value
        mock_safe_execute.return_value = {"error": "Database query failed", "industry": "SaaS"}

        db = ProductionBusinessDataDB()
        result = db.query_industry_success_rates("SaaS")

        assert "error" in result
        mock_safe_execute.assert_called_once()

    @patch("src.tools.database_production.db_config")
    @patch("src.tools.database_production.validate_input")
    def test_query_validation(self, mock_validate, mock_db_config):
        """Test input validation in queries."""
        mock_db_config.use_postgres = True
        mock_db_config.init_database = Mock()

        # Mock connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db_config.get_connection.return_value = mock_conn

        with patch.object(ProductionBusinessDataDB, "populate_sample_data"):
            db = ProductionBusinessDataDB()

        db.query_industry_success_rates("TestIndustry")

        # Verify validation was called
        mock_validate.assert_called_once_with(
            {"industry": "TestIndustry"}, ["industry"], {"industry": str}
        )

    @patch("src.tools.database_production.db_config")
    def test_connection_error_handling(self, mock_db_config):
        """Test connection error handling with decorators."""
        mock_db_config.use_postgres = True
        mock_db_config.init_database = Mock()

        # Mock connection failure
        mock_db_config.get_connection.side_effect = ConnectionError("Database unavailable")

        with patch.object(ProductionBusinessDataDB, "populate_sample_data"):
            db = ProductionBusinessDataDB()

        # The decorated method should handle ConnectionError
        # Due to the decorators, this should be handled gracefully
        try:
            result = db.query_industry_success_rates("TestIndustry")
            # If decorators work properly, should get a response
            assert isinstance(result, dict)
        except DatabaseError:
            # Expected behavior with error handling
            pass


class TestIntegration:
    """Test integration scenarios."""

    @patch("src.tools.database_production.db_config")
    def test_full_workflow_postgres(self, mock_db_config):
        """Test complete workflow with PostgreSQL."""
        mock_db_config.use_postgres = True
        mock_db_config.init_database = Mock()

        # Mock connection for all operations
        mock_conn = Mock()
        mock_cursor = Mock()

        # Mock different responses for different operations
        def mock_execute(query, params=()):
            if "SELECT COUNT(*)" in query:
                mock_cursor.fetchone.return_value = (0,)  # No existing data
            elif "SELECT\n                    status" in query:
                mock_cursor.fetchall.return_value = [
                    {
                        "status": "active",
                        "count": 2,
                        "avg_funding": 3000000.0,
                        "avg_valuation": 15000000.0,
                    }
                ]
            elif "SELECT metric_name" in query:
                mock_cursor.fetchall.return_value = [
                    {
                        "metric_name": "CAC",
                        "metric_value": 120.0,
                        "metric_unit": "USD",
                        "percentile": 50,
                        "source": "Report",
                    }
                ]
            elif "SELECT name, status" in query:
                mock_cursor.fetchall.return_value = [
                    {
                        "name": "Similar1",
                        "status": "active",
                        "initial_funding": 1000000.0,
                        "total_funding": 5000000.0,
                        "valuation": 25000000.0,
                        "employees": 50,
                        "revenue": 3000000.0,
                    }
                ]
            elif "INSERT INTO business_ventures" in query and "RETURNING" in query:
                mock_cursor.fetchone.return_value = {"id": 999}

        mock_cursor.execute.side_effect = mock_execute
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db_config.get_connection.return_value = mock_conn

        with patch.object(ProductionBusinessDataDB, "populate_sample_data"):
            db = ProductionBusinessDataDB()

        # Test all operations
        success_rates = db.query_industry_success_rates("SaaS")
        assert success_rates["success_rate"] == 100.0

        benchmarks = db.get_industry_benchmarks("SaaS")
        assert len(benchmarks["metrics"]) == 1

        similar = db.analyze_similar_ventures("SaaS", "subscription")
        assert similar["count"] == 1

        venture_id = db.add_venture({"name": "TestVenture", "industry": "SaaS"})
        assert venture_id == "999"

    @patch("src.tools.database_production.db_config")
    @patch("src.tools.database_production.BusinessDataDB")
    def test_full_workflow_sqlite(self, mock_sqlite_db_class, mock_db_config):
        """Test complete workflow with SQLite."""
        mock_db_config.use_postgres = False
        mock_sqlite_db = Mock()

        # Mock all SQLite operations
        mock_sqlite_db.query_industry_success_rates.return_value = {
            "industry": "SaaS",
            "success_rate": 85.0,
        }
        mock_sqlite_db.get_industry_benchmarks.return_value = {"industry": "SaaS", "metrics": []}
        mock_sqlite_db.analyze_similar_ventures.return_value = {"count": 2, "success_rate": 50.0}
        mock_sqlite_db.add_venture.return_value = 456

        mock_sqlite_db_class.return_value = mock_sqlite_db

        db = ProductionBusinessDataDB()

        # Test all operations delegate to SQLite
        success_rates = db.query_industry_success_rates("SaaS")
        assert success_rates["success_rate"] == 85.0

        benchmarks = db.get_industry_benchmarks("SaaS")
        assert benchmarks["industry"] == "SaaS"

        similar = db.analyze_similar_ventures("SaaS", "subscription", "US")
        assert similar["count"] == 2

        venture_id = db.add_venture({"name": "TestVenture", "industry": "SaaS"})
        assert venture_id == "456"

    def test_executor_integration_all_operations(self):
        """Test executor integration with all operations."""
        test_cases = [
            ("success_rates", {"industry": "SaaS"}),
            ("benchmarks", {"industry": "FinTech"}),
            ("similar_ventures", {"industry": "AI", "business_model": "B2B"}),
            ("add_venture", {"venture_data": {"name": "Test", "industry": "Tech"}}),
        ]

        with patch("src.tools.database_production.ProductionBusinessDataDB") as mock_db_class:
            mock_db = Mock()
            mock_db.query_industry_success_rates.return_value = {"industry": "SaaS"}
            mock_db.get_industry_benchmarks.return_value = {"industry": "FinTech"}
            mock_db.analyze_similar_ventures.return_value = {"count": 0}
            mock_db.add_venture.return_value = "123"
            mock_db_class.return_value = mock_db

            for query_type, params in test_cases:
                result = database_tool_executor(query_type, params)
                assert isinstance(result, dict)
                if query_type == "add_venture":
                    assert result["success"] is True
                else:
                    assert "error" not in result

    @patch("src.tools.database_production.db_config")
    def test_data_type_conversion(self, mock_db_config):
        """Test proper data type conversion for PostgreSQL."""
        mock_db_config.use_postgres = True
        mock_db_config.init_database = Mock()

        # Mock connection with float values
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {
                "name": "TestCorp",
                "status": "active",
                "initial_funding": 1500000.50,
                "total_funding": 7500000.75,
                "valuation": 37500000.25,
                "employees": 75,
                "revenue": 4500000.80,
            }
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db_config.get_connection.return_value = mock_conn

        with patch.object(ProductionBusinessDataDB, "populate_sample_data"):
            db = ProductionBusinessDataDB()

        result = db.analyze_similar_ventures("SaaS", "subscription")

        venture = result["similar_ventures"][0]
        assert isinstance(venture["initial_funding"], float)
        assert isinstance(venture["total_funding"], float)
        assert isinstance(venture["valuation"], float)
        assert isinstance(venture["employees"], int)
        assert isinstance(venture["revenue"], float)
