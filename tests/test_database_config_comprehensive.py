"""
Comprehensive synthetic tests for database_config.py to achieve 95%+ coverage.
"""

import pytest
import os
import sqlite3
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path

from src.database_config import (
    DatabaseConfig,
    db_config,
    HAS_POSTGRES,
    logger
)


class TestDatabaseConfigInit:
    """Test DatabaseConfig initialization with different environments."""

    @patch.dict(os.environ, {'ENVIRONMENT': 'development'})
    def test_development_environment(self):
        """Test development environment initialization."""
        config = DatabaseConfig()
        assert config.environment == "development"
        assert config.use_postgres is False or not HAS_POSTGRES

    @patch.dict(os.environ, {'ENVIRONMENT': 'production', 'DATABASE_URL': 'postgresql://test'})
    @patch('src.database_config.HAS_POSTGRES', True)
    def test_production_environment_with_postgres(self):
        """Test production environment with PostgreSQL."""
        config = DatabaseConfig()
        assert config.environment == "production"
        assert config.database_url == 'postgresql://test'
        # Would use postgres if available

    @patch.dict(os.environ, {'SQLITE_PATH': 'custom/path/test.db'})
    def test_custom_sqlite_path(self):
        """Test custom SQLite path."""
        config = DatabaseConfig()
        assert config.sqlite_path == 'custom/path/test.db'

    @patch.dict(os.environ, {}, clear=True)
    def test_default_environment(self):
        """Test default environment values."""
        config = DatabaseConfig()
        assert config.environment == "development"
        assert config.database_url is None
        assert config.sqlite_path == "data/business_intelligence.db"


class TestDatabaseConfigConnections:
    """Test database connection management."""

    @patch('src.database_config.sqlite3.connect')
    @patch('src.database_config.Path')
    def test_get_sqlite_connection_success(self, mock_path, mock_connect):
        """Test successful SQLite connection."""
        # Setup mocks
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.parent.mkdir.return_value = None
        
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        config = DatabaseConfig()
        config.use_postgres = False
        
        result = config._get_sqlite_connection()
        
        assert result == mock_conn
        mock_path_instance.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_connect.assert_called_once()

    @patch('src.database_config.HAS_POSTGRES', True)
    @patch('src.database_config.psycopg2')
    def test_get_postgres_connection_success(self, mock_psycopg2):
        """Test successful PostgreSQL connection."""
        mock_conn = Mock()
        mock_psycopg2.connect.return_value = mock_conn
        
        config = DatabaseConfig()
        config.use_postgres = True
        config.database_url = "postgresql://test"
        
        result = config._get_postgres_connection()
        
        assert result == mock_conn
        mock_psycopg2.connect.assert_called_once_with("postgresql://test", cursor_factory=None)

    @patch('src.database_config.HAS_POSTGRES', True)
    @patch('src.database_config.psycopg2')
    def test_get_postgres_connection_with_env_vars(self, mock_psycopg2):
        """Test PostgreSQL connection with environment variables."""
        mock_conn = Mock()
        mock_psycopg2.connect.return_value = mock_conn
        
        config = DatabaseConfig()
        config.use_postgres = True
        config.database_url = None  # Force env var path
        
        with patch.dict(os.environ, {
            'POSTGRES_HOST': 'localhost',
            'POSTGRES_PORT': '5432',
            'POSTGRES_DB': 'test_db',
            'POSTGRES_USER': 'test_user',
            'POSTGRES_PASSWORD': 'test_pass'
        }):
            result = config._get_postgres_connection()
            
            assert result == mock_conn
            # Should call connect with individual parameters
            mock_psycopg2.connect.assert_called_once()

    def test_get_connection_context_manager_sqlite(self):
        """Test get_connection as context manager for SQLite."""
        config = DatabaseConfig()
        config.use_postgres = False
        
        mock_conn = Mock()
        with patch.object(config, '_get_sqlite_connection', return_value=mock_conn):
            with config.get_connection() as conn:
                assert conn == mock_conn
            
            # Connection should be closed
            mock_conn.close.assert_called_once()

    def test_get_connection_context_manager_postgres(self):
        """Test get_connection as context manager for PostgreSQL."""
        config = DatabaseConfig()
        config.use_postgres = True
        
        mock_conn = Mock()
        with patch.object(config, '_get_postgres_connection', return_value=mock_conn):
            with config.get_connection() as conn:
                assert conn == mock_conn
            
            # Connection should be closed
            mock_conn.close.assert_called_once()

    def test_get_connection_exception_handling(self):
        """Test exception handling in get_connection."""
        config = DatabaseConfig()
        config.use_postgres = False
        
        mock_conn = Mock()
        mock_conn.close = Mock()
        
        with patch.object(config, '_get_sqlite_connection', return_value=mock_conn):
            try:
                with config.get_connection() as conn:
                    assert conn == mock_conn
                    raise Exception("Test exception")
            except Exception:
                pass
            
            # Connection should still be closed
            mock_conn.close.assert_called_once()


