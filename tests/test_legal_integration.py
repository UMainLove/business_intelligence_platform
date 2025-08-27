"""
Production-ready integration tests for legal compliance system.

Tests the legal agreement database integration without requiring Streamlit UI.
Validates database operations, user agreement workflows, and compliance tracking.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import Mock

import pytest

# Ensure project root is in path
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))


class MockSessionState:
    """Mock Streamlit session state for testing."""

    def __init__(self) -> None:
        """Initialize mock session state."""
        self._data: Dict[str, Any] = {}

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get value from session state."""
        return self._data.get(key, default)

    def __setitem__(self, key: str, value: Any) -> None:
        """Set value in session state."""
        self._data[key] = value

    def __getitem__(self, key: str) -> Any:
        """Get value from session state."""
        return self._data[key]


class MockStreamlit:
    """Mock Streamlit module for testing."""

    def __init__(self) -> None:
        """Initialize mock Streamlit."""
        self.session_state = MockSessionState()

    def set_page_config(self, **kwargs: Any) -> None:
        """Mock set_page_config method."""
        pass

    def stop(self) -> bool:
        """Mock stop method."""
        return True

    def dialog(self, title: str) -> Any:
        """Mock dialog decorator."""

        def decorator(func):
            return func

        return decorator


@pytest.fixture
def mock_streamlit() -> Mock:
    """Provide mocked Streamlit for testing."""
    # Replace streamlit import in user_agreement module
    original_streamlit = sys.modules.get("streamlit")
    mock_st = MockStreamlit()
    sys.modules["streamlit"] = mock_st  # type: ignore

    yield mock_st

    # Restore original streamlit module
    if original_streamlit:
        sys.modules["streamlit"] = original_streamlit
    elif "streamlit" in sys.modules:
        del sys.modules["streamlit"]


