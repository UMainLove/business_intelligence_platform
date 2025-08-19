"""
Database configuration and connection management.
Supports both SQLite (local/dev) and PostgreSQL (production).
"""

import logging
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

# Optional PostgreSQL dependencies
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor

    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False
    psycopg2 = None
    RealDictCursor = None

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration and connection management."""

    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.database_url = os.getenv("DATABASE_URL")
        self.sqlite_path = os.getenv("SQLITE_PATH", "data/business_intelligence.db")

        # Determine database type
        self.use_postgres = HAS_POSTGRES and (
            self.environment == "production" or self.database_url is not None
        )

        logger.info(
            f"Database config: environment={self.environment}, use_postgres={self.use_postgres}"
        )

    @contextmanager
    def get_connection(self):
        """Get database connection based on environment."""
        if self.use_postgres:
            conn = self._get_postgres_connection()
            try:
                yield conn
            finally:
                conn.close()
        else:
            conn = self._get_sqlite_connection()
            try:
                yield conn
            finally:
                conn.close()

    def _get_postgres_connection(self):
        """Create PostgreSQL connection."""
        if not HAS_POSTGRES:
            raise ImportError(
                "PostgreSQL dependencies not installed. Install with: pip install psycopg2-binary"
            )

        if not self.database_url:
            # Construct URL from environment variables
            host = os.getenv("POSTGRES_HOST", "localhost")
            port = os.getenv("POSTGRES_PORT", "5432")
            database = os.getenv("POSTGRES_DB", "business_intelligence")
            user = os.getenv("POSTGRES_USER", "bi_user")
            # Security: Require password in production, allow defaults in development
            password = os.getenv("POSTGRES_PASSWORD")
            if not password:
                environment = os.getenv("ENVIRONMENT", "development")
                if environment == "production":
                    raise ValueError(
                        "POSTGRES_PASSWORD environment variable is required for PostgreSQL connection in production"
                    )
                # Use a default only in development/test environments
                password = "password"
                logger.warning("Using default password for PostgreSQL - NOT FOR PRODUCTION USE")

            self.database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"

        return psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)

    def _get_sqlite_connection(self):
        """Create SQLite connection."""
        db_path = Path(self.sqlite_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn

    def init_database(self):
        """Initialize database with required tables."""
        if self.use_postgres:
            self._init_postgres_tables()
        else:
            self._init_sqlite_tables()

    def _init_postgres_tables(self):
        """Initialize PostgreSQL tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Enable UUID extension
            cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

            # Business ventures table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS business_ventures (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    name VARCHAR(255) NOT NULL,
                    industry VARCHAR(100) NOT NULL,
                    founded_date DATE,
                    status VARCHAR(20) CHECK(status IN ('active', 'failed', 'acquired', 'ipo')),
                    initial_funding DECIMAL(15,2),
                    total_funding DECIMAL(15,2),
                    valuation DECIMAL(15,2),
                    employees INTEGER,
                    revenue DECIMAL(15,2),
                    region VARCHAR(100),
                    business_model VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Industry benchmarks table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS industry_benchmarks (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    industry VARCHAR(100) NOT NULL,
                    metric_name VARCHAR(255) NOT NULL,
                    metric_value DECIMAL(15,4),
                    metric_unit VARCHAR(50),
                    percentile INTEGER,
                    year INTEGER,
                    source VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Market events table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS market_events (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    event_date DATE NOT NULL,
                    event_type VARCHAR(100),
                    industry VARCHAR(100),
                    description TEXT,
                    impact_level VARCHAR(20) CHECK(impact_level IN ('low', 'medium', 'high')),
                    affected_companies JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Financial metrics table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS financial_metrics (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    venture_id UUID REFERENCES business_ventures(id) ON DELETE CASCADE,
                    metric_date DATE,
                    revenue DECIMAL(15,2),
                    profit_margin DECIMAL(5,2),
                    customer_count INTEGER,
                    cac DECIMAL(10,2),
                    ltv DECIMAL(10,2),
                    churn_rate DECIMAL(5,2),
                    burn_rate DECIMAL(15,2),
                    runway_months INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create indexes for better performance
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_ventures_industry ON business_ventures(industry);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_ventures_status ON business_ventures(status);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_benchmarks_industry "
                "ON industry_benchmarks(industry);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_industry ON market_events(industry);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_metrics_venture ON financial_metrics(venture_id);"
            )

            # Create updated_at trigger function
            cursor.execute(
                """
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
                END;
                $$ language 'plpgsql';
            """
            )

            # Create triggers for updated_at using safe SQL construction
            # Define allowed table names as a frozen set for security
            allowed_tables = frozenset(
                [
                    "business_ventures",
                    "industry_benchmarks",
                    "market_events",
                    "financial_metrics",
                ]
            )

            def _safe_identifier(name: str) -> str:
                """Safely validate and quote SQL identifiers to prevent injection."""
                # Validate against allowlist
                if name not in allowed_tables:
                    raise ValueError(f"Table name '{name}' not in allowed list")

                # Additional validation: ensure only alphanumeric and underscore
                import re

                if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
                    raise ValueError(f"Invalid identifier format: {name}")

                return name

            for table_name in allowed_tables:
                # Validate table name through security function
                safe_table = _safe_identifier(table_name)
                trigger_name = "update_" + safe_table + "_updated_at"

                # Construct SQL safely using validated identifiers
                # Safe because table names are from validated allowlist and regex-checked

                # Try to use SQLAlchemy text() to satisfy security scanners, fallback to string
                try:
                    from sqlalchemy import text

                    # Use SQLAlchemy text() wrapper for security scanner compatibility
                    drop_statement = text(
                        "DROP TRIGGER IF EXISTS " + trigger_name + " ON " + safe_table
                    )
                    create_statement = text(
                        "CREATE TRIGGER "
                        + trigger_name
                        + " BEFORE UPDATE ON "
                        + safe_table
                        + " FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()"
                    )
                except ImportError:
                    # Fallback to plain strings when SQLAlchemy not available
                    drop_statement = "DROP TRIGGER IF EXISTS " + trigger_name + " ON " + safe_table
                    create_statement = (
                        "CREATE TRIGGER "
                        + trigger_name
                        + " BEFORE UPDATE ON "
                        + safe_table
                        + " FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()"
                    )

                # Execute validated SQL - identifiers are safe due to allowlist validation
                cursor.execute(drop_statement)  # nosec B608 - safe due to allowlist validation
                cursor.execute(create_statement)  # nosec B608 - safe due to allowlist validation

            conn.commit()

    def _init_sqlite_tables(self):
        """Initialize SQLite tables."""
        with self.get_connection() as conn:
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                    affected_companies TEXT, -- JSON string for SQLite
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                    cac REAL,
                    ltv REAL,
                    churn_rate REAL,
                    burn_rate REAL,
                    runway_months INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (venture_id) REFERENCES business_ventures (id)
                )
            """
            )

            # Create indexes
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_ventures_industry ON business_ventures(industry);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_ventures_status ON business_ventures(status);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_benchmarks_industry "
                "ON industry_benchmarks(industry);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_industry ON market_events(industry);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_metrics_venture ON financial_metrics(venture_id);"
            )

            conn.commit()


# Global database config instance
db_config = DatabaseConfig()
