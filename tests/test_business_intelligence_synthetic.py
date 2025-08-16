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
    @patch('src.business_intelligence.ConversableAgent.register_for_llm')
    def test_agent_initialization_with_tools(self, mock_register, mock_super_init):
        """Test BusinessIntelligenceAgent initialization with tools."""
        mock_super_init.return_value = None
        mock_register.return_value = lambda x: x  # Mock decorator behavior
        
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
        
        # Verify parent class was initialized correctly
        mock_super_init.assert_called_once_with(
            name="TestAgent",
            system_message="Test message",
            llm_config={"model": "test"},
            human_input_mode="NEVER"
        )
        
        # Verify tools were registered
        assert mock_register.call_count == 2  # One for each tool

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
            agent, "business_database"
        )
        
        with patch('src.business_intelligence.database_tool_executor') as mock_executor:
            mock_executor.return_value = {"success": True}
            
            result = tool_func(query_type="query", params={"sql": "SELECT *"})
            
            assert result == {"success": True}
            mock_executor.assert_called_once_with("query", {"sql": "SELECT *"})

    def test_create_tool_function_document(self):
        """Test creating document tool function."""
        agent = Mock(spec=BusinessIntelligenceAgent)
        
        tool_func = BusinessIntelligenceAgent._create_tool_function(
            agent, "document_generator"
        )
        
        with patch('src.business_intelligence.document_tool_executor') as mock_executor:
            mock_executor.return_value = {"document": "content"}
            
            result = tool_func(document_type="report", data={"data": "test"})
            
            assert result == {"document": "content"}
            mock_executor.assert_called_once_with("report", {"data": "test"})

    def test_create_tool_function_api(self):
        """Test creating API tool function."""
        agent = Mock(spec=BusinessIntelligenceAgent)
        
        tool_func = BusinessIntelligenceAgent._create_tool_function(
            agent, "external_api"
        )
        
        with patch('src.business_intelligence.api_tool_executor') as mock_executor:
            mock_executor.return_value = {"api_response": "data"}
            
            result = tool_func(api_type="test", params={"method": "GET"})
            
            assert result == {"api_response": "data"}
            mock_executor.assert_called_once_with("test", {"method": "GET"})

    def test_create_tool_function_unknown(self):
        """Test creating unknown tool function."""
        agent = Mock(spec=BusinessIntelligenceAgent)
        
        tool_func = BusinessIntelligenceAgent._create_tool_function(
            agent, "unknown_tool"
        )
        
        result = tool_func()
        
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
        mock_db.return_value = {"name": "business_database"}
        mock_doc.return_value = {"name": "document_generator"}
        mock_api.return_value = {"name": "external_api"}
        
        tools = create_bi_tools_list()
        
        assert len(tools) == 6
        assert {"name": "financial_calculator"} in tools
        assert {"name": "market_research_rag"} in tools
        assert {"name": "web_search"} in tools
        assert {"name": "business_database"} in tools
        assert {"name": "document_generator"} in tools
        assert {"name": "external_api"} in tools


class TestBuildBiGroup:
    """Test build_bi_group function."""

    @patch('src.business_intelligence.SwarmScenarioAnalysis')
    @patch('src.business_intelligence.SequentialValidationWorkflow')
    @patch('src.business_intelligence.ConversableAgent')
    @patch('src.business_intelligence.BusinessIntelligenceAgent')
    @patch('src.business_intelligence.GroupChat')
    @patch('src.business_intelligence.GroupChatManager')
    @patch('src.business_intelligence.create_bi_tools_list')
    @patch('src.business_intelligence._anthropic_cfg')
    @patch('src.business_intelligence._compose_system')
    def test_build_bi_group(self, mock_compose, mock_cfg, mock_tools, 
                            mock_manager_class, mock_chat_class, 
                            mock_bi_agent, mock_conv_agent, mock_workflow_class, mock_swarm_class):
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
        
        mock_workflow = Mock()
        mock_workflow_class.return_value = mock_workflow
        mock_swarm = Mock()
        mock_swarm_class.return_value = mock_swarm
        
        result = build_bi_group()
        
        # build_bi_group returns (manager, user_proxy, synthesizer, workflow, swarm)
        assert len(result) == 5
        manager, user_proxy, synthesizer, workflow, swarm = result
        assert manager == mock_manager
        assert user_proxy == mock_user
        assert synthesizer == mock_synthesizer
        assert workflow == mock_workflow
        assert swarm == mock_swarm


