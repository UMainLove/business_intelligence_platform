"""
Database management for legal acceptances and compliance tracking.

This module provides persistent storage of user legal agreements with full audit capabilities.
"""

import hashlib
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    create_engine,
    func,
    or_,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import sessionmaker

Base: DeclarativeMeta = declarative_base()
logger = logging.getLogger(__name__)


class LegalAcceptance(Base):  # type: ignore
    """Database model for tracking legal acceptance records."""

    __tablename__ = "legal_acceptances"

    # Primary identification
    id = Column(Integer, primary_key=True, autoincrement=True)
    acceptance_id = Column(String(64), unique=True, nullable=False, index=True)

    # User identification (anonymized)
    user_hash = Column(String(64), nullable=False, index=True)  # Hashed user identifier
    session_hash = Column(String(64), nullable=False, index=True)  # Session identifier
    ip_hash = Column(String(64), nullable=False)  # Hashed IP for geographic compliance

    # Acceptance details
    timestamp = Column(DateTime, nullable=False, index=True)
    terms_version = Column(String(20), nullable=False, index=True)  # Version of terms accepted
    acceptance_type = Column(String(50), nullable=False)  # 'initial', 'renewal', 'update'

    # Specific disclaimers acknowledged (JSON array)
    disclaimers_accepted = Column(JSON, nullable=False)

    # Acceptance verification
    all_terms_accepted = Column(Boolean, nullable=False, default=False)
    acceptance_method = Column(String(50), nullable=False)  # 'checkbox', 'button', 'signature'

    # Additional metadata
    user_agent_hash = Column(String(64))  # Browser fingerprint
    country_code = Column(String(2))  # For jurisdiction tracking
    language = Column(String(5), default="en")

    # Platform details
    platform_version = Column(String(20))
    environment = Column(String(20))  # 'development', 'staging', 'production'

    # Consent specifics
    data_processing_consent = Column(Boolean, default=False)
    marketing_consent = Column(Boolean, default=False)
    third_party_sharing_consent = Column(Boolean, default=False)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # When re-acceptance needed
    revoked_at = Column(DateTime)  # If user revokes consent
    revocation_reason = Column(Text)

    __table_args__ = (
        Index("idx_user_timestamp", "user_hash", "timestamp"),
        Index("idx_version_timestamp", "terms_version", "timestamp"),
        Index("idx_acceptance_expires", "expires_at"),
    )


class LegalComplianceLog(Base):  # type: ignore
    """Audit log for all legal-related events."""

    __tablename__ = "legal_compliance_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), unique=True, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)

    # Event details
    event_type = Column(
        String(50), nullable=False, index=True
    )  # 'acceptance', 'rejection', 'revocation', 'update'
    user_hash = Column(String(64), index=True)
    session_hash = Column(String(64))

    # Event data
    event_data = Column(JSON)
    ip_hash = Column(String(64))
    user_agent_hash = Column(String(64))

    # Compliance tracking
    compliance_status = Column(String(20))  # 'compliant', 'non_compliant', 'pending'
    risk_level = Column(String(20))  # 'low', 'medium', 'high'

    __table_args__ = (
        Index("idx_event_user", "event_type", "user_hash"),
        Index("idx_compliance_timestamp", "compliance_status", "timestamp"),
    )


class LegalTermsVersion(Base):  # type: ignore
    """Track different versions of legal terms."""

    __tablename__ = "legal_terms_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(20), unique=True, nullable=False, index=True)

    # Version details
    effective_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime)

    # Content hashes for integrity
    terms_hash = Column(String(64), nullable=False)  # SHA-256 of terms content
    disclaimer_hash = Column(String(64), nullable=False)
    privacy_policy_hash = Column(String(64))

    # Version metadata
    major_changes = Column(Text)  # Description of changes
    requires_reacceptance = Column(Boolean, default=False)

    # Compliance requirements
    jurisdictions = Column(JSON)  # List of applicable jurisdictions
    minimum_age = Column(Integer, default=18)

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))


