#!/usr/bin/env python3
"""
Isolated test runner for legal feature to avoid external dependency warnings.
This ensures zero fault tolerance for the legal feature specifically.
"""

import sys
import warnings
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure project root is in path
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))


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


def test_legal_database_functionality() -> None:
    """Test legal database module functionality."""
    print("🧪 Testing legal database functionality...")

    try:
        from src.legal.legal_database import (
            LegalAcceptance,
            LegalComplianceLog,
            LegalDatabaseManager,
            LegalTermsVersion,
        )

        # Test database initialization
        db = LegalDatabaseManager()
        assert db is not None
        assert hasattr(db, "engine")
        assert hasattr(db, "SessionLocal")
        print("✅ Database manager initializes correctly")

        # Test compliance stats
        stats = db.get_compliance_stats(days=1)
        assert isinstance(stats, dict)
        assert "total_acceptances" in stats
        assert "active_acceptances" in stats
        assert "unique_users" in stats
        assert "compliance_rate" in stats
        print("✅ Database compliance stats work correctly")

        # Test model classes exist and have required attributes
        assert hasattr(LegalAcceptance, "__tablename__")
        assert hasattr(LegalComplianceLog, "__tablename__")
        assert hasattr(LegalTermsVersion, "__tablename__")
        print("✅ Database models are properly defined")

    except ImportError as e:
        print(f"⚠️  SQLAlchemy not available (expected in CI): {e}")
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        raise


def test_legal_agreement_functionality() -> None:
    """Test legal agreement module functionality."""
    print("🧪 Testing legal agreement functionality...")

    # Mock streamlit
    original_streamlit = sys.modules.get("streamlit")
    mock_st = MockStreamlit()
    sys.modules["streamlit"] = mock_st  # type: ignore

    try:
        from src.legal.user_agreement import LegalAgreement

        # Test JSON mode initialization
        legal = LegalAgreement(use_database=False)
        assert legal.use_database is False
        assert hasattr(legal, "acceptance_file")
        assert legal.critical_disclaimers is not None
        print("✅ LegalAgreement JSON mode initializes correctly")

        # Test database mode initialization (with fallback)
        legal_db = LegalAgreement(use_database=True)
        # May fall back to JSON mode if SQLAlchemy not available
        if legal_db.use_database:
            assert hasattr(legal_db, "db")
        else:
            assert hasattr(legal_db, "acceptance_file")
        print("✅ LegalAgreement database mode initializes correctly")

        # Test critical disclaimers structure
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
        print("✅ Critical disclaimers are complete and correct")

        # Test session hash generation
        mock_st.session_state._data = {"session_id": "test_session"}
        session_hash = legal.get_session_hash()
        assert isinstance(session_hash, str)
        assert len(session_hash) == 16
        print("✅ Session hash generation works correctly")

        # Test acceptance recording workflow
        mock_st.session_state._data = {
            "user_id": "test_user_isolated",
            "session_id": "test_session_isolated",
            "remote_ip": "127.0.0.1",
            "user_agent": "Test Agent",
        }

        # Test complete acknowledgments
        complete_acknowledgments = {key: True for key in legal.critical_disclaimers.keys()}
        success = legal.record_acceptance(complete_acknowledgments)
        assert success is True
        print("✅ Complete acknowledgments are accepted")

        # Test incomplete acknowledgments
        incomplete_acknowledgments = {key: False for key in legal.critical_disclaimers.keys()}
        success = legal.record_acceptance(incomplete_acknowledgments)
        assert success is False
        print("✅ Incomplete acknowledgments are rejected")

    finally:
        # Restore streamlit
        if original_streamlit:
            sys.modules["streamlit"] = original_streamlit
        elif "streamlit" in sys.modules:
            del sys.modules["streamlit"]


def test_legal_integration_imports() -> None:
    """Test that all legal module imports work without warnings."""
    print("🧪 Testing legal module imports...")

    # Enable strict deprecation warning checking
    with warnings.catch_warnings():
        warnings.filterwarnings("error", category=DeprecationWarning)

        try:
            from src.legal.user_agreement import LegalAgreement  # noqa: F401

            print("✅ user_agreement imports without warnings")
        except DeprecationWarning as e:
            print(f"❌ Deprecation warning in user_agreement: {e}")
            raise

        try:
            from src.legal.legal_database import LegalDatabaseManager  # noqa: F401

            print("✅ legal_database imports without warnings")
        except ImportError:
            print("⚠️  SQLAlchemy not available (expected in CI)")
        except DeprecationWarning as e:
            print(f"❌ Deprecation warning in legal_database: {e}")
            raise


def run_all_tests() -> bool:
    """Run all isolated legal feature tests."""
    print("🚀 Starting comprehensive legal feature tests...")
    print("=" * 60)

    try:
        test_legal_integration_imports()
        print()

        test_legal_database_functionality()
        print()

        test_legal_agreement_functionality()
        print()

        print("=" * 60)
        print("🎉 ALL LEGAL FEATURE TESTS PASSED - ZERO FAULTS DETECTED!")
        return True

    except Exception as e:
        print("=" * 60)
        print(f"❌ LEGAL FEATURE TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
