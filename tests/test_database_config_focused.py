"""
Focused tests for database_config.py to achieve 95%+ coverage.
"""

import pytest
import os
import sqlite3
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile

from src.database_config import DatabaseConfig, db_config


class TestDatabaseConfigInit:
    """Test DatabaseConfig initialization."""

    @patch.dict(os.environ, {}, clear=True)
    def test_init_defaults(self):
        """Test initialization with default values."""
        config = DatabaseConfig()
        
        assert config.environment == "development"
        assert config.database_url is None
        assert config.sqlite_path == "data/business_intelligence.db"
        assert config.use_postgres is False  # HAS_POSTGRES should be False in test

    @patch.dict(os.environ, {
        "ENVIRONMENT": "production",
        "DATABASE_URL": "postgresql://user:pass@localhost/db",
        "SQLITE_PATH": "/custom/path.db"
    })
    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        config = DatabaseConfig()
        
        assert config.environment == "production"
        assert config.database_url == "postgresql://user:pass@localhost/db"
        assert config.sqlite_path == "/custom/path.db"

    @patch('src.database_config.HAS_POSTGRES', True)
    @patch.dict(os.environ, {"ENVIRONMENT": "production"})
    def test_init_postgres_production(self):
        """Test PostgreSQL is used in production when available."""
        config = DatabaseConfig()
        
        assert config.use_postgres is True

    @patch('src.database_config.HAS_POSTGRES', True)
    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://test"})
    def test_init_postgres_with_url(self):
        """Test PostgreSQL is used when DATABASE_URL is provided."""
        config = DatabaseConfig()
        
        assert config.use_postgres is True

    @patch('src.database_config.HAS_POSTGRES', False)
    @patch.dict(os.environ, {"ENVIRONMENT": "production"})
    def test_init_no_postgres_available(self):
        """Test SQLite is used when PostgreSQL not available."""
        config = DatabaseConfig()
        
        assert config.use_postgres is False


