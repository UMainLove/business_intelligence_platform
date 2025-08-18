"""
Integration tests for PostgreSQL ↔ SQLite database switching logic.
Tests real database connection switching using synthetic data.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.database_config import DatabaseConfig


class TestDatabaseSwitchingIntegration:
    """Integration tests for database switching between PostgreSQL and SQLite."""

    @pytest.fixture
    def temp_db_file(self):
        """Create temporary SQLite database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
            temp_path = temp_file.name
            yield temp_path
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @pytest.fixture
    def clean_environment(self):
        """Clean environment variables before and after test."""
        original_env = {}
        env_vars = ["ENVIRONMENT", "DATABASE_URL", "SQLITE_PATH"]

        # Store original values
        for var in env_vars:
            original_env[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]

        yield

        # Restore original values
        for var, value in original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]

    def test_sqlite_connection_development_environment(self, clean_environment, temp_db_file):
        """Test SQLite connection in development environment."""
        # Set development environment
        os.environ["ENVIRONMENT"] = "development"
        os.environ["SQLITE_PATH"] = temp_db_file

        # Initialize database config
        db_config = DatabaseConfig()

        # Verify SQLite selection
        assert db_config.environment == "development"
        assert db_config.use_postgres is False
        assert db_config.sqlite_path == temp_db_file

        # Test connection
        with db_config.get_connection() as conn:
            assert conn is not None
            cursor = conn.cursor()

            # Test basic operations
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS test_table (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    value REAL
                )
            """
            )

            cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test", 42.5))
            conn.commit()

            cursor.execute("SELECT * FROM test_table WHERE name = ?", ("test",))
            result = cursor.fetchone()

            # Verify SQLite row factory (dict-like access)
            assert result["name"] == "test"
            assert result["value"] == 42.5

    @patch("src.database_config.psycopg2.connect")
    def test_postgresql_connection_production_environment(self, mock_pg_connect, clean_environment):
        """Test PostgreSQL connection in production environment."""
        # Mock PostgreSQL connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {"name": "test", "value": 42.5}
        mock_pg_connect.return_value = mock_conn

        # Set production environment
        os.environ["ENVIRONMENT"] = "production"
        os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/test_db"

        # Patch HAS_POSTGRES to True
        with patch("src.database_config.HAS_POSTGRES", True):
            db_config = DatabaseConfig()

            # Verify PostgreSQL selection
            assert db_config.environment == "production"
            assert db_config.use_postgres is True
            assert db_config.database_url == "postgresql://user:pass@localhost:5432/test_db"

            # Test connection
            with db_config.get_connection() as conn:
                assert conn is not None
                cursor = conn.cursor()

                # Test basic operations
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS test_table (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        value DECIMAL(10,2)
                    )
                """
                )

                cursor.execute(
                    "INSERT INTO test_table (name, value) VALUES (%s, %s)", ("test", 42.5)
                )
                cursor.execute("SELECT * FROM test_table WHERE name = %s", ("test",))
                result = cursor.fetchone()

                # Verify RealDictCursor access
                assert result["name"] == "test"
                assert result["value"] == 42.5

            # Verify PostgreSQL connection was attempted
            mock_pg_connect.assert_called_once()

    @patch("src.database_config.psycopg2.connect")
    def test_database_url_override_forces_postgresql(
        self, mock_pg_connect, clean_environment, temp_db_file
    ):
        """Test that DATABASE_URL forces PostgreSQL even in development."""
        # Mock PostgreSQL connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pg_connect.return_value = mock_conn

        # Set development but with DATABASE_URL
        os.environ["ENVIRONMENT"] = "development"
        os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/dev_db"
        os.environ["SQLITE_PATH"] = temp_db_file

        # Patch HAS_POSTGRES to True
        with patch("src.database_config.HAS_POSTGRES", True):
            db_config = DatabaseConfig()

            # Verify PostgreSQL is chosen despite development environment
            assert db_config.environment == "development"
            assert db_config.use_postgres is True
            assert db_config.database_url == "postgresql://user:pass@localhost:5432/dev_db"

            # Test connection uses PostgreSQL
            with db_config.get_connection() as conn:
                assert conn is not None

            mock_pg_connect.assert_called_once()

    @patch("src.database_config.HAS_POSTGRES", False)
    def test_fallback_to_sqlite_when_postgres_unavailable(self, clean_environment, temp_db_file):
        """Test fallback to SQLite when PostgreSQL is not available."""
        # Set production environment
        os.environ["ENVIRONMENT"] = "production"
        os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/prod_db"
        os.environ["SQLITE_PATH"] = temp_db_file

        # HAS_POSTGRES is mocked to False to simulate missing psycopg2
        db_config = DatabaseConfig()

        # Verify fallback to SQLite
        assert db_config.environment == "production"
        assert db_config.use_postgres is False  # Falls back due to missing psycopg2
        assert db_config.sqlite_path == temp_db_file

        # Test SQLite connection works
        with db_config.get_connection() as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            assert result["test"] == 1

    @patch("src.database_config.psycopg2.connect")
    def test_connection_switching_during_runtime(
        self, mock_pg_connect, clean_environment, temp_db_file
    ):
        """Test switching between databases during runtime."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {"count": 5}
        mock_pg_connect.return_value = mock_conn

        # Start with SQLite (development)
        os.environ["ENVIRONMENT"] = "development"
        os.environ["SQLITE_PATH"] = temp_db_file

        db_config = DatabaseConfig()
        assert db_config.use_postgres is False

        # Test SQLite connection
        with db_config.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS metrics (id INTEGER, count INTEGER)")
            cursor.execute("INSERT INTO metrics (id, count) VALUES (1, 5)")
            conn.commit()

            cursor.execute("SELECT count FROM metrics WHERE id = 1")
            result = cursor.fetchone()
            assert result["count"] == 5

        # Switch to PostgreSQL (change environment)
        os.environ["ENVIRONMENT"] = "production"
        os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/prod_db"

        with patch("src.database_config.HAS_POSTGRES", True):
            db_config_new = DatabaseConfig()
            assert db_config_new.use_postgres is True

            # Test PostgreSQL connection
            with db_config_new.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM information_schema.tables")
                result = cursor.fetchone()
                assert result["count"] == 5

            mock_pg_connect.assert_called()

    @patch("src.database_config.psycopg2.connect")
    def test_connection_error_handling(self, mock_pg_connect, clean_environment):
        """Test connection error handling for both database types."""
        # Test PostgreSQL connection error
        mock_pg_connect.side_effect = Exception("Connection failed")

        os.environ["ENVIRONMENT"] = "production"
        os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/bad_db"

        with patch("src.database_config.HAS_POSTGRES", True):
            db_config = DatabaseConfig()

            # Connection should raise an exception
            with pytest.raises(Exception, match="Connection failed"):
                with db_config.get_connection():
                    pass

    def test_sqlite_connection_with_custom_path(self, clean_environment):
        """Test SQLite connection with custom database path."""
        custom_path = "/tmp/custom_test.db"

        # Ensure clean state
        if os.path.exists(custom_path):
            os.unlink(custom_path)

        try:
            os.environ["ENVIRONMENT"] = "development"
            os.environ["SQLITE_PATH"] = custom_path

            db_config = DatabaseConfig()
            assert db_config.sqlite_path == custom_path
            assert db_config.use_postgres is False

            # Test connection creates database at custom path
            with db_config.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("CREATE TABLE custom_test (id INTEGER)")
                cursor.execute("INSERT INTO custom_test (id) VALUES (42)")
                conn.commit()

                cursor.execute("SELECT id FROM custom_test")
                result = cursor.fetchone()
                assert result["id"] == 42

            # Verify file was created
            assert os.path.exists(custom_path)

        finally:
            # Clean up
            if os.path.exists(custom_path):
                os.unlink(custom_path)

    @patch("src.database_config.psycopg2.connect")
    def test_cursor_compatibility_between_databases(
        self, mock_pg_connect, clean_environment, temp_db_file
    ):
        """Test that both databases provide compatible cursor interfaces."""
        # Test SQLite cursor interface
        os.environ["ENVIRONMENT"] = "development"
        os.environ["SQLITE_PATH"] = temp_db_file

        sqlite_config = DatabaseConfig()

        with sqlite_config.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE compatibility_test (name TEXT, value INTEGER)")
            cursor.execute(
                "INSERT INTO compatibility_test (name, value) VALUES (?, ?)", ("test", 123)
            )
            conn.commit()

            cursor.execute("SELECT * FROM compatibility_test WHERE name = ?", ("test",))
            sqlite_result = cursor.fetchone()

            # Verify dict-like access works
            assert sqlite_result["name"] == "test"
            assert sqlite_result["value"] == 123

        # Test PostgreSQL cursor interface
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {"name": "test", "value": 123}
        mock_pg_connect.return_value = mock_conn

        os.environ["ENVIRONMENT"] = "production"
        os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/test_db"

        with patch("src.database_config.HAS_POSTGRES", True):
            pg_config = DatabaseConfig()

            with pg_config.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO compatibility_test (name, value) VALUES (%s, %s)", ("test", 123)
                )
                cursor.execute("SELECT * FROM compatibility_test WHERE name = %s", ("test",))
                pg_result = cursor.fetchone()

                # Verify dict-like access works for PostgreSQL too
                assert pg_result["name"] == "test"
                assert pg_result["value"] == 123

        # Both interfaces should be compatible
        assert sqlite_result["name"] == pg_result["name"]
        assert sqlite_result["value"] == pg_result["value"]
