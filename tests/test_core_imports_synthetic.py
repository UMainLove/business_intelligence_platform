"""
Synthetic tests for core module imports and basic functionality.
"""

from unittest.mock import Mock, patch

import pytest


class TestCoreImports:
    """Test that all core modules can be imported successfully."""

    def test_error_handling_import(self):
        """Test error handling module import."""
        from src.error_handling import (
            BusinessIntelligenceError,
            DatabaseError,
            handle_errors,
            retry_with_backoff,
            safe_execute,
            validate_input,
        )

        # Test that classes are properly defined
        assert issubclass(DatabaseError, BusinessIntelligenceError)
        assert callable(retry_with_backoff)
        assert callable(handle_errors)
        assert callable(safe_execute)
        assert callable(validate_input)

    def test_health_monitor_import(self):
        """Test health monitor module import."""
        from src.health_monitor import HealthMonitor

        # Test basic instantiation
        monitor = HealthMonitor()
        assert monitor is not None
        assert hasattr(monitor, "get_simple_health")
        assert hasattr(monitor, "get_system_metrics")

    def test_financial_tools_import(self):
        """Test financial tools module import."""
        from src.tools.financial_tools import (
            FinancialCalculator,
            financial_tool_executor,
        )

        # Test basic functionality
        calc = FinancialCalculator()
        assert hasattr(calc, "calculate_npv")
        assert hasattr(calc, "calculate_irr")
        assert callable(financial_tool_executor)

    def test_rag_tools_import(self):
        """Test RAG tools module import."""
        from src.tools.rag_tools import (
            Document,
            rag_tool_executor,
        )

        # Test Document dataclass
        doc = Document(id="test", title="Test", content="Content", metadata={})
        assert doc.id == "test"
        assert callable(rag_tool_executor)

    def test_document_tools_import(self):
        """Test document tools module import."""
        import tempfile

        from src.tools.document_tools import DocumentGenerator

        with tempfile.TemporaryDirectory() as temp_dir:
            doc_gen = DocumentGenerator(temp_dir)
            assert doc_gen is not None
            assert hasattr(doc_gen, "generate_market_analysis_report")

    def test_database_config_import(self):
        """Test database configuration import."""
        from src.database_config import DatabaseConfig

        # Test basic instantiation
        config = DatabaseConfig()
        assert config is not None
        assert hasattr(config, "get_connection")
        assert hasattr(config, "init_database")

    def test_business_intelligence_import(self):
        """Test business intelligence module import."""
        from src.business_intelligence import BusinessIntelligenceAgent

        # Should be able to import without errors
        assert BusinessIntelligenceAgent is not None

    def test_util_import(self):
        """Test utility module import."""
        from src.util import (
            BI_DEFAULT_SPLIT,
            DEFAULT_SPLIT,
            describe_pricing,
            estimate_cost_usd,
            get_cost_breakdown,
        )

        assert isinstance(BI_DEFAULT_SPLIT, dict)
        assert isinstance(DEFAULT_SPLIT, dict)
        assert callable(estimate_cost_usd)
        assert callable(describe_pricing)
        assert callable(get_cost_breakdown)

    def test_memory_import(self):
        """Test memory module import."""
        from src.memory import (
            PROMPT_JSON,
            build_memory_from_messages,
            load_memory,
            memory_block,
            save_memory,
        )

        assert callable(memory_block)
        assert callable(load_memory)
        assert callable(save_memory)
        assert callable(build_memory_from_messages)
        assert isinstance(PROMPT_JSON, str)

    def test_chat_import(self):
        """Test chat module import."""
        from src.chat import build_group

        assert callable(build_group)

    def test_workflows_import(self):
        """Test workflow modules import."""
        from src.workflows.sequential_validation import SequentialValidationWorkflow
        from src.workflows.swarm_scenarios import (
            ScenarioResult,
            ScenarioType,
            SwarmScenarioAnalysis,
        )

        assert SequentialValidationWorkflow is not None
        assert SwarmScenarioAnalysis is not None
        assert ScenarioType is not None
        assert ScenarioResult is not None


class TestModuleCompatibility:
    """Test module compatibility and basic functionality."""

    def test_financial_tools_basic_operations(self):
        """Test basic financial calculations work."""
        from src.tools.financial_tools import FinancialCalculator

        calc = FinancialCalculator()

        # Test NPV calculation
        npv = calc.calculate_npv([-1000, 500, 600], 0.1)
        assert isinstance(npv, (int, float))

        # Test ROI calculation
        roi = calc.calculate_roi(1500, 1000)
        assert roi == 50.0

    @patch("anthropic.Anthropic")
    def test_anthropic_client_creation(self, mock_anthropic):
        """Test Anthropic client creation with mocking."""
        import os

        mock_client = Mock()
        mock_anthropic.return_value = mock_client

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            # Test creating client directly
            from anthropic import Anthropic

            client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            mock_anthropic.assert_called()
            assert client == mock_client

    def test_error_handling_basic_functionality(self):
        """Test basic error handling functionality."""
        from src.error_handling import safe_execute

        def success_func():
            return "success"

        def error_func():
            raise ValueError("test error")

        # Test successful execution
        result = safe_execute(success_func, fallback_value="fallback")
        assert result == "success"

        # Test fallback on error
        result = safe_execute(error_func, fallback_value="fallback")
        assert result == "fallback"

    def test_health_monitor_basic_functionality(self):
        """Test basic health monitoring functionality."""
        from src.health_monitor import HealthMonitor

        monitor = HealthMonitor()
        health = monitor.get_simple_health()

        assert isinstance(health, dict)
        assert "status" in health
        assert "timestamp" in health

    def test_document_generation_basic(self):
        """Test basic document generation."""
        import tempfile

        from src.tools.document_tools import DocumentGenerator

        with tempfile.TemporaryDirectory() as temp_dir:
            doc_gen = DocumentGenerator(temp_dir)
            result = doc_gen.generate_market_analysis_report(
                {"industry": "Test Industry", "market_size": "$1B"}
            )

            assert result["document_type"] == "market_analysis"
            assert "filename" in result
            assert "content" in result

    def test_rag_basic_functionality(self):
        """Test basic RAG functionality."""
        import tempfile

        from src.tools.rag_tools import MarketResearchRAG

        with tempfile.TemporaryDirectory() as temp_dir:
            rag = MarketResearchRAG(temp_dir)

            # Add a document
            doc_id = rag.add_document("Test", "Content", {"type": "test"})
            assert isinstance(doc_id, str)

            # Search for it
            results = rag.search("Content", top_k=1)
            assert len(results) == 1
            assert results[0].content == "Content"


