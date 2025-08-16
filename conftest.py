"""
Pytest configuration and fixtures for Business Intelligence Platform tests.
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["ANTHROPIC_API_KEY"] = "test-key-12345"


@pytest.fixture(scope="session")
def test_data_dir():
    """Create temporary directory for test data."""
    temp_dir = tempfile.mkdtemp(prefix="bi_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_db_path(test_data_dir):
    """Create test SQLite database."""
    db_path = test_data_dir / "test_bi.db"
    return str(db_path)


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing."""
    with patch("anthropic.Anthropic") as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance

        # Mock response structure
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Mock AI response for testing"
        mock_instance.messages.create.return_value = mock_response

        yield mock_instance


@pytest.fixture
def sample_business_data():
    """Sample business data for testing."""
    return {
        "name": "TestCorp",
        "industry": "SaaS",
        "founded_date": "2023-01-01",
        "status": "active",
        "initial_funding": 1000000.0,
        "total_funding": 5000000.0,
        "valuation": 25000000.0,
        "employees": 50,
        "revenue": 3000000.0,
        "region": "North America",
        "business_model": "subscription",
    }


@pytest.fixture
def sample_financial_params():
    """Sample financial calculation parameters."""
    return {
        "cash_flows": [-100000, 30000, 40000, 50000, 60000],
        "discount_rate": 0.1,
        "initial_investment": 100000,
        "monthly_revenue": 10000,
        "monthly_costs": 7000,
    }


@pytest.fixture
def mock_database_config():
    """Mock database configuration for testing."""
    with patch("src.database_config.db_config") as mock_config:
        mock_config.use_postgres = False
        mock_config.environment = "test"
        yield mock_config


@pytest.fixture
def clean_error_tracker():
    """Clean error tracker before each test."""
    from src.error_handling import error_tracker

    error_tracker.errors.clear()
    yield error_tracker
    error_tracker.errors.clear()


@pytest.fixture(autouse=True)
def reset_global_state():
    """Reset all global singletons before each test to ensure isolation."""
    # Import here to avoid circular imports
    import src.business_intelligence as bi_module
    import src.chat as chat_module
    import src.error_handling as error_module

    # Reset all global state before each test
    chat_module._manager = None
    chat_module._user_proxy = None
    chat_module._synthesizer = None
    chat_module._memory_dict = None

    bi_module._bi_manager = None
    bi_module._bi_user_proxy = None
    bi_module._bi_synthesizer = None
    bi_module._bi_workflow = None
    bi_module._bi_swarm = None

    # Reset error tracker state
    if hasattr(error_module.error_tracker, "_errors"):
        error_module.error_tracker._errors.clear()
    if hasattr(error_module.error_tracker, "errors"):
        error_module.error_tracker.errors.clear()

    yield  # Run the test


@pytest.fixture
def mock_streamlit():
    """Mock Streamlit for testing UI components."""
    with patch("streamlit.session_state") as mock_state:
        mock_state.history = []
        mock_state.last_len = 0
        mock_state.mode = "chat"
        yield mock_state
