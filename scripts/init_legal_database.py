#!/usr/bin/env python3
"""
Initialize legal compliance database for production deployment.

This script sets up the legal compliance database tables and initial data.
Run this before deploying to production.
"""

import hashlib
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.legal.legal_database import Base, LegalDatabaseManager, LegalTermsVersion

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def init_database():
    """Initialize the legal compliance database."""

    logger.info("Initializing legal compliance database...")

    # Initialize database manager
    db = LegalDatabaseManager()

    # Create all tables
    Base.metadata.create_all(db.engine)
    logger.info("Database tables created successfully")

    # Insert initial terms version
    session = db.SessionLocal()
    try:
        # Check if initial version exists
        existing = session.query(LegalTermsVersion).filter_by(version="1.0").first()

        if not existing:
            # Read current legal disclaimer
            legal_file = Path("LEGAL_DISCLAIMER.md")
            if legal_file.exists():
                content = legal_file.read_text()
                terms_hash = hashlib.sha256(content.encode()).hexdigest()
            else:
                terms_hash = hashlib.sha256(b"Initial terms").hexdigest()

            initial_version = LegalTermsVersion(
                version="1.0",
                effective_date=datetime.utcnow(),
                terms_hash=terms_hash,
                disclaimer_hash=terms_hash,
                privacy_policy_hash=hashlib.sha256(b"Privacy policy v1.0").hexdigest(),
                major_changes="Initial release of legal terms and disclaimers",
                requires_reacceptance=False,
                jurisdictions=["US", "EU", "UK", "CA"],
                minimum_age=18,
                created_by="System Administrator",
            )

            session.add(initial_version)
            session.commit()
            logger.info("Initial terms version 1.0 created")
        else:
            logger.info("Terms version 1.0 already exists")

        # Get compliance stats
        stats = db.get_compliance_stats(days=30)
        logger.info(f"Current compliance stats: {stats}")

    except Exception as e:
        session.rollback()
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        session.close()

    logger.info("Legal compliance database initialization complete!")

    # Create indexes for better performance
    logger.info("Creating additional indexes for performance...")

    # Add custom indexes if using PostgreSQL
    if "postgresql" in str(db.engine.url):
        try:
            with db.engine.connect() as conn:
                # Create partial index for active acceptances
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_active_acceptances
                    ON legal_acceptances (user_hash, terms_version)
                    WHERE revoked_at IS NULL AND expires_at > NOW()
                """
                )

                # Create index for compliance reporting
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_compliance_reporting
                    ON legal_acceptances (timestamp, terms_version, environment)
                    WHERE all_terms_accepted = true
                """
                )

                conn.commit()
                logger.info("PostgreSQL indexes created successfully")
        except Exception as e:
            logger.warning(f"Could not create custom indexes: {e}")

    return True


def verify_database():
    """Verify database is properly configured."""

    logger.info("Verifying database configuration...")

    db = LegalDatabaseManager()
    session = db.SessionLocal()

    try:
        # Test database connection
        from sqlalchemy import text

        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1, "Database connection test failed"
        logger.info("✓ Database connection successful")

        # Check tables exist
        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        required_tables = ["legal_acceptances", "legal_compliance_log", "legal_terms_versions"]

        for table in required_tables:
            assert table in tables, f"Table {table} not found"
            logger.info(f"✓ Table {table} exists")

        # Check terms version
        version = session.query(LegalTermsVersion).filter_by(version="1.0").first()
        assert version is not None, "Initial terms version not found"
        logger.info(f"✓ Terms version 1.0 found (effective: {version.effective_date})")

        logger.info("Database verification complete - all checks passed!")
        return True

    except AssertionError as e:
        logger.error(f"Database verification failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        return False
    finally:
        session.close()


def create_test_acceptance():
    """Create a test acceptance record for verification."""

    logger.info("Creating test acceptance record...")

    db = LegalDatabaseManager()

    success, acceptance_id = db.record_acceptance(
        user_identifier="test_user_001",
        session_id="test_session_001",
        ip_address="127.0.0.1",
        disclaimers=[
            "no_financial_advice",
            "no_legal_advice",
            "use_at_own_risk",
            "no_liability",
            "seek_professionals",
            "ai_limitations",
            "verify_information",
            "no_guarantee",
        ],
        terms_version="1.0",
        additional_data={
            "platform_version": "1.0",
            "user_agent": "Test Script",
            "country_code": "US",
        },
    )

    if success:
        logger.info(f"✓ Test acceptance created: {acceptance_id[:16]}...")

        # Verify retrieval
        has_acceptance, details = db.check_user_acceptance("test_user_001", "1.0")
        assert has_acceptance, "Could not retrieve test acceptance"
        logger.info("✓ Test acceptance verified successfully")

        return True
    else:
        logger.error("Failed to create test acceptance")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Initialize legal compliance database")
    parser.add_argument("--test", action="store_true", help="Create test acceptance record")
    parser.add_argument("--verify", action="store_true", help="Verify database only")

    args = parser.parse_args()

    try:
        if args.verify:
            success = verify_database()
        else:
            success = init_database()

            if success and args.test:
                success = create_test_acceptance()

        if success:
            logger.info("✅ All operations completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Operations failed!")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