class TestSQLiteConnection:
    """Test SQLite connection methods."""

    def test_get_sqlite_connection(self):
        """Test SQLite connection creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = DatabaseConfig()
            config.sqlite_path = f"{temp_dir}/test.db"
            config.use_postgres = False
            
            conn = config._get_sqlite_connection()
            
            assert isinstance(conn, sqlite3.Connection)
            assert conn.row_factory == sqlite3.Row
            conn.close()

    def test_get_connection_sqlite(self):
        """Test get_connection context manager with SQLite."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = DatabaseConfig()
            config.sqlite_path = f"{temp_dir}/test.db"
            config.use_postgres = False
            
            with config.get_connection() as conn:
                assert isinstance(conn, sqlite3.Connection)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result[0] == 1

    def test_sqlite_directory_creation(self):
        """Test that SQLite directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = DatabaseConfig()
            nested_path = f"{temp_dir}/nested/dir/test.db"
            config.sqlite_path = nested_path
            config.use_postgres = False
            
            conn = config._get_sqlite_connection()
            
            assert Path(nested_path).parent.exists()
            conn.close()


class TestPostgreSQLConnection:
    """Test PostgreSQL connection methods."""

    @patch('src.database_config.HAS_POSTGRES', False)
    def test_postgres_not_available(self):
        """Test error when PostgreSQL not available."""
        config = DatabaseConfig()
        config.use_postgres = True
        
        with pytest.raises(ImportError, match="PostgreSQL dependencies not installed"):
            config._get_postgres_connection()

    @patch('src.database_config.HAS_POSTGRES', True)
    @patch('src.database_config.psycopg2')
    def test_postgres_connection_with_url(self, mock_psycopg2):
        """Test PostgreSQL connection with existing URL."""
        mock_conn = Mock()
        mock_psycopg2.connect.return_value = mock_conn
        
        config = DatabaseConfig()
        config.database_url = "postgresql://user:pass@host:5432/db"
        config.use_postgres = True
        
        result = config._get_postgres_connection()
        
        assert result == mock_conn
        mock_psycopg2.connect.assert_called_once()

    @patch('src.database_config.HAS_POSTGRES', True)
    @patch('src.database_config.psycopg2')
    @patch.dict(os.environ, {
        "POSTGRES_HOST": "custom-host",
        "POSTGRES_PORT": "5433",
        "POSTGRES_DB": "custom_db",
        "POSTGRES_USER": "custom_user",
        "POSTGRES_PASSWORD": "custom_pass"
    })
    def test_postgres_connection_from_env(self, mock_psycopg2):
        """Test PostgreSQL connection constructed from environment variables."""
        mock_conn = Mock()
        mock_psycopg2.connect.return_value = mock_conn
        
        config = DatabaseConfig()
        config.database_url = None
        config.use_postgres = True
        
        result = config._get_postgres_connection()
        
        expected_url = "postgresql://custom_user:custom_pass@custom-host:5433/custom_db"
        assert config.database_url == expected_url
        mock_psycopg2.connect.assert_called_once()

    @patch('src.database_config.HAS_POSTGRES', True)
    @patch('src.database_config.psycopg2')
    @patch.dict(os.environ, {}, clear=True)
    def test_postgres_connection_defaults(self, mock_psycopg2):
        """Test PostgreSQL connection with default environment values."""
        mock_conn = Mock()
        mock_psycopg2.connect.return_value = mock_conn
        
        config = DatabaseConfig()
        config.database_url = None
        config.use_postgres = True
        
        result = config._get_postgres_connection()
        
        expected_url = "postgresql://bi_user:password@localhost:5432/business_intelligence"
        assert config.database_url == expected_url
        mock_psycopg2.connect.assert_called_once()

    @patch('src.database_config.HAS_POSTGRES', True)
    @patch('src.database_config.psycopg2')
    def test_get_connection_postgres(self, mock_psycopg2):
        """Test get_connection context manager with PostgreSQL."""
        mock_conn = Mock()
        mock_psycopg2.connect.return_value = mock_conn
        
        config = DatabaseConfig()
        config.database_url = "postgresql://test"
        config.use_postgres = True
        
        with config.get_connection() as conn:
            assert conn == mock_conn
        
        mock_conn.close.assert_called_once()

    @patch('src.database_config.HAS_POSTGRES', True)
    @patch('src.database_config.psycopg2')
    def test_get_connection_postgres_exception(self, mock_psycopg2):
        """Test get_connection context manager handles exceptions."""
        mock_conn = Mock()
        mock_psycopg2.connect.return_value = mock_conn
        
        config = DatabaseConfig()
        config.database_url = "postgresql://test"
        config.use_postgres = True
        
        with pytest.raises(ValueError):
            with config.get_connection() as conn:
                raise ValueError("Test exception")
        
        mock_conn.close.assert_called_once()


class TestDatabaseInitialization:
    """Test database initialization methods."""

    def test_init_database_sqlite(self):
        """Test database initialization for SQLite."""
        config = DatabaseConfig()
        config.use_postgres = False
        
        with patch.object(config, '_init_sqlite_tables') as mock_init:
            config.init_database()
            mock_init.assert_called_once()

    @patch('src.database_config.HAS_POSTGRES', True)
    def test_init_database_postgres(self):
        """Test database initialization for PostgreSQL."""
        config = DatabaseConfig()
        config.use_postgres = True
        
        with patch.object(config, '_init_postgres_tables') as mock_init:
            config.init_database()
            mock_init.assert_called_once()


class TestSQLiteTableInitialization:
    """Test SQLite table initialization."""

    def test_init_sqlite_tables(self):
        """Test SQLite table creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = DatabaseConfig()
            config.sqlite_path = f"{temp_dir}/test.db"
            config.use_postgres = False
            
            config._init_sqlite_tables()
            
            # Verify tables were created
            with config.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if tables exist
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                tables = [row[0] for row in cursor.fetchall()]
                
                expected_tables = [
                    'business_ventures',
                    'industry_benchmarks', 
                    'market_events',
                    'financial_metrics'
                ]
                
                for table in expected_tables:
                    assert table in tables

    def test_init_sqlite_tables_indexes(self):
        """Test SQLite index creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = DatabaseConfig()
            config.sqlite_path = f"{temp_dir}/test.db"
            config.use_postgres = False
            
            config._init_sqlite_tables()
            
            # Verify indexes were created
            with config.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
                )
                indexes = [row[0] for row in cursor.fetchall()]
                
                expected_indexes = [
                    'idx_ventures_industry',
                    'idx_ventures_status',
                    'idx_benchmarks_industry',
                    'idx_events_industry',
                    'idx_metrics_venture'
                ]
                
                for index in expected_indexes:
                    assert index in indexes


class TestPostgreSQLTableInitialization:
    """Test PostgreSQL table initialization."""

    @patch('src.database_config.HAS_POSTGRES', True)
    def test_init_postgres_tables(self):
        """Test PostgreSQL table creation."""
        config = DatabaseConfig()
        config.use_postgres = True
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        
        with patch.object(config, 'get_connection', return_value=mock_conn):
            config._init_postgres_tables()
        
        # Verify basic setup calls
        assert mock_cursor.execute.call_count > 0
        mock_conn.commit.assert_called_once()

    @patch('src.database_config.HAS_POSTGRES', True)
    def test_init_postgres_tables_uuid_extension(self):
        """Test PostgreSQL UUID extension creation."""
        config = DatabaseConfig()
        config.use_postgres = True
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        
        with patch.object(config, 'get_connection', return_value=mock_conn):
            config._init_postgres_tables()
        
        # Check UUID extension was created
        execute_calls = [call[0][0] for call in mock_cursor.execute.call_args_list]
        uuid_call = next((call for call in execute_calls if 'uuid-ossp' in call), None)
        assert uuid_call is not None

    @patch('src.database_config.HAS_POSTGRES', True)
    def test_init_postgres_tables_business_ventures(self):
        """Test PostgreSQL business_ventures table creation."""
        config = DatabaseConfig()
        config.use_postgres = True
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        
        with patch.object(config, 'get_connection', return_value=mock_conn):
            config._init_postgres_tables()
        
        # Check business_ventures table was created
        execute_calls = [call[0][0] for call in mock_cursor.execute.call_args_list]
        table_call = next((call for call in execute_calls if 'business_ventures' in call and 'CREATE TABLE' in call), None)
        assert table_call is not None

    @patch('src.database_config.HAS_POSTGRES', True)
    def test_init_postgres_tables_triggers(self):
        """Test PostgreSQL trigger creation."""
        config = DatabaseConfig()
        config.use_postgres = True
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        
        with patch.object(config, 'get_connection', return_value=mock_conn):
            config._init_postgres_tables()
        
        # Check trigger function was created
        execute_calls = [call[0][0] for call in mock_cursor.execute.call_args_list]
        function_call = next((call for call in execute_calls if 'update_updated_at_column' in call), None)
        assert function_call is not None
        
        # Check triggers were created for tables
        trigger_calls = [call for call in execute_calls if 'CREATE TRIGGER' in call]
        assert len(trigger_calls) >= 4  # Should have triggers for all main tables

    @patch('src.database_config.HAS_POSTGRES', True)  
    def test_init_postgres_tables_indexes(self):
        """Test PostgreSQL index creation."""
        config = DatabaseConfig()
        config.use_postgres = True
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        
        with patch.object(config, 'get_connection', return_value=mock_conn):
            config._init_postgres_tables()
        
        # Check indexes were created
        execute_calls = [call[0][0] for call in mock_cursor.execute.call_args_list]
        index_calls = [call for call in execute_calls if 'CREATE INDEX' in call]
        assert len(index_calls) >= 5  # Should have multiple indexes


class TestGlobalDatabaseConfig:
    """Test global database config instance."""

    def test_global_config_exists(self):
        """Test that global db_config instance exists."""
        assert db_config is not None
        assert isinstance(db_config, DatabaseConfig)

    def test_global_config_properties(self):
        """Test global config has expected properties."""
        assert hasattr(db_config, 'environment')
        assert hasattr(db_config, 'database_url')
        assert hasattr(db_config, 'sqlite_path')
        assert hasattr(db_config, 'use_postgres')


class TestConnectionErrorHandling:
    """Test connection error handling."""

    def test_sqlite_connection_exception_handling(self):
        """Test SQLite connection exception handling."""
        config = DatabaseConfig()
        config.use_postgres = False
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config.sqlite_path = f"{temp_dir}/test.db"
            
            with pytest.raises(ValueError):
                with config.get_connection() as conn:
                    raise ValueError("Test exception")

    @patch('src.database_config.HAS_POSTGRES', True)
    @patch('src.database_config.psycopg2')
    def test_postgres_connection_exception_handling(self, mock_psycopg2):
        """Test PostgreSQL connection exception handling."""
        mock_conn = Mock()
        mock_psycopg2.connect.return_value = mock_conn
        
        config = DatabaseConfig()
        config.database_url = "postgresql://test"
        config.use_postgres = True
        
        with pytest.raises(ValueError):
            with config.get_connection() as conn:
                raise ValueError("Test exception")
        
        mock_conn.close.assert_called_once()


class TestDatabasePathHandling:
    """Test database path handling."""

    def test_sqlite_path_normalization(self):
        """Test SQLite path handling with different formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = DatabaseConfig()
            config.sqlite_path = f"{temp_dir}//nested///path//test.db"
            config.use_postgres = False
            
            conn = config._get_sqlite_connection()
            
            # Should normalize path and create directories
            assert Path(config.sqlite_path).parent.exists()
            conn.close()

    def test_relative_sqlite_path(self):
        """Test SQLite with relative path."""
        config = DatabaseConfig()
        config.sqlite_path = "relative/path/test.db"
        config.use_postgres = False
        
        # Should work with relative paths
        conn = config._get_sqlite_connection()
        assert conn is not None
        conn.close()