class TestConfigurationAndSettings:
    """Test configuration and settings functionality."""

    def test_cost_estimation(self):
        """Test cost estimation functionality."""
        from src.util import describe_pricing, estimate_cost_usd

        # Test cost estimation
        cost = estimate_cost_usd(1000, use_bi_pricing=True)
        assert isinstance(cost, (int, float))
        assert cost >= 0

        # Test pricing description
        pricing = describe_pricing()
        assert isinstance(pricing, dict)

    def test_bi_default_split_structure(self):
        """Test BI default split configuration."""
        from src.util import BI_DEFAULT_SPLIT

        assert isinstance(BI_DEFAULT_SPLIT, dict)
        # Check that it has the expected keys for BI pricing split
        assert "input" in BI_DEFAULT_SPLIT
        assert "output_specs" in BI_DEFAULT_SPLIT
        assert "output_synth" in BI_DEFAULT_SPLIT

        # Test that values sum to approximately 1.0
        total = sum(BI_DEFAULT_SPLIT.values())
        assert abs(total - 1.0) < 0.001

    @patch.dict("os.environ", {"ANTHROPIC_MODEL_SPECIALISTS": "test-model"})
    def test_environment_variable_usage(self):
        """Test that environment variables are properly used."""
        import os

        # Test that environment variable is set
        assert os.getenv("ANTHROPIC_MODEL_SPECIALISTS") == "test-model"

        # Test that util module can use environment variables
        from src.util import estimate_cost_usd

        cost = estimate_cost_usd(1000)
        assert isinstance(cost, (int, float))

    def test_database_config_environment_detection(self):
        """Test database configuration environment detection."""
        from src.database_config import DatabaseConfig

        # Test with different environment settings
        with patch.dict("os.environ", {"ENVIRONMENT": "test"}):
            config = DatabaseConfig()
            assert config.environment == "test"

        with patch.dict("os.environ", {"ENVIRONMENT": "production"}):
            config = DatabaseConfig()
            assert config.environment == "production"


class TestModuleDependencies:
    """Test module dependencies and imports."""

    def test_all_tool_imports(self):
        """Test that all tool modules can be imported."""
        tool_modules = [
            "src.tools.financial_tools",
            "src.tools.rag_tools",
            "src.tools.document_tools",
            "src.tools.web_tools",
            "src.tools.api_tools",
            "src.tools.database_tools",
            "src.tools.database_production",
        ]

        for module_name in tool_modules:
            try:
                __import__(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")

    def test_workflow_imports(self):
        """Test that workflow modules can be imported."""
        workflow_modules = [
            "src.workflows.sequential_validation",
            "src.workflows.swarm_scenarios",
        ]

        for module_name in workflow_modules:
            try:
                __import__(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")

    def test_core_module_imports(self):
        """Test that core modules can be imported."""
        core_modules = [
            "src.business_intelligence",
            "src.chat",
            "src.error_handling",
            "src.health_monitor",
            "src.memory",
            "src.util",
            "src.database_config",
        ]

        for module_name in core_modules:
            try:
                __import__(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")

    def test_optional_dependency_handling(self):
        """Test handling of optional dependencies."""
        # Test that modules gracefully handle missing optional dependencies
        with patch.dict("sys.modules", {"psycopg2": None}):
            try:
                from src.database_config import DatabaseConfig

                config = DatabaseConfig()
                # Should default to SQLite when PostgreSQL is not available
                assert not config.use_postgres
            except Exception as e:
                pytest.fail(f"Failed to handle missing psycopg2: {e}")


class TestBasicFunctionality:
    """Test basic functionality without external dependencies."""

    def test_validation_functions(self):
        """Test input validation functions."""
        from src.error_handling import ValidationError, validate_input

        # Valid input should not raise
        validate_input(
            {"name": "test", "value": 42}, ["name", "value"], {"name": str, "value": int}
        )

        # Invalid input should raise
        with pytest.raises(ValidationError):
            validate_input({"name": 123}, ["name"], {"name": str})  # Wrong type

    def test_memory_prompt_structure(self):
        """Test memory prompt structure."""
        from src.memory import PROMPT_JSON

        assert isinstance(PROMPT_JSON, str)
        # PROMPT_JSON is a prompt template, check it exists and is a string
        assert len(PROMPT_JSON) > 0

    def test_financial_metrics_dataclass(self):
        """Test FinancialMetrics dataclass."""
        from src.tools.financial_tools import FinancialMetrics

        metrics = FinancialMetrics(
            npv=1000.0, irr=0.15, payback_period=3.0, break_even_point=500, roi=25.0
        )

        assert metrics.npv == 1000.0
        assert metrics.irr == 0.15
        assert metrics.roi == 25.0