class TestLegalComplianceIntegration:
    """Integration tests for legal compliance system."""

    def test_database_manager_initialization(self) -> None:
        """Test database manager can be initialized."""
        from src.legal.legal_database import LegalDatabaseManager

        db = LegalDatabaseManager()
        assert db is not None
        assert hasattr(db, "engine")
        assert hasattr(db, "SessionLocal")

    def test_database_structure_validation(self) -> None:
        """Test database tables exist and are operational."""
        from src.legal.legal_database import LegalDatabaseManager

        db = LegalDatabaseManager()
        stats = db.get_compliance_stats(days=1)

        assert isinstance(stats, dict)
        assert "total_acceptances" in stats
        assert "active_acceptances" in stats
        assert "unique_users" in stats
        assert "compliance_rate" in stats

    def test_legal_agreement_database_mode(self, mock_streamlit: Mock) -> None:
        """Test legal agreement system with database enabled."""
        from src.legal.user_agreement import LegalAgreement

        legal = LegalAgreement(use_database=True)
        assert legal.use_database is True
        assert hasattr(legal, "db")
        assert legal.critical_disclaimers is not None

    def test_legal_agreement_fallback_mode(self, mock_streamlit: Mock) -> None:
        """Test legal agreement system with JSON fallback."""
        from src.legal.user_agreement import LegalAgreement

        legal = LegalAgreement(use_database=False)
        assert legal.use_database is False
        assert hasattr(legal, "acceptance_file")
        assert legal.critical_disclaimers is not None

    def test_acceptance_recording_workflow(self, mock_streamlit: Mock) -> None:
        """Test complete acceptance recording workflow."""
        from src.legal.user_agreement import LegalAgreement

        # Setup mock session state
        mock_streamlit.session_state._data = {
            "user_id": "test_user_integration_pytest",
            "session_id": "test_session_integration_pytest",
            "remote_ip": "127.0.0.1",
            "user_agent": "Pytest Integration Test",
        }

        # Initialize legal system
        legal = LegalAgreement(use_database=True)

        # Test acknowledgments (all required disclaimers)
        test_acknowledgments = {
            "no_financial_advice": True,
            "no_legal_advice": True,
            "use_at_own_risk": True,
            "no_liability": True,
            "seek_professionals": True,
            "ai_limitations": True,
            "verify_information": True,
            "no_guarantee": True,
        }

        # Record acceptance
        success = legal.record_acceptance(test_acknowledgments)
        assert success is True

        # Verify acceptance was recorded
        has_accepted = legal.has_accepted_terms()
        assert has_accepted is True

    def test_incomplete_acknowledgments_rejection(self, mock_streamlit: Mock) -> None:
        """Test that incomplete acknowledgments are rejected."""
        from src.legal.user_agreement import LegalAgreement

        # Setup mock session state
        mock_streamlit.session_state._data = {
            "user_id": "test_incomplete_user",
            "session_id": "test_incomplete_session",
            "remote_ip": "127.0.0.1",
        }

        legal = LegalAgreement(use_database=True)

        # Incomplete acknowledgments (missing some required disclaimers)
        incomplete_acknowledgments = {
            "no_financial_advice": True,
            "no_legal_advice": False,  # This should cause rejection
            "use_at_own_risk": True,
            "no_liability": True,
        }

        success = legal.record_acceptance(incomplete_acknowledgments)
        assert success is False

    def test_compliance_statistics_tracking(self) -> None:
        """Test compliance statistics are properly tracked."""
        from src.legal.legal_database import LegalDatabaseManager

        db = LegalDatabaseManager()

        # Get initial stats
        initial_stats = db.get_compliance_stats(days=7)

        # Verify stats structure
        assert isinstance(initial_stats["total_acceptances"], int)
        assert isinstance(initial_stats["active_acceptances"], int)
        assert isinstance(initial_stats["unique_users"], int)
        assert isinstance(initial_stats["compliance_rate"], (int, float))

        # Verify compliance rate calculation
        if initial_stats["total_acceptances"] > 0:
            expected_rate = (
                initial_stats["active_acceptances"] / initial_stats["total_acceptances"] * 100
            )
            assert abs(initial_stats["compliance_rate"] - expected_rate) < 0.1

    def test_database_tables_existence(self) -> None:
        """Test that all required database tables exist."""
        from sqlalchemy import inspect

        from src.legal.legal_database import LegalDatabaseManager

        db = LegalDatabaseManager()
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        required_tables = ["legal_acceptances", "legal_compliance_log", "legal_terms_versions"]

        for table in required_tables:
            assert table in tables, f"Required table {table} not found"

    def test_legal_terms_version_management(self) -> None:
        """Test legal terms version management."""
        from src.legal.legal_database import LegalDatabaseManager, LegalTermsVersion

        db = LegalDatabaseManager()
        session = db.SessionLocal()

        try:
            # Check that initial version exists
            version = session.query(LegalTermsVersion).filter_by(version="1.0").first()
            assert version is not None
            assert version.terms_hash is not None
            assert version.effective_date is not None
        finally:
            session.close()

    def test_session_hash_generation(self, mock_streamlit: Mock) -> None:
        """Test session hash generation for user tracking."""
        from src.legal.user_agreement import LegalAgreement

        # Setup session state
        mock_streamlit.session_state._data = {
            "session_id": "test_session_hash",
        }

        legal = LegalAgreement(use_database=False)
        session_hash = legal.get_session_hash()

        assert isinstance(session_hash, str)
        assert len(session_hash) == 16  # SHA256 truncated to 16 chars

    def test_critical_disclaimers_completeness(self, mock_streamlit: Mock) -> None:
        """Test that all critical disclaimers are defined."""
        from src.legal.user_agreement import LegalAgreement

        legal = LegalAgreement(use_database=False)

        # Expected disclaimer keys based on implementation
        expected_disclaimers = {
            "no_financial_advice",
            "no_legal_advice",
            "use_at_own_risk",
            "no_liability",
            "seek_professionals",
            "ai_limitations",
            "verify_information",
            "no_guarantee",
        }

        actual_disclaimers = set(legal.critical_disclaimers.keys())
        assert actual_disclaimers == expected_disclaimers


def test_legal_integration_cli_execution() -> None:
    """Test legal integration can be executed as CLI script."""
    # This test ensures the integration works when called from command line
    from src.legal.legal_database import LegalDatabaseManager
    from src.legal.user_agreement import LegalAgreement

    # Basic smoke test
    db = LegalDatabaseManager()
    assert db is not None

    # Mock streamlit for initialization test
    original_streamlit = sys.modules.get("streamlit")
    mock_st = MockStreamlit()
    sys.modules["streamlit"] = mock_st  # type: ignore

    try:
        legal = LegalAgreement(use_database=True)
        assert legal is not None
    finally:
        # Restore streamlit
        if original_streamlit:
            sys.modules["streamlit"] = original_streamlit
        elif "streamlit" in sys.modules:
            del sys.modules["streamlit"]


if __name__ == "__main__":
    # Allow running as standalone script for development
    pytest.main([__file__, "-v"])