class TestIntegration:
    """Test integration scenarios."""

    def test_full_sqlite_workflow(self):
        """Test complete SQLite workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = DatabaseConfig()
            config.sqlite_path = f"{temp_dir}/integration_test.db"
            config.use_postgres = False
            
            # Initialize database
            config.init_database()
            
            # Test connection and basic operations
            with config.get_connection() as conn:
                cursor = conn.cursor()
                
                # Insert test data
                cursor.execute(
                    "INSERT INTO business_ventures (name, industry, status) VALUES (?, ?, ?)",
                    ("Test Corp", "Tech", "active")
                )
                
                # Query test data
                cursor.execute(
                    "SELECT name, industry, status FROM business_ventures WHERE name = ?",
                    ("Test Corp",)
                )
                result = cursor.fetchone()
                
                assert result[0] == "Test Corp"
                assert result[1] == "Tech"  
                assert result[2] == "active"
                
                conn.commit()

    def test_environment_detection(self):
        """Test environment-based configuration."""
        test_cases = [
            ("development", False),
            ("staging", False),
            ("production", True),  # Would be True if HAS_POSTGRES was True
            ("testing", False)
        ]
        
        for env, expected_postgres in test_cases:
            with patch.dict(os.environ, {"ENVIRONMENT": env}):
                with patch('src.database_config.HAS_POSTGRES', expected_postgres):
                    config = DatabaseConfig()
                    assert config.environment == env
                    # Note: use_postgres depends on HAS_POSTGRES availability

    @patch('src.database_config.logger')
    def test_logging_configuration(self, mock_logger):
        """Test that configuration is logged properly."""
        config = DatabaseConfig()
        
        # Verify logging was called
        mock_logger.info.assert_called()
        log_call = mock_logger.info.call_args[0][0]
        assert "Database config:" in log_call
        assert "environment=" in log_call
        assert "use_postgres=" in log_call

    def test_config_properties_consistency(self):
        """Test configuration property consistency."""
        config = DatabaseConfig()
        
        # Environment and database selection should be consistent
        if config.use_postgres:
            # If using postgres, should have postgres dependencies or explicit URL
            assert config.database_url is not None or config.environment == "production"
        else:
            # If using SQLite, should have valid SQLite path
            assert config.sqlite_path is not None
            assert isinstance(config.sqlite_path, str)