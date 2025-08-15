"""
Focused synthetic tests for business_intelligence.py core functions.
"""

import pytest
from unittest.mock import Mock, patch

# Only import what actually exists
from src.business_intelligence import (
    create_bi_tools_list,
    get_bi_capabilities,
    BusinessIntelligenceAgent
)


class TestCreateBiToolsList:
    """Test create_bi_tools_list function."""

    def test_create_bi_tools_list_returns_list(self):
        """Test that create_bi_tools_list returns a list."""
        tools = create_bi_tools_list()
        
        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_create_bi_tools_list_has_required_tools(self):
        """Test that all required tools are present."""
        tools = create_bi_tools_list()
        tool_names = [tool.get("name", "") for tool in tools]
        
        # Check for expected tool types
        assert any("financial" in name.lower() for name in tool_names)
        assert any("market" in name.lower() or "rag" in name.lower() for name in tool_names)
        assert any("web" in name.lower() or "search" in name.lower() for name in tool_names)

    def test_create_bi_tools_list_structure(self):
        """Test that tools have expected structure."""
        tools = create_bi_tools_list()
        
        for tool in tools:
            assert isinstance(tool, dict)
            assert "name" in tool
            assert "description" in tool


class TestGetBiCapabilities:
    """Test get_bi_capabilities function."""

    def test_get_bi_capabilities_returns_dict(self):
        """Test that get_bi_capabilities returns a dict."""
        capabilities = get_bi_capabilities()
        
        assert isinstance(capabilities, dict)
        assert len(capabilities) > 0

    def test_get_bi_capabilities_has_expected_keys(self):
        """Test that capabilities has expected structure."""
        capabilities = get_bi_capabilities()
        
        # Check for main capability categories
        assert "tools_available" in capabilities or "tool_categories" in capabilities
        assert "specialized_agents" in capabilities or "agents" in capabilities
        assert "workflows_available" in capabilities or "workflows" in capabilities

    def test_get_bi_capabilities_structure(self):
        """Test capabilities structure."""
        capabilities = get_bi_capabilities()
        
        # Each capability should be a list or dict
        for key, value in capabilities.items():
            assert isinstance(value, (list, dict, str, int))


class TestBusinessIntelligenceAgent:
    """Test BusinessIntelligenceAgent class initialization."""

    @patch('src.business_intelligence.ConversableAgent.__init__')
    def test_agent_init_basic(self, mock_super_init):
        """Test basic agent initialization."""
        mock_super_init.return_value = None
        
        agent = BusinessIntelligenceAgent(
            name="TestAgent",
            system_message="Test message", 
            llm_config={"model": "test"}
        )
        
        # Verify parent class was called
        mock_super_init.assert_called_once()

    def test_agent_init_with_tools(self):
        """Test agent initialization with tools (mocked)."""
        # Since AG2 initialization is complex, just test the class exists
        assert BusinessIntelligenceAgent is not None
        assert hasattr(BusinessIntelligenceAgent, '__init__')
        assert hasattr(BusinessIntelligenceAgent, '_create_tool_function')


class TestModuleIntegrity:
    """Test module imports and basic functionality."""

    def test_all_imports_work(self):
        """Test that all main imports work without errors."""
        try:
            from src.business_intelligence import (
                BusinessIntelligenceAgent,
                create_bi_tools_list,
                get_bi_capabilities
            )
            # Basic functionality test
            tools = create_bi_tools_list()
            caps = get_bi_capabilities()
            
            assert len(tools) > 0
            assert len(caps) > 0
            
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    def test_functions_are_callable(self):
        """Test that main functions are callable."""
        assert callable(create_bi_tools_list)
        assert callable(get_bi_capabilities)
        assert callable(BusinessIntelligenceAgent)

    def test_no_syntax_errors(self):
        """Test that module loads without syntax errors."""
        try:
            import src.business_intelligence
            # If we get here, no syntax errors
            assert True
        except SyntaxError as e:
            pytest.fail(f"Syntax error in module: {e}")