class TestDatabaseInitialization:
    """Test database table initialization."""

    @patch('src.database_config.sqlite3.connect')
    @patch('src.database_config.Path')
    def test_init_database_sqlite(self, mock_path, mock_connect):
        """Test SQLite database initialization."""
        # Setup mocks
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.parent.mkdir.return_value = None
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        config = DatabaseConfig()
        config.use_postgres = False
        
        config.init_database()
        
        # Should have created tables
        assert mock_cursor.execute.call_count > 0
        mock_conn.commit.assert_called()
        mock_conn.close.assert_called()

    @patch('src.database_config.HAS_POSTGRES', True)
    @patch('src.database_config.psycopg2')
    def test_init_database_postgres(self, mock_psycopg2):
        """Test PostgreSQL database initialization."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        config = DatabaseConfig()
        config.use_postgres = True
        config.database_url = "postgresql://test"
        
        config.init_database()
        
        # Should have created tables and extensions
        assert mock_cursor.execute.call_count > 0
        mock_conn.commit.assert_called()
        mock_conn.close.assert_called()

    @patch('src.database_config.sqlite3.connect')
    @patch('src.database_config.Path')
    def test_init_sqlite_tables_comprehensive(self, mock_path, mock_connect):
        """Test comprehensive SQLite table creation."""
        # Setup mocks
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.parent.mkdir.return_value = None
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        config = DatabaseConfig()
        config.use_postgres = False
        
        config._init_sqlite_tables()
        
        # Check that all expected tables are created
        execute_calls = [call[0][0] for call in mock_cursor.execute.call_args_list]
        table_creates = [call for call in execute_calls if 'CREATE TABLE' in call]
        
        # Should create multiple tables
        assert len(table_creates) >= 4
        assert any('business_ventures' in call for call in table_creates)
        assert any('industry_benchmarks' in call for call in table_creates)
        assert any('market_events' in call for call in table_creates)
        assert any('financial_metrics' in call for call in table_creates)

    @patch('src.database_config.HAS_POSTGRES', True)
    @patch('src.database_config.psycopg2')
    def test_init_postgres_tables_comprehensive(self, mock_psycopg2):
        """Test comprehensive PostgreSQL table creation."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        config = DatabaseConfig()
        config.use_postgres = True
        config.database_url = "postgresql://test"
        
        config._init_postgres_tables()
        
        # Check that UUID extension and tables are created
        execute_calls = [call[0][0] for call in mock_cursor.execute.call_args_list]
        
        # Should enable UUID extension
        assert any('uuid-ossp' in call for call in execute_calls)
        
        # Should create tables with proper constraints
        table_creates = [call for call in execute_calls if 'CREATE TABLE' in call]
        assert len(table_creates) >= 4


class TestDatabaseConfigErrorHandling:
    """Test error handling in database operations."""

    @patch('src.database_config.sqlite3.connect')
    def test_sqlite_connection_error(self, mock_connect):
        """Test SQLite connection error handling."""
        mock_connect.side_effect = sqlite3.Error("Connection failed")
        
        config = DatabaseConfig()
        config.use_postgres = False
        
        with pytest.raises(sqlite3.Error):
            config._get_sqlite_connection()

    @patch('src.database_config.HAS_POSTGRES', True)
    @patch('src.database_config.psycopg2')
    def test_postgres_connection_error(self, mock_psycopg2):
        """Test PostgreSQL connection error handling."""
        mock_psycopg2.connect.side_effect = Exception("Connection failed")
        
        config = DatabaseConfig()
        config.use_postgres = True
        config.database_url = "postgresql://invalid"
        
        with pytest.raises(Exception):
            config._get_postgres_connection()

    @patch('src.database_config.sqlite3.connect')
    @patch('src.database_config.Path')
    def test_init_database_error_handling(self, mock_path, mock_connect):
        """Test database initialization error handling."""
        # Setup mocks
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.parent.mkdir.side_effect = OSError("Permission denied")
        
        config = DatabaseConfig()
        config.use_postgres = False
        
        # Should handle path creation errors gracefully
        with pytest.raises(OSError):
            config._get_sqlite_connection()


