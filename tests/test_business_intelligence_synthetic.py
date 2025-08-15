"""
Synthetic tests for business_intelligence.py without external dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from typing import Dict, Any
import json

from src.business_intelligence import (
    BusinessIntelligenceAgent,
    create_bi_tools_list,
    build_bi_group,
    run_sequential_validation,
    run_swarm_analysis,
    run_enhanced_synthesis,
    get_bi_capabilities
)


class TestBusinessIntelligenceAgent:
    """Test BusinessIntelligenceAgent class."""

    @patch('src.business_intelligence.ConversableAgent.__init__')
    def test_agent_initialization_no_tools(self, mock_super_init):
        """Test BusinessIntelligenceAgent initialization without tools."""
        mock_super_init.return_value = None
        
        agent = BusinessIntelligenceAgent(
            name="TestAgent",
            system_message="Test message",
            llm_config={"model": "test"},
            tools=None
        )
        
        mock_super_init.assert_called_once_with(
            name="TestAgent",
            system_message="Test message",
            llm_config={"model": "test"},
            human_input_mode="NEVER"
        )

    @patch('src.business_intelligence.ConversableAgent.__init__')
    def test_agent_initialization_with_tools(self, mock_super_init):
        """Test BusinessIntelligenceAgent initialization with tools."""
        mock_super_init.return_value = None
        
        # Create agent with mock tools
        tools = [
            {"name": "financial_calculator", "description": "Calculate finances"},
            {"name": "market_research_rag", "description": "Search market data"}
        ]
        
        agent = BusinessIntelligenceAgent(
            name="TestAgent",
            system_message="Test message",
            llm_config={"model": "test"},
            tools=tools
        )
        
        # Mock the register_for_llm method to test tool registration
        agent.register_for_llm = Mock(return_value=lambda x: x)
        
        # Re-initialize to trigger tool registration
        agent.__init__(
            name="TestAgent",
            system_message="Test message", 
            llm_config={"model": "test"},
            tools=tools
        )

    def test_create_tool_function_financial(self):
        """Test creating financial calculator tool function."""
        agent = Mock(spec=BusinessIntelligenceAgent)
        
        # Create the tool function
        tool_func = BusinessIntelligenceAgent._create_tool_function(
            agent, "financial_calculator"
        )
        
        # Mock the executor
        with patch('src.business_intelligence.financial_tool_executor') as mock_executor:
            mock_executor.return_value = {"result": "success"}
            
            result = tool_func(operation="npv", params={"cash_flows": [100, 200]})
            
            assert result == {"result": "success"}
            mock_executor.assert_called_once_with("npv", {"cash_flows": [100, 200]})

    def test_create_tool_function_financial_error(self):
        """Test financial calculator tool function error handling."""
        agent = Mock(spec=BusinessIntelligenceAgent)
        
        tool_func = BusinessIntelligenceAgent._create_tool_function(
            agent, "financial_calculator"
        )
        
        with patch('src.business_intelligence.financial_tool_executor') as mock_executor:
            mock_executor.side_effect = Exception("Calculator error")
            
            result = tool_func(operation="npv", params={})
            
            assert "error" in result
            assert "Financial tool execution failed" in result["error"]

    def test_create_tool_function_rag(self):
        """Test creating RAG tool function."""
        agent = Mock(spec=BusinessIntelligenceAgent)
        
        tool_func = BusinessIntelligenceAgent._create_tool_function(
            agent, "market_research_rag"
        )
        
        with patch('src.business_intelligence.rag_tool_executor') as mock_executor:
            mock_executor.return_value = {"results": ["doc1", "doc2"]}
            
            result = tool_func(action="search", params={"query": "AI market"})
            
            assert result == {"results": ["doc1", "doc2"]}
            mock_executor.assert_called_once_with("search", {"query": "AI market"})

    def test_create_tool_function_web_search(self):
        """Test creating web search tool function."""
        agent = Mock(spec=BusinessIntelligenceAgent)
        
        tool_func = BusinessIntelligenceAgent._create_tool_function(
            agent, "web_search"
        )
        
        with patch('src.business_intelligence.web_search_executor') as mock_executor:
            mock_executor.return_value = {"results": ["result1"]}
            
            result = tool_func(search_type="market", params={"query": "trends"})
            
            assert result == {"results": ["result1"]}

    def test_create_tool_function_database(self):
        """Test creating database tool function."""
        agent = Mock(spec=BusinessIntelligenceAgent)
        
        tool_func = BusinessIntelligenceAgent._create_tool_function(
            agent, "database_manager"
        )
        
        with patch('src.business_intelligence.database_tool_executor') as mock_executor:
            mock_executor.return_value = {"success": True}
            
            result = tool_func(operation="query", params={"sql": "SELECT *"})
            
            assert result == {"success": True}

    def test_create_tool_function_document(self):
        """Test creating document tool function."""
        agent = Mock(spec=BusinessIntelligenceAgent)
        
        tool_func = BusinessIntelligenceAgent._create_tool_function(
            agent, "document_generator"
        )
        
        with patch('src.business_intelligence.document_tool_executor') as mock_executor:
            mock_executor.return_value = {"document": "content"}
            
            result = tool_func(doc_type="report", params={"data": "test"})
            
            assert result == {"document": "content"}

    def test_create_tool_function_api(self):
        """Test creating API tool function."""
        agent = Mock(spec=BusinessIntelligenceAgent)
        
        tool_func = BusinessIntelligenceAgent._create_tool_function(
            agent, "external_api"
        )
        
        with patch('src.business_intelligence.api_tool_executor') as mock_executor:
            mock_executor.return_value = {"api_response": "data"}
            
            result = tool_func(endpoint="test", params={"method": "GET"})
            
            assert result == {"api_response": "data"}

    def test_create_tool_function_unknown(self):
        """Test creating unknown tool function."""
        agent = Mock(spec=BusinessIntelligenceAgent)
        
        tool_func = BusinessIntelligenceAgent._create_tool_function(
            agent, "unknown_tool"
        )
        
        result = tool_func(param1="value1", param2="value2")
        
        assert result == {"error": "Unknown tool: unknown_tool"}


class TestToolsListCreation:
    """Test create_bi_tools_list function."""

    @patch('src.business_intelligence.create_financial_tool_spec')
    @patch('src.business_intelligence.create_rag_tool_spec')
    @patch('src.business_intelligence.create_web_search_tool_spec')
    @patch('src.business_intelligence.create_database_tool_spec')
    @patch('src.business_intelligence.create_document_tool_spec')
    @patch('src.business_intelligence.create_api_tool_spec')
    def test_create_bi_tools_list(self, mock_api, mock_doc, mock_db, 
                                mock_web, mock_rag, mock_financial):
        """Test creating BI tools list."""
        # Mock tool spec returns
        mock_financial.return_value = {"name": "financial_calculator"}
        mock_rag.return_value = {"name": "market_research_rag"}
        mock_web.return_value = {"name": "web_search"}
        mock_db.return_value = {"name": "database_manager"}
        mock_doc.return_value = {"name": "document_generator"}
        mock_api.return_value = {"name": "external_api"}
        
        tools = create_bi_tools_list()
        
        assert len(tools) == 6
        assert {"name": "financial_calculator"} in tools
        assert {"name": "market_research_rag"} in tools
        assert {"name": "web_search"} in tools
        assert {"name": "database_manager"} in tools
        assert {"name": "document_generator"} in tools
        assert {"name": "external_api"} in tools


class TestBuildBiGroup:
    """Test build_bi_group function."""

    @patch('src.business_intelligence.ConversableAgent')
    @patch('src.business_intelligence.BusinessIntelligenceAgent')
    @patch('src.business_intelligence.GroupChat')
    @patch('src.business_intelligence.GroupChatManager')
    @patch('src.business_intelligence.create_bi_tools_list')
    @patch('src.business_intelligence._anthropic_cfg')
    @patch('src.business_intelligence._compose_system')
    def test_build_bi_group(self, mock_compose, mock_cfg, mock_tools, 
                            mock_manager_class, mock_chat_class, 
                            mock_bi_agent, mock_conv_agent):
        """Test building BI group."""
        # Setup mocks
        mock_cfg.return_value = {"model": "test"}
        mock_compose.return_value = "system message"
        mock_tools.return_value = [{"name": "test_tool"}]
        
        mock_user = Mock()
        mock_economist = Mock()
        mock_lawyer = Mock()
        mock_sociologist = Mock()
        mock_synthesizer = Mock()
        
        mock_conv_agent.return_value = mock_user
        mock_bi_agent.side_effect = [mock_economist, mock_lawyer, mock_sociologist, mock_synthesizer]
        
        mock_chat = Mock()
        mock_chat_class.return_value = mock_chat
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        
        result = build_bi_group(memory={"idea": "test"})
        
        assert "user_proxy" in result
        assert "economist" in result
        assert "lawyer" in result
        assert "sociologist" in result
        assert "synthesizer" in result
        assert "group_chat" in result
        assert "manager" in result


class TestWorkflowFunctions:
    """Test workflow execution functions."""

    @patch('src.business_intelligence.SequentialValidationWorkflow')
    def test_run_sequential_validation(self, mock_workflow_class):
        """Test running sequential validation."""
        mock_workflow = Mock()
        mock_workflow.run_validation.return_value = {"result": "validation complete"}
        mock_workflow_class.return_value = mock_workflow
        
        business_data = {"idea": "AI startup", "market": "B2B"}
        result = run_sequential_validation(business_data)
        
        assert result == {"result": "validation complete"}
        mock_workflow_class.assert_called_once_with(business_data)
        mock_workflow.run_validation.assert_called_once()

    @patch('src.business_intelligence.SwarmScenarioAnalysis')
    def test_run_swarm_analysis(self, mock_swarm_class):
        """Test running swarm analysis."""
        mock_swarm = Mock()
        mock_swarm.run_all_scenarios.return_value = {"scenarios": "complete"}
        mock_swarm_class.return_value = mock_swarm
        
        business_data = {"idea": "Tech startup"}
        scenario_config = {"stress_test": True}
        
        result = run_swarm_analysis(business_data, scenario_config)
        
        assert result == {"scenarios": "complete"}
        mock_swarm_class.assert_called_once_with(business_data, scenario_config)
        mock_swarm.run_all_scenarios.assert_called_once()

    @patch('src.business_intelligence.ConversableAgent')
    @patch('src.business_intelligence.GroupChatManager')
    def test_run_enhanced_synthesis_success(self, mock_manager_class, mock_agent_class):
        """Test successful enhanced synthesis."""
        # Mock synthesizer agent
        mock_synthesizer = Mock()
        mock_agent_class.return_value = mock_synthesizer
        
        # Mock manager
        mock_manager = Mock()
        mock_chat_result = Mock()
        mock_chat_result.chat_history = [
            {"content": json.dumps({
                "executive_summary": "Test summary",
                "economic_viability": "Good",
                "legal_risks": "Low", 
                "social_impact": "Positive",
                "next_steps": ["Step 1", "Step 2"]
            })}
        ]
        mock_manager.initiate_chat.return_value = mock_chat_result
        mock_manager_class.return_value = mock_manager
        
        messages = [
            {"name": "economist", "content": "Economic analysis"},
            {"name": "lawyer", "content": "Legal analysis"}
        ]
        
        result = run_enhanced_synthesis(messages)
        
        assert result["executive_summary"] == "Test summary"
        assert result["economic_viability"] == "Good"
        assert len(result["next_steps"]) == 2

    @patch('src.business_intelligence.ConversableAgent')
    @patch('src.business_intelligence.GroupChatManager')
    def test_run_enhanced_synthesis_json_error(self, mock_manager_class, mock_agent_class):
        """Test enhanced synthesis with JSON parsing error."""
        mock_synthesizer = Mock()
        mock_agent_class.return_value = mock_synthesizer
        
        mock_manager = Mock()
        mock_chat_result = Mock()
        mock_chat_result.chat_history = [
            {"content": "Not valid JSON"}
        ]
        mock_manager.initiate_chat.return_value = mock_chat_result
        mock_manager_class.return_value = mock_manager
        
        messages = [{"name": "test", "content": "test"}]
        
        result = run_enhanced_synthesis(messages)
        
        assert "executive_summary" in result
        assert result["executive_summary"] == "Could not parse structured synthesis report."

    @patch('src.business_intelligence.ConversableAgent')
    @patch('src.business_intelligence.GroupChatManager')
    def test_run_enhanced_synthesis_exception(self, mock_manager_class, mock_agent_class):
        """Test enhanced synthesis with exception."""
        mock_synthesizer = Mock()
        mock_agent_class.return_value = mock_synthesizer
        
        mock_manager = Mock()
        mock_manager.initiate_chat.side_effect = Exception("Synthesis error")
        mock_manager_class.return_value = mock_manager
        
        messages = [{"name": "test", "content": "test"}]
        
        with patch('src.business_intelligence.logger') as mock_logger:
            result = run_enhanced_synthesis(messages)
            
            assert "executive_summary" in result
            assert "error" in result["executive_summary"].lower()
            mock_logger.error.assert_called()


class TestToolsIntegration:
    """Test tools integration functions."""

    @patch('src.business_intelligence.create_financial_tool_spec')
    @patch('src.business_intelligence.create_rag_tool_spec')
    @patch('src.business_intelligence.create_web_search_tool_spec')
    @patch('src.business_intelligence.create_database_tool_spec')
    @patch('src.business_intelligence.create_document_tool_spec')
    @patch('src.business_intelligence.create_api_tool_spec')
    def test_create_bi_tools_list_all_tools(self, mock_api, mock_doc, mock_db, 
                                            mock_web, mock_rag, mock_financial):
        """Test that create_bi_tools_list includes all tool types."""
        # Mock each tool spec function
        mock_financial.return_value = {"name": "financial_calculator", "type": "financial"}
        mock_rag.return_value = {"name": "market_research_rag", "type": "rag"}
        mock_web.return_value = {"name": "web_search", "type": "web"}
        mock_db.return_value = {"name": "database_manager", "type": "database"}
        mock_doc.return_value = {"name": "document_generator", "type": "document"}
        mock_api.return_value = {"name": "external_api", "type": "api"}
        
        tools = create_bi_tools_list()
        
        # Verify all tool spec functions were called
        mock_financial.assert_called_once()
        mock_rag.assert_called_once()
        mock_web.assert_called_once()
        mock_db.assert_called_once()
        mock_doc.assert_called_once()
        mock_api.assert_called_once()
        
        # Verify all tools are in the list
        tool_names = [tool["name"] for tool in tools]
        assert "financial_calculator" in tool_names
        assert "market_research_rag" in tool_names
        assert "web_search" in tool_names
        assert "database_manager" in tool_names
        assert "document_generator" in tool_names
        assert "external_api" in tool_names


class TestCapabilities:
    """Test get_bi_capabilities function."""

    def test_get_bi_capabilities(self):
        """Test getting BI platform capabilities."""
        capabilities = get_bi_capabilities()
        
        assert isinstance(capabilities, dict)
        assert "agents" in capabilities
        assert "tools" in capabilities
        assert "workflows" in capabilities
        assert "analysis_modes" in capabilities
        
        # Check agents
        agents = capabilities["agents"]
        assert "economist" in agents
        assert "lawyer" in agents
        assert "sociologist" in agents
        assert "synthesizer" in agents
        
        # Check tools
        tools = capabilities["tools"]
        assert "financial_modeling" in tools
        assert "market_research" in tools
        assert "web_intelligence" in tools
        assert "document_generation" in tools
        assert "database_operations" in tools
        
        # Check workflows
        workflows = capabilities["workflows"]
        assert "sequential_validation" in workflows
        assert "swarm_scenarios" in workflows
        assert "enhanced_synthesis" in workflows
        
        # Check analysis modes
        modes = capabilities["analysis_modes"]
        assert "interactive" in modes
        assert "structured_validation" in modes
        assert "scenario_stress_testing" in modes