class LegalDatabaseManager:
    """Manager class for legal compliance database operations."""

    def __init__(self, database_url: Optional[str] = None):
        """Initialize database connection.

        Args:
            database_url: SQLAlchemy database URL. Defaults to PostgreSQL or SQLite.
        """
        if database_url is None:
            # Try PostgreSQL first, fall back to SQLite
            env_url = os.getenv("DATABASE_URL")
            if env_url:
                database_url = env_url
            else:
                # Use SQLite for local development
                db_path = Path("data/legal_compliance.db")
                db_path.parent.mkdir(parents=True, exist_ok=True)
                database_url = f"sqlite:///{db_path}"

        self.engine = create_engine(
            database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Verify connections before use
            echo=False,
        )

        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)

        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def record_acceptance(
        self,
        user_identifier: str,
        session_id: str,
        ip_address: str,
        disclaimers: List[str],
        terms_version: str = "1.0",
        additional_data: Optional[Dict] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Record user's acceptance of legal terms.

        Args:
            user_identifier: Unique user identifier (will be hashed)
            session_id: Session identifier
            ip_address: User's IP address (will be hashed)
            disclaimers: List of accepted disclaimer keys
            terms_version: Version of terms accepted
            additional_data: Optional additional metadata

        Returns:
            Tuple of (success, acceptance_id or error message)
        """
        session = self.SessionLocal()
        try:
            # Generate hashes for privacy
            user_hash = hashlib.sha256(user_identifier.encode()).hexdigest()
            session_hash = hashlib.sha256(session_id.encode()).hexdigest()
            ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()
            acceptance_id = hashlib.sha256(
                f"{user_hash}{session_hash}{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()

            # Create acceptance record
            acceptance = LegalAcceptance(
                acceptance_id=acceptance_id,
                user_hash=user_hash,
                session_hash=session_hash,
                ip_hash=ip_hash,
                timestamp=datetime.utcnow(),
                terms_version=terms_version,
                acceptance_type="initial",
                disclaimers_accepted=disclaimers,
                all_terms_accepted=True,
                acceptance_method="checkbox",
                platform_version=(
                    additional_data.get("platform_version", "1.0") if additional_data else "1.0"
                ),
                environment=os.getenv("ENVIRONMENT", "development"),
                expires_at=datetime.utcnow() + timedelta(days=365),  # 1 year validity
                data_processing_consent=True,
                country_code=additional_data.get("country_code") if additional_data else None,
                user_agent_hash=(
                    hashlib.sha256(additional_data.get("user_agent", "").encode()).hexdigest()
                    if additional_data
                    else None
                ),
            )

            session.add(acceptance)

            # Log the event
            event = LegalComplianceLog(
                event_id=hashlib.sha256(f"accept_{acceptance_id}".encode()).hexdigest(),
                timestamp=datetime.utcnow(),
                event_type="acceptance",
                user_hash=user_hash,
                session_hash=session_hash,
                event_data={
                    "terms_version": terms_version,
                    "disclaimers": disclaimers,
                    "acceptance_id": acceptance_id,
                },
                ip_hash=ip_hash,
                compliance_status="compliant",
                risk_level="low",
            )

            session.add(event)
            session.commit()

            logger.info(f"Legal acceptance recorded: {acceptance_id[:8]}...")
            return True, acceptance_id

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error recording acceptance: {e}")
            return False, str(e)
        finally:
            session.close()

    def check_user_acceptance(
        self, user_identifier: str, terms_version: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict]]:
        """Check if user has valid acceptance on file.

        Args:
            user_identifier: User identifier to check
            terms_version: Specific version to check (None for latest)

        Returns:
            Tuple of (has_valid_acceptance, acceptance_details)
        """
        session = self.SessionLocal()
        try:
            user_hash = hashlib.sha256(user_identifier.encode()).hexdigest()

            query = session.query(LegalAcceptance).filter(
                LegalAcceptance.user_hash == user_hash,
                LegalAcceptance.all_terms_accepted,
                LegalAcceptance.revoked_at.is_(None),
                or_(
                    LegalAcceptance.expires_at.is_(None),
                    LegalAcceptance.expires_at > datetime.utcnow(),
                ),
            )

            if terms_version:
                query = query.filter(LegalAcceptance.terms_version == terms_version)

            acceptance = query.order_by(LegalAcceptance.timestamp.desc()).first()

            if acceptance:
                return True, {
                    "acceptance_id": acceptance.acceptance_id,
                    "timestamp": acceptance.timestamp.isoformat(),
                    "terms_version": acceptance.terms_version,
                    "expires_at": (
                        acceptance.expires_at.isoformat() if acceptance.expires_at else None
                    ),
                    "disclaimers": acceptance.disclaimers_accepted,
                }

            return False, None

        except SQLAlchemyError as e:
            logger.error(f"Database error checking acceptance: {e}")
            return False, None
        finally:
            session.close()

    def revoke_acceptance(self, user_identifier: str, reason: str = "User requested") -> bool:
        """Revoke user's acceptance of terms.

        Args:
            user_identifier: User identifier
            reason: Reason for revocation

        Returns:
            Success status
        """
        session = self.SessionLocal()
        try:
            user_hash = hashlib.sha256(user_identifier.encode()).hexdigest()

            # Find active acceptances
            acceptances = (
                session.query(LegalAcceptance)
                .filter(
                    LegalAcceptance.user_hash == user_hash, LegalAcceptance.revoked_at.is_(None)
                )
                .all()
            )

            for acceptance in acceptances:
                acceptance.revoked_at = datetime.utcnow()  # type: ignore
                acceptance.revocation_reason = reason  # type: ignore

            # Log revocation event
            event = LegalComplianceLog(
                event_id=hashlib.sha256(
                    f"revoke_{user_hash}_{datetime.utcnow().isoformat()}".encode()
                ).hexdigest(),
                timestamp=datetime.utcnow(),
                event_type="revocation",
                user_hash=user_hash,
                event_data={"reason": reason, "revoked_count": len(acceptances)},
                compliance_status="non_compliant",
                risk_level="medium",
            )

            session.add(event)
            session.commit()

            logger.info(f"Revoked {len(acceptances)} acceptances for user")
            return True

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error revoking acceptance: {e}")
            return False
        finally:
            session.close()

    def get_compliance_stats(self, days: int = 30) -> Dict:
        """Get compliance statistics for monitoring.

        Args:
            days: Number of days to look back

        Returns:
            Dictionary of compliance statistics
        """
        session = self.SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            total_acceptances = (
                session.query(func.count(LegalAcceptance.id))
                .filter(LegalAcceptance.timestamp >= cutoff_date)
                .scalar()
            )

            active_acceptances = (
                session.query(func.count(LegalAcceptance.id))
                .filter(
                    LegalAcceptance.timestamp >= cutoff_date,
                    LegalAcceptance.revoked_at.is_(None),
                    LegalAcceptance.expires_at > datetime.utcnow(),
                )
                .scalar()
            )

            revocations = (
                session.query(func.count(LegalAcceptance.id))
                .filter(LegalAcceptance.revoked_at >= cutoff_date)
                .scalar()
            )

            unique_users = (
                session.query(func.count(func.distinct(LegalAcceptance.user_hash)))
                .filter(LegalAcceptance.timestamp >= cutoff_date)
                .scalar()
            )

            return {
                "period_days": days,
                "total_acceptances": total_acceptances,
                "active_acceptances": active_acceptances,
                "revocations": revocations,
                "unique_users": unique_users,
                "compliance_rate": (
                    (active_acceptances / total_acceptances * 100) if total_acceptances > 0 else 0
                ),
            }

        except SQLAlchemyError as e:
            logger.error(f"Database error getting stats: {e}")
            return {}
        finally:
            session.close()

    def cleanup_expired_records(self, retention_days: int = 730) -> int:
        """Clean up old expired records for GDPR compliance.

        Args:
            retention_days: Days to retain records (default 2 years)

        Returns:
            Number of records deleted
        """
        session = self.SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

            # Delete old revoked records
            deleted = (
                session.query(LegalAcceptance)
                .filter(LegalAcceptance.revoked_at < cutoff_date)
                .delete()
            )

            # Delete old expired records
            deleted += (
                session.query(LegalAcceptance)
                .filter(LegalAcceptance.expires_at < cutoff_date)
                .delete()
            )

            session.commit()
            logger.info(f"Cleaned up {deleted} expired legal records")
            return deleted

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error during cleanup: {e}")
            return 0
        finally:
            session.close()