class TestWorkflowFunctions:
    """Test workflow execution functions."""

    @patch('src.business_intelligence.build_bi_group')
    def test_run_sequential_validation(self, mock_build_group):
        """Test running sequential validation."""
        mock_workflow = Mock()
        mock_workflow.run_full_validation.return_value = {"result": "validation complete"}
        
        # build_bi_group returns (manager, user_proxy, synthesizer, workflow, swarm)
        mock_build_group.return_value = (Mock(), Mock(), Mock(), mock_workflow, Mock())
        
        business_data = {"idea": "AI startup", "market": "B2B"}
        result = run_sequential_validation(business_data)
        
        assert result == {"result": "validation complete"}
        mock_workflow.run_full_validation.assert_called_once_with(business_data)

    @patch('src.business_intelligence.build_bi_group')
    def test_run_swarm_analysis(self, mock_build_group):
        """Test running swarm analysis."""
        mock_swarm = Mock()
        mock_swarm.run_swarm_analysis.return_value = {"scenario_results": "complete"}
        mock_swarm.synthesize_swarm_results.return_value = {"synthesis": "complete"}
        
        # build_bi_group returns (manager, user_proxy, synthesizer, workflow, swarm)
        mock_build_group.return_value = (Mock(), Mock(), Mock(), Mock(), mock_swarm)
        
        business_data = {"idea": "Tech startup"}
        scenarios = ["optimistic", "pessimistic"]
        
        result = run_swarm_analysis(business_data, scenarios)
        
        assert result == {"synthesis": "complete"}
        mock_swarm.run_swarm_analysis.assert_called_once()
        mock_swarm.synthesize_swarm_results.assert_called_once()

    @patch('src.business_intelligence.build_bi_group')
    @patch('src.business_intelligence.document_tool_executor')
    def test_run_enhanced_synthesis_success(self, mock_doc_executor, mock_build_group):
        """Test successful enhanced synthesis."""
        # Mock synthesizer agent
        mock_synthesizer = Mock()
        mock_synthesizer.generate_reply.return_value = "Comprehensive business analysis summary"
        
        # build_bi_group returns (manager, user_proxy, synthesizer, workflow, swarm)
        mock_build_group.return_value = (Mock(), Mock(), mock_synthesizer, Mock(), Mock())
        
        # Mock document generation
        mock_doc_executor.return_value = {
            "document_type": "executive_summary",
            "filename": "test_summary.md",
            "content": "Document content"
        }
        
        messages = [
            {"role": "user", "content": "Analyze my business idea"},
            {"role": "economist", "content": "Economic analysis"}
        ]
        
        result = run_enhanced_synthesis(messages)
        
        assert result["synthesis_response"] == "Comprehensive business analysis summary"
        assert result["analysis_complete"] is True
        assert len(result["generated_documents"]) == 1
        mock_synthesizer.generate_reply.assert_called_once_with(messages=messages)

    @patch('src.business_intelligence.build_bi_group')
    @patch('src.business_intelligence.document_tool_executor')
    def test_run_enhanced_synthesis_json_error(self, mock_doc_executor, mock_build_group):
        """Test enhanced synthesis with document generation error."""
        mock_synthesizer = Mock()
        mock_synthesizer.generate_reply.return_value = "Analysis response"
        
        # build_bi_group returns (manager, user_proxy, synthesizer, workflow, swarm)
        mock_build_group.return_value = (Mock(), Mock(), mock_synthesizer, Mock(), Mock())
        
        # Mock document generation failure
        mock_doc_executor.side_effect = Exception("Document generation failed")
        
        messages = [{"role": "user", "content": "test"}]
        
        result = run_enhanced_synthesis(messages)
        
        assert result["synthesis_response"] == "Analysis response"
        assert result["generated_documents"] == []
        assert "document_error" in result

    @patch('src.business_intelligence.build_bi_group')
    def test_run_enhanced_synthesis_exception(self, mock_build_group):
        """Test enhanced synthesis with exception."""
        mock_synthesizer = Mock()
        mock_synthesizer.generate_reply.side_effect = Exception("Synthesis error")
        
        # build_bi_group returns (manager, user_proxy, synthesizer, workflow, swarm)
        mock_build_group.return_value = (Mock(), Mock(), mock_synthesizer, Mock(), Mock())
        
        messages = [{"role": "user", "content": "test"}]
        
        # The actual function doesn't have error handling, so it should raise
        with pytest.raises(Exception, match="Synthesis error"):
            run_enhanced_synthesis(messages)


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
        mock_db.return_value = {"name": "business_database", "type": "database"}
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
        assert "business_database" in tool_names
        assert "document_generator" in tool_names
        assert "external_api" in tool_names


class TestCapabilities:
    """Test get_bi_capabilities function."""

    def test_get_bi_capabilities(self):
        """Test getting BI platform capabilities."""
        capabilities = get_bi_capabilities()
        
        assert isinstance(capabilities, dict)
        assert "tools_available" in capabilities
        assert "tool_categories" in capabilities
        assert "workflows_available" in capabilities
        assert "specialized_agents" in capabilities
        assert "document_types" in capabilities
        
        # Check tools available count
        assert capabilities["tools_available"] == 6
        
        # Check tool categories
        categories = capabilities["tool_categories"]
        assert "Financial Modeling & Analysis" in categories
        assert "Market Research & RAG" in categories
        assert "Web Intelligence & Search" in categories
        assert "Document Generation" in categories
        
        # Check workflows
        workflows = capabilities["workflows_available"]
        assert "Sequential Validation (7 phases)" in workflows
        assert "Swarm Scenario Analysis (8 scenario types)" in workflows
        assert "Enhanced Group Chat with Tools" in workflows
        
        # Check specialized agents
        agents = capabilities["specialized_agents"]
        assert "Economist (with financial tools)" in agents
        assert "Lawyer (with regulatory tools)" in agents
        
        # Check document types
        doc_types = capabilities["document_types"]
        assert "Business Plans" in doc_types
        assert "Market Analysis Reports" in doc_types