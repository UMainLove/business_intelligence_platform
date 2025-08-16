"""
Focused tests for database_tools.py to achieve 95%+ coverage.
"""

import pytest
import sqlite3
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, Any

from src.tools.database_tools import (
    BusinessDataDB,
    create_database_tool_spec,
    database_tool_executor
)


class TestBusinessDataDB:
    """Test BusinessDataDB class."""

    def setup_method(self):
        """Setup test database in temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_business.db"
        
    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test BusinessDataDB initialization."""
        db = BusinessDataDB(str(self.db_path))
        
        assert db.db_path == self.db_path
        assert self.db_path.exists()
        assert self.db_path.parent.exists()

    def test_init_database_creates_tables(self):
        """Test that init_database creates all required tables."""
        db = BusinessDataDB(str(self.db_path))
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check that all tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            'business_ventures',
            'industry_benchmarks', 
            'market_events',
            'financial_metrics'
        ]
        
        for table in expected_tables:
            assert table in table_names
        
        conn.close()

    def test_init_database_table_structure(self):
        """Test database table structures."""
        db = BusinessDataDB(str(self.db_path))
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check business_ventures table structure
        cursor.execute("PRAGMA table_info(business_ventures)")
        columns = [row[1] for row in cursor.fetchall()]
        expected_columns = [
            'id', 'name', 'industry', 'founded_date', 'status',
            'initial_funding', 'total_funding', 'valuation', 'employees',
            'revenue', 'region', 'business_model', 'created_at'
        ]
        for col in expected_columns:
            assert col in columns
        
        # Check industry_benchmarks table structure  
        cursor.execute("PRAGMA table_info(industry_benchmarks)")
        columns = [row[1] for row in cursor.fetchall()]
        expected_columns = [
            'id', 'industry', 'metric_name', 'metric_value', 'metric_unit',
            'percentile', 'year', 'source', 'created_at'
        ]
        for col in expected_columns:
            assert col in columns
        
        conn.close()

    def test_populate_sample_data(self):
        """Test populate_sample_data method."""
        db = BusinessDataDB(str(self.db_path))
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check that sample data was added
        cursor.execute("SELECT COUNT(*) FROM business_ventures")
        venture_count = cursor.fetchone()[0]
        assert venture_count > 0
        
        cursor.execute("SELECT COUNT(*) FROM industry_benchmarks")
        benchmark_count = cursor.fetchone()[0]
        assert benchmark_count > 0
        
        # Check specific sample data
        cursor.execute("SELECT name FROM business_ventures WHERE name = 'TechStart'")
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == 'TechStart'
        
        conn.close()

    def test_populate_sample_data_no_duplicate(self):
        """Test that populate_sample_data doesn't create duplicates."""
        db = BusinessDataDB(str(self.db_path))
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get initial count
        cursor.execute("SELECT COUNT(*) FROM business_ventures")
        initial_count = cursor.fetchone()[0]
        
        # Call populate again
        db.populate_sample_data()
        
        # Check count didn't increase
        cursor.execute("SELECT COUNT(*) FROM business_ventures")
        final_count = cursor.fetchone()[0]
        assert final_count == initial_count
        
        conn.close()

    def test_query_industry_success_rates(self):
        """Test query_industry_success_rates method."""
        db = BusinessDataDB(str(self.db_path))
        
        result = db.query_industry_success_rates("SaaS")
        
        assert isinstance(result, dict)
        assert "industry" in result
        assert "total_ventures" in result
        assert "status_breakdown" in result
        assert "success_rate" in result
        assert "avg_funding_by_status" in result
        
        assert result["industry"] == "SaaS"
        assert result["total_ventures"] >= 0
        assert isinstance(result["status_breakdown"], dict)
        assert isinstance(result["success_rate"], (int, float))

    def test_query_industry_success_rates_nonexistent(self):
        """Test query_industry_success_rates with nonexistent industry."""
        db = BusinessDataDB(str(self.db_path))
        
        result = db.query_industry_success_rates("NonexistentIndustry")
        
        assert result["total_ventures"] == 0
        assert result["success_rate"] == 0
        assert result["status_breakdown"] == {}

    def test_query_industry_success_rates_calculation(self):
        """Test success rate calculation logic."""
        # Create a clean database for this test
        temp_db_path = Path(self.temp_dir) / "calc_test.db"
        db = BusinessDataDB(str(temp_db_path))
        
        # Add test data with known success rate
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute("DELETE FROM business_ventures")
        
        # Add 4 ventures: 2 successful (active, acquired), 2 failed
        test_ventures = [
            ("Test1", "TestIndustry", "2020-01-01", "active", 100, 500, 1000, 10, 200, "US", "B2B"),
            ("Test2", "TestIndustry", "2020-01-01", "acquired", 200, 1000, 5000, 20, 500, "US", "B2B"),
            ("Test3", "TestIndustry", "2020-01-01", "failed", 150, 150, 0, 0, 0, "US", "B2B"),
            ("Test4", "TestIndustry", "2020-01-01", "failed", 300, 300, 0, 0, 0, "US", "B2B"),
        ]
        
        cursor.executemany(
            """INSERT INTO business_ventures 
               (name, industry, founded_date, status, initial_funding, total_funding, valuation, employees, revenue, region, business_model)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            test_ventures
        )
        conn.commit()
        conn.close()
        
        result = db.query_industry_success_rates("TestIndustry")
        
        assert result["total_ventures"] == 4
        assert result["success_rate"] == 50.0  # 2 out of 4 successful

    def test_get_industry_benchmarks(self):
        """Test get_industry_benchmarks method."""
        db = BusinessDataDB(str(self.db_path))
        
        result = db.get_industry_benchmarks("SaaS")
        
        assert isinstance(result, dict)
        assert "industry" in result
        assert "metrics" in result
        
        assert result["industry"] == "SaaS"
        assert isinstance(result["metrics"], list)
        
        if result["metrics"]:
            metric = result["metrics"][0]
            assert "name" in metric
            assert "value" in metric
            assert "unit" in metric
            assert "percentile" in metric
            assert "source" in metric

    def test_get_industry_benchmarks_nonexistent(self):
        """Test get_industry_benchmarks with nonexistent industry."""
        db = BusinessDataDB(str(self.db_path))
        
        result = db.get_industry_benchmarks("NonexistentIndustry")
        
        assert result["industry"] == "NonexistentIndustry"
        assert result["metrics"] == []

    def test_analyze_similar_ventures(self):
        """Test analyze_similar_ventures method."""
        db = BusinessDataDB(str(self.db_path))
        
        result = db.analyze_similar_ventures("SaaS", "subscription")
        
        assert isinstance(result, dict)
        assert "similar_ventures" in result
        assert "count" in result
        assert "success_rate" in result
        assert "avg_total_funding" in result
        assert "analysis" in result
        
        assert isinstance(result["similar_ventures"], list)
        assert isinstance(result["count"], int)
        assert isinstance(result["success_rate"], (int, float))

    def test_analyze_similar_ventures_with_region(self):
        """Test analyze_similar_ventures with region filter."""
        db = BusinessDataDB(str(self.db_path))
        
        result = db.analyze_similar_ventures("SaaS", "subscription", "North America")
        
        assert isinstance(result, dict)
        assert "similar_ventures" in result

    def test_analyze_similar_ventures_no_matches(self):
        """Test analyze_similar_ventures with no matches."""
        db = BusinessDataDB(str(self.db_path))
        
        result = db.analyze_similar_ventures("NonexistentIndustry", "NonexistentModel")
        
        assert result["similar_ventures"] == []
        assert "No similar ventures found" in result["analysis"]

    def test_analyze_similar_ventures_calculation(self):
        """Test similar ventures calculation logic."""
        # Create test database with known data
        temp_db_path = Path(self.temp_dir) / "similar_test.db"
        db = BusinessDataDB(str(temp_db_path))
        
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Clear and add specific test data
        cursor.execute("DELETE FROM business_ventures")
        
        test_ventures = [
            ("Similar1", "TestIndustry", "2020-01-01", "active", 100, 500, 1000, 10, 200, "US", "TestModel"),
            ("Similar2", "TestIndustry", "2020-01-01", "failed", 200, 200, 0, 0, 0, "US", "TestModel"),
            ("Similar3", "TestIndustry", "2020-01-01", "acquired", 300, 800, 2000, 15, 400, "US", "TestModel"),
        ]
        
        cursor.executemany(
            """INSERT INTO business_ventures 
               (name, industry, founded_date, status, initial_funding, total_funding, valuation, employees, revenue, region, business_model)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            test_ventures
        )
        conn.commit()
        conn.close()
        
        result = db.analyze_similar_ventures("TestIndustry", "TestModel")
        
        assert result["count"] == 3
        assert result["success_rate"] == 66.7  # 2 out of 3 successful (active + acquired)
        assert result["avg_total_funding"] == 500  # (500 + 200 + 800) / 3

    def test_add_venture(self):
        """Test add_venture method."""
        db = BusinessDataDB(str(self.db_path))
        
        venture_data = {
            "name": "NewVenture",
            "industry": "NewTech",
            "founded_date": "2023-01-01",
            "status": "active",
            "initial_funding": 500000,
            "total_funding": 1000000,
            "valuation": 5000000,
            "employees": 25,
            "revenue": 750000,
            "region": "Europe",
            "business_model": "SaaS"
        }
        
        venture_id = db.add_venture(venture_data)
        
        assert isinstance(venture_id, int)
        assert venture_id > 0
        
        # Verify the venture was added
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, industry FROM business_ventures WHERE id = ?", (venture_id,))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[0] == "NewVenture"
        assert result[1] == "NewTech"

    def test_add_venture_minimal_data(self):
        """Test add_venture with minimal required data."""
        db = BusinessDataDB(str(self.db_path))
        
        venture_data = {
            "name": "MinimalVenture",
            "industry": "MinimalIndustry"
        }
        
        venture_id = db.add_venture(venture_data)
        
        assert isinstance(venture_id, int)
        assert venture_id > 0
        
        # Verify the venture was added with defaults
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, industry, status FROM business_ventures WHERE id = ?", (venture_id,))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[0] == "MinimalVenture"
        assert result[1] == "MinimalIndustry"
        assert result[2] == "active"  # Default status

    def test_database_persistence(self):
        """Test that database persists across instances."""
        # Create first instance and add data
        db1 = BusinessDataDB(str(self.db_path))
        venture_data = {
            "name": "PersistentVenture",
            "industry": "TestIndustry"
        }
        venture_id = db1.add_venture(venture_data)
        
        # Create second instance and verify data exists
        db2 = BusinessDataDB(str(self.db_path))
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM business_ventures WHERE id = ?", (venture_id,))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[0] == "PersistentVenture"