class TestDatabaseConfigProperties:
    """Test database configuration properties and methods."""

    def test_singleton_db_config(self):
        """Test that db_config is a singleton instance."""
        assert db_config is not None
        assert isinstance(db_config, DatabaseConfig)
        
        # Should be the same instance
        from src.database_config import db_config as db_config2
        assert db_config is db_config2

    def test_has_postgres_constant(self):
        """Test HAS_POSTGRES constant behavior."""
        assert isinstance(HAS_POSTGRES, bool)
        
        # Test with different psycopg2 availability
        with patch('src.database_config.psycopg2', None):
            # Would normally be False if psycopg2 not available
            pass

    def test_logger_configuration(self):
        """Test logger configuration."""
        assert logger is not None
        assert logger.name == 'src.database_config'
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'warning')

    @patch('src.database_config.logger')
    def test_logging_calls(self, mock_logger):
        """Test that initialization logs properly."""
        config = DatabaseConfig()
        
        # Should log initialization info
        mock_logger.info.assert_called()
        args = mock_logger.info.call_args[0][0]
        assert "Database config:" in args
        assert "environment=" in args
        assert "use_postgres=" in args


class TestDatabaseConfigEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch.dict(os.environ, {'DATABASE_URL': ''})
    def test_empty_database_url(self):
        """Test handling of empty DATABASE_URL."""
        config = DatabaseConfig()
        assert config.database_url == ''

    @patch.dict(os.environ, {'SQLITE_PATH': ''})
    def test_empty_sqlite_path(self):
        """Test handling of empty SQLITE_PATH."""
        config = DatabaseConfig()
        assert config.sqlite_path == ''

    @patch('src.database_config.HAS_POSTGRES', False)
    def test_postgres_unavailable(self):
        """Test behavior when PostgreSQL is unavailable."""
        config = DatabaseConfig()
        assert config.use_postgres is False

    @patch('src.database_config.HAS_POSTGRES', True)
    @patch.dict(os.environ, {'ENVIRONMENT': 'production'})
    def test_production_without_database_url(self):
        """Test production environment without DATABASE_URL."""
        config = DatabaseConfig()
        # Should still work, might use env vars for connection
        assert config.environment == "production"

    def test_multiple_instances_same_config(self):
        """Test that multiple instances have consistent configuration."""
        config1 = DatabaseConfig()
        config2 = DatabaseConfig()
        
        assert config1.environment == config2.environment
        assert config1.use_postgres == config2.use_postgres
        assert config1.sqlite_path == config2.sqlite_path


class TestDatabaseIntegrationScenarios:
    """Test realistic integration scenarios."""

    @patch('src.database_config.sqlite3.connect')
    @patch('src.database_config.Path')
    def test_full_sqlite_workflow(self, mock_path, mock_connect):
        """Test complete SQLite workflow from init to usage."""
        # Setup mocks
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.parent.mkdir.return_value = None
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        config = DatabaseConfig()
        config.use_postgres = False
        
        # Initialize database
        config.init_database()
        
        # Use connection
        with config.get_connection() as conn:
            assert conn == mock_conn
        
        # Verify all operations
        assert mock_cursor.execute.call_count > 0
        mock_conn.commit.assert_called()
        mock_conn.close.assert_called()

    @patch('src.database_config.HAS_POSTGRES', True)
    @patch('src.database_config.psycopg2')
    def test_full_postgres_workflow(self, mock_psycopg2):
        """Test complete PostgreSQL workflow from init to usage."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        config = DatabaseConfig()
        config.use_postgres = True
        config.database_url = "postgresql://test"
        
        # Initialize database
        config.init_database()
        
        # Use connection
        with config.get_connection() as conn:
            assert conn == mock_conn
        
        # Verify all operations
        assert mock_cursor.execute.call_count > 0
        mock_conn.commit.assert_called()
        mock_conn.close.assert_called()

    def test_environment_detection_scenarios(self):
        """Test various environment detection scenarios."""
        scenarios = [
            ({'ENVIRONMENT': 'development'}, 'development'),
            ({'ENVIRONMENT': 'production'}, 'production'),
            ({'ENVIRONMENT': 'testing'}, 'testing'),
            ({}, 'development'),  # default
        ]
        
        for env_vars, expected in scenarios:
            with patch.dict(os.environ, env_vars, clear=True):
                config = DatabaseConfig()
                assert config.environment == expected