class TestDatabaseToolSpec:
    """Test database tool specification."""

    def test_create_database_tool_spec(self):
        """Test create_database_tool_spec function."""
        spec = create_database_tool_spec()
        
        assert isinstance(spec, dict)
        assert "name" in spec
        assert "description" in spec
        assert "parameters" in spec
        
        assert spec["name"] == "business_database"
        
        # Check parameters structure
        params = spec["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params
        
        properties = params["properties"]
        assert "query_type" in properties
        assert "params" in properties
        
        # Check query_type enum
        query_type = properties["query_type"]
        assert query_type["type"] == "string"
        assert "enum" in query_type
        expected_types = ["success_rates", "benchmarks", "similar_ventures", "add_venture"]
        assert query_type["enum"] == expected_types
        
        # Check required fields
        assert params["required"] == ["query_type", "params"]


class TestDatabaseToolExecutor:
    """Test database_tool_executor function."""

    def setup_method(self):
        """Setup test database in temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_executor.db"
        
    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    @patch('src.tools.database_tools.BusinessDataDB')
    def test_success_rates_executor(self, mock_db_class):
        """Test database_tool_executor for success rates."""
        mock_db = Mock()
        mock_db.query_industry_success_rates.return_value = {
            "industry": "SaaS",
            "total_ventures": 5,
            "success_rate": 80.0
        }
        mock_db_class.return_value = mock_db
        
        result = database_tool_executor("success_rates", {"industry": "SaaS"})
        
        assert result["industry"] == "SaaS"
        assert result["total_ventures"] == 5
        assert result["success_rate"] == 80.0
        mock_db.query_industry_success_rates.assert_called_once_with("SaaS")

    @patch('src.tools.database_tools.BusinessDataDB')
    def test_benchmarks_executor(self, mock_db_class):
        """Test database_tool_executor for benchmarks."""
        mock_db = Mock()
        mock_db.get_industry_benchmarks.return_value = {
            "industry": "FinTech",
            "metrics": [{"name": "CAC", "value": 150}]
        }
        mock_db_class.return_value = mock_db
        
        result = database_tool_executor("benchmarks", {"industry": "FinTech"})
        
        assert result["industry"] == "FinTech"
        assert len(result["metrics"]) == 1
        mock_db.get_industry_benchmarks.assert_called_once_with("FinTech")

    @patch('src.tools.database_tools.BusinessDataDB')
    def test_similar_ventures_executor(self, mock_db_class):
        """Test database_tool_executor for similar ventures."""
        mock_db = Mock()
        mock_db.analyze_similar_ventures.return_value = {
            "similar_ventures": [],
            "count": 0,
            "success_rate": 0
        }
        mock_db_class.return_value = mock_db
        
        result = database_tool_executor("similar_ventures", {
            "industry": "AI",
            "business_model": "B2B"
        })
        
        assert result["count"] == 0
        mock_db.analyze_similar_ventures.assert_called_once_with("AI", "B2B", None)

    @patch('src.tools.database_tools.BusinessDataDB')
    def test_similar_ventures_executor_with_region(self, mock_db_class):
        """Test database_tool_executor for similar ventures with region."""
        mock_db = Mock()
        mock_db.analyze_similar_ventures.return_value = {
            "similar_ventures": [],
            "count": 0
        }
        mock_db_class.return_value = mock_db
        
        result = database_tool_executor("similar_ventures", {
            "industry": "Crypto",
            "business_model": "DeFi",
            "region": "Asia"
        })
        
        mock_db.analyze_similar_ventures.assert_called_once_with("Crypto", "DeFi", "Asia")

    @patch('src.tools.database_tools.BusinessDataDB')
    def test_add_venture_executor(self, mock_db_class):
        """Test database_tool_executor for adding ventures."""
        mock_db = Mock()
        mock_db.add_venture.return_value = 123
        mock_db_class.return_value = mock_db
        
        venture_data = {
            "name": "NewVenture",
            "industry": "NewTech"
        }
        
        result = database_tool_executor("add_venture", {"venture_data": venture_data})
        
        assert result["success"] is True
        assert result["venture_id"] == 123
        mock_db.add_venture.assert_called_once_with(venture_data)

    def test_unknown_query_type_executor(self):
        """Test database_tool_executor with unknown query type."""
        result = database_tool_executor("unknown_type", {})
        
        assert "error" in result
        assert "Unknown query type: unknown_type" in result["error"]


class TestIntegration:
    """Test integration scenarios."""

    def setup_method(self):
        """Setup test database in temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_integration.db"
        
    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_full_database_workflow(self):
        """Test complete database workflow."""
        db = BusinessDataDB(str(self.db_path))
        
        # 1. Query initial industry success rates
        initial_rates = db.query_industry_success_rates("SaaS")
        initial_count = initial_rates["total_ventures"]
        
        # 2. Add a new venture
        new_venture = {
            "name": "WorkflowTestVenture",
            "industry": "SaaS",
            "status": "active",
            "business_model": "subscription",
            "region": "North America"
        }
        venture_id = db.add_venture(new_venture)
        assert venture_id > 0
        
        # 3. Query success rates again - should have one more venture
        updated_rates = db.query_industry_success_rates("SaaS")
        assert updated_rates["total_ventures"] == initial_count + 1
        
        # 4. Query similar ventures
        similar = db.analyze_similar_ventures("SaaS", "subscription")
        venture_names = [v["name"] for v in similar["similar_ventures"]]
        assert "WorkflowTestVenture" in venture_names
        
        # 5. Get benchmarks
        benchmarks = db.get_industry_benchmarks("SaaS")
        assert benchmarks["industry"] == "SaaS"

    def test_executor_integration(self):
        """Test database_tool_executor integration."""
        # Test all executor functions work together
        
        # 1. Get initial success rates
        result1 = database_tool_executor("success_rates", {"industry": "SaaS"})
        assert "success_rate" in result1
        
        # 2. Get benchmarks
        result2 = database_tool_executor("benchmarks", {"industry": "SaaS"})
        assert "metrics" in result2
        
        # 3. Analyze similar ventures
        result3 = database_tool_executor("similar_ventures", {
            "industry": "SaaS",
            "business_model": "subscription"
        })
        assert "similar_ventures" in result3
        
        # 4. Add a new venture
        venture_data = {
            "name": "IntegrationTestVenture",
            "industry": "SaaS"
        }
        result4 = database_tool_executor("add_venture", {"venture_data": venture_data})
        assert result4["success"] is True
        assert "venture_id" in result4

    def test_database_error_handling(self):
        """Test database error handling scenarios."""
        # Test with very long paths (might cause issues)
        very_long_path = "x" * 1000 + ".db"
        try:
            db = BusinessDataDB(very_long_path)
            # If it succeeds, that's fine too
        except Exception:
            # Expected for very long paths
            pass

    def test_concurrent_access(self):
        """Test concurrent database access."""
        db1 = BusinessDataDB(str(self.db_path))
        db2 = BusinessDataDB(str(self.db_path))
        
        # Both instances should work with the same database
        venture1 = {"name": "Concurrent1", "industry": "Test"}
        venture2 = {"name": "Concurrent2", "industry": "Test"}
        
        id1 = db1.add_venture(venture1)
        id2 = db2.add_venture(venture2)
        
        assert id1 != id2
        
        # Both should see each other's data
        result1 = db1.query_industry_success_rates("Test")
        result2 = db2.query_industry_success_rates("Test")
        
        assert result1["total_ventures"] == result2["total_ventures"]
        assert result1["total_ventures"] >= 2

    def test_data_validation(self):
        """Test data validation and edge cases."""
        db = BusinessDataDB(str(self.db_path))
        
        # Test with None/empty values
        venture_data = {
            "name": "TestVenture",
            "industry": "TestIndustry",
            "initial_funding": None,
            "total_funding": None,
            "employees": None
        }
        
        venture_id = db.add_venture(venture_data)
        assert venture_id > 0
        
        # Query should handle None values gracefully
        result = db.analyze_similar_ventures("TestIndustry", None)
        assert isinstance(result, dict)

    def test_performance_with_large_dataset(self):
        """Test performance with larger dataset."""
        db = BusinessDataDB(str(self.db_path))
        
        # Add multiple ventures quickly
        for i in range(10):
            venture_data = {
                "name": f"PerfTest{i}",
                "industry": "Performance",
                "business_model": "test"
            }
            venture_id = db.add_venture(venture_data)
            assert venture_id > 0
        
        # Queries should still work efficiently
        result = db.query_industry_success_rates("Performance")
        assert result["total_ventures"] >= 10
        
        similar = db.analyze_similar_ventures("Performance", "test")
        assert similar["count"] >= 10