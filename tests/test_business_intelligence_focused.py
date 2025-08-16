"""
Focused synthetic tests for business_intelligence.py core functions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Only import what actually exists
from src.business_intelligence import (
    create_bi_tools_list,
    get_bi_capabilities,
    BusinessIntelligenceAgent,
    build_bi_group,
    run_sequential_validation,
    run_swarm_analysis,
    run_enhanced_synthesis
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

    @patch('src.business_intelligence.ConversableAgent.__init__')
    @patch.object(BusinessIntelligenceAgent, 'register_for_llm')
    def test_agent_init_with_tools(self, mock_register, mock_super_init):
        """Test agent initialization with tools."""
        mock_super_init.return_value = None
        mock_register.return_value = lambda func: func  # Mock decorator
        
        tools = [
            {"name": "financial_calculator", "description": "Financial tool"},
            {"name": "market_research_rag", "description": "RAG tool"},
            {"name": "web_search", "description": "Web search tool"}
        ]
        
        agent = BusinessIntelligenceAgent(
            name="TestAgent",
            system_message="Test message", 
            llm_config={"model": "test"},
            tools=tools
        )
        
        # Verify tools were registered
        assert mock_register.call_count == len(tools)

    @patch('src.business_intelligence.ConversableAgent.__init__')
    def test_create_tool_function_financial_calculator(self, mock_super_init):
        """Test _create_tool_function for financial_calculator."""
        mock_super_init.return_value = None
        
        agent = BusinessIntelligenceAgent(
            name="TestAgent",
            system_message="Test message", 
            llm_config={"model": "test"}
        )
        
        with patch('src.business_intelligence.financial_tool_executor') as mock_executor:
            mock_executor.return_value = {"result": "success"}
            
            func = agent._create_tool_function("financial_calculator")
            result = func("operation", {"param": "value"})
            
            assert result == {"result": "success"}
            mock_executor.assert_called_once_with("operation", {"param": "value"})

    @patch('src.business_intelligence.ConversableAgent.__init__')
    def test_create_tool_function_financial_calculator_error(self, mock_super_init):
        """Test _create_tool_function for financial_calculator with error."""
        mock_super_init.return_value = None
        
        agent = BusinessIntelligenceAgent(
            name="TestAgent",
            system_message="Test message", 
            llm_config={"model": "test"}
        )
        
        with patch('src.business_intelligence.financial_tool_executor') as mock_executor:
            mock_executor.side_effect = Exception("Tool error")
            
            func = agent._create_tool_function("financial_calculator")
            result = func("operation", {"param": "value"})
            
            assert "error" in result
            assert "Financial tool execution failed" in result["error"]

    @patch('src.business_intelligence.ConversableAgent.__init__')
    def test_create_tool_function_market_research_rag(self, mock_super_init):
        """Test _create_tool_function for market_research_rag."""
        mock_super_init.return_value = None
        
        agent = BusinessIntelligenceAgent(
            name="TestAgent",
            system_message="Test message", 
            llm_config={"model": "test"}
        )
        
        with patch('src.business_intelligence.rag_tool_executor') as mock_executor:
            mock_executor.return_value = {"data": "rag_result"}
            
            func = agent._create_tool_function("market_research_rag")
            result = func("search", {"query": "test"})
            
            assert result == {"data": "rag_result"}
            mock_executor.assert_called_once_with("search", {"query": "test"})

    @patch('src.business_intelligence.ConversableAgent.__init__')
    def test_create_tool_function_market_research_rag_error(self, mock_super_init):
        """Test _create_tool_function for market_research_rag with error."""
        mock_super_init.return_value = None
        
        agent = BusinessIntelligenceAgent(
            name="TestAgent",
            system_message="Test message", 
            llm_config={"model": "test"}
        )
        
        with patch('src.business_intelligence.rag_tool_executor') as mock_executor:
            mock_executor.side_effect = Exception("RAG error")
            
            func = agent._create_tool_function("market_research_rag")
            result = func("search", {"query": "test"})
            
            assert "error" in result
            assert "RAG tool execution failed" in result["error"]

    @patch('src.business_intelligence.ConversableAgent.__init__')
    def test_create_tool_function_web_search(self, mock_super_init):
        """Test _create_tool_function for web_search."""
        mock_super_init.return_value = None
        
        agent = BusinessIntelligenceAgent(
            name="TestAgent",
            system_message="Test message", 
            llm_config={"model": "test"}
        )
        
        with patch('src.business_intelligence.web_search_executor') as mock_executor:
            mock_executor.return_value = {"results": ["result1", "result2"]}
            
            func = agent._create_tool_function("web_search")
            result = func("search", {"query": "test search"})
            
            assert result == {"results": ["result1", "result2"]}
            mock_executor.assert_called_once_with("search", {"query": "test search"})

    @patch('src.business_intelligence.ConversableAgent.__init__')
    def test_create_tool_function_web_search_error(self, mock_super_init):
        """Test _create_tool_function for web_search with error."""
        mock_super_init.return_value = None
        
        agent = BusinessIntelligenceAgent(
            name="TestAgent",
            system_message="Test message", 
            llm_config={"model": "test"}
        )
        
        with patch('src.business_intelligence.web_search_executor') as mock_executor:
            mock_executor.side_effect = Exception("Web search error")
            
            func = agent._create_tool_function("web_search")
            result = func("search", {"query": "test search"})
            
            assert "error" in result
            assert "Web search tool execution failed" in result["error"]

    @patch('src.business_intelligence.ConversableAgent.__init__')
    def test_create_tool_function_business_database(self, mock_super_init):
        """Test _create_tool_function for business_database."""
        mock_super_init.return_value = None
        
        agent = BusinessIntelligenceAgent(
            name="TestAgent",
            system_message="Test message", 
            llm_config={"model": "test"}
        )
        
        with patch('src.business_intelligence.database_tool_executor') as mock_executor:
            mock_executor.return_value = {"data": "database_result"}
            
            func = agent._create_tool_function("business_database")
            result = func("query", {"table": "ventures"})
            
            assert result == {"data": "database_result"}
            mock_executor.assert_called_once_with("query", {"table": "ventures"})

    @patch('src.business_intelligence.ConversableAgent.__init__')
    def test_create_tool_function_business_database_error(self, mock_super_init):
        """Test _create_tool_function for business_database with error."""
        mock_super_init.return_value = None
        
        agent = BusinessIntelligenceAgent(
            name="TestAgent",
            system_message="Test message", 
            llm_config={"model": "test"}
        )
        
        with patch('src.business_intelligence.database_tool_executor') as mock_executor:
            mock_executor.side_effect = Exception("Database error")
            
            func = agent._create_tool_function("business_database")
            result = func("query", {"table": "ventures"})
            
            assert "error" in result
            assert "Database tool execution failed" in result["error"]

    @patch('src.business_intelligence.ConversableAgent.__init__')
    def test_create_tool_function_document_generator(self, mock_super_init):
        """Test _create_tool_function for document_generator."""
        mock_super_init.return_value = None
        
        agent = BusinessIntelligenceAgent(
            name="TestAgent",
            system_message="Test message", 
            llm_config={"model": "test"}
        )
        
        with patch('src.business_intelligence.document_tool_executor') as mock_executor:
            mock_executor.return_value = {"document": "generated"}
            
            func = agent._create_tool_function("document_generator")
            result = func("business_plan", {"name": "Test Corp"})
            
            assert result == {"document": "generated"}
            mock_executor.assert_called_once_with("business_plan", {"name": "Test Corp"})

    @patch('src.business_intelligence.ConversableAgent.__init__')
    def test_create_tool_function_document_generator_error(self, mock_super_init):
        """Test _create_tool_function for document_generator with error."""
        mock_super_init.return_value = None
        
        agent = BusinessIntelligenceAgent(
            name="TestAgent",
            system_message="Test message", 
            llm_config={"model": "test"}
        )
        
        with patch('src.business_intelligence.document_tool_executor') as mock_executor:
            mock_executor.side_effect = Exception("Document error")
            
            func = agent._create_tool_function("document_generator")
            result = func("business_plan", {"name": "Test Corp"})
            
            assert "error" in result
            assert "Document generator execution failed" in result["error"]

    @patch('src.business_intelligence.ConversableAgent.__init__')
    def test_create_tool_function_external_api(self, mock_super_init):
        """Test _create_tool_function for external_api."""
        mock_super_init.return_value = None
        
        agent = BusinessIntelligenceAgent(
            name="TestAgent",
            system_message="Test message", 
            llm_config={"model": "test"}
        )
        
        with patch('src.business_intelligence.api_tool_executor') as mock_executor:
            mock_executor.return_value = {"api_data": "result"}
            
            func = agent._create_tool_function("external_api")
            result = func("company_data", {"company": "TestCorp"})
            
            assert result == {"api_data": "result"}
            mock_executor.assert_called_once_with("company_data", {"company": "TestCorp"})

    @patch('src.business_intelligence.ConversableAgent.__init__')
    def test_create_tool_function_external_api_error(self, mock_super_init):
        """Test _create_tool_function for external_api with error."""
        mock_super_init.return_value = None
        
        agent = BusinessIntelligenceAgent(
            name="TestAgent",
            system_message="Test message", 
            llm_config={"model": "test"}
        )
        
        with patch('src.business_intelligence.api_tool_executor') as mock_executor:
            mock_executor.side_effect = Exception("API error")
            
            func = agent._create_tool_function("external_api")
            result = func("company_data", {"company": "TestCorp"})
            
            assert "error" in result
            assert "External API execution failed" in result["error"]

    @patch('src.business_intelligence.ConversableAgent.__init__')
    def test_create_tool_function_unknown_tool(self, mock_super_init):
        """Test _create_tool_function for unknown tool."""
        mock_super_init.return_value = None
        
        agent = BusinessIntelligenceAgent(
            name="TestAgent",
            system_message="Test message", 
            llm_config={"model": "test"}
        )
        
        func = agent._create_tool_function("unknown_tool_name")
        result = func()
        
        assert "error" in result
        assert "Unknown tool: unknown_tool_name" in result["error"]


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


class TestBuildBiGroup:
    """Test build_bi_group function."""

    @patch('src.business_intelligence._anthropic_cfg')
    @patch('src.business_intelligence._compose_system')
    @patch('src.business_intelligence.logger')
    def test_build_bi_group_success(self, mock_logger, mock_compose, mock_anthropic):
        """Test successful build_bi_group execution."""
        mock_anthropic.return_value = {"model": "claude", "api_key": "test"}
        mock_compose.return_value = "System message"
        
        with patch('src.business_intelligence.settings') as mock_settings:
            mock_settings.model_specialists = "claude-3-sonnet"
            mock_settings.model_synth = "claude-3-sonnet"
            mock_settings.temperature_economist = 0.7
            mock_settings.temperature_lawyer = 0.5
            mock_settings.temperature_sociologist = 0.6
            mock_settings.temperature_synth = 0.4
            mock_settings.max_tokens_specialists = 4000
            mock_settings.max_tokens_synth = 4000
            mock_settings.top_p = 0.9
            
            with patch('src.business_intelligence.BusinessIntelligenceAgent') as mock_agent:
                with patch('src.business_intelligence.ConversableAgent') as mock_user:
                    with patch('src.business_intelligence.GroupChat') as mock_chat:
                        with patch('src.business_intelligence.GroupChatManager') as mock_manager:
                            with patch('src.business_intelligence.SequentialValidationWorkflow') as mock_workflow:
                                with patch('src.business_intelligence.SwarmScenarioAnalysis') as mock_swarm:
                                    
                                    # Mock instances
                                    mock_agent_instance = Mock()
                                    mock_agent.return_value = mock_agent_instance
                                    mock_user_instance = Mock()
                                    mock_user.return_value = mock_user_instance
                                    mock_chat_instance = Mock()
                                    mock_chat.return_value = mock_chat_instance
                                    mock_manager_instance = Mock()
                                    mock_manager.return_value = mock_manager_instance
                                    mock_workflow_instance = Mock()
                                    mock_workflow.return_value = mock_workflow_instance
                                    mock_swarm_instance = Mock()
                                    mock_swarm.return_value = mock_swarm_instance
                                    
                                    result = build_bi_group()
                                    
                                    assert len(result) == 5
                                    manager, user_proxy, synthesizer, workflow, swarm = result
                                    
                                    # Verify components were created
                                    assert mock_agent.call_count == 4  # economist, lawyer, sociologist, synthesizer
                                    mock_user.assert_called_once()
                                    mock_chat.assert_called_once()
                                    mock_manager.assert_called_once()
                                    mock_workflow.assert_called_once()
                                    mock_swarm.assert_called_once()

    @patch('src.business_intelligence.logger')
    def test_build_bi_group_cached_result(self, mock_logger):
        """Test that build_bi_group returns cached result on second call."""
        # Reset global variables first
        import src.business_intelligence as bi
        bi._bi_manager = Mock()
        bi._bi_user_proxy = Mock()
        bi._bi_synthesizer = Mock()
        bi._bi_workflow = Mock()
        bi._bi_swarm = Mock()
        
        result = build_bi_group()
        
        assert len(result) == 5
        # Should return cached instances
        assert result[0] == bi._bi_manager
        assert result[1] == bi._bi_user_proxy
        assert result[2] == bi._bi_synthesizer
        assert result[3] == bi._bi_workflow
        assert result[4] == bi._bi_swarm
        
        # Reset for other tests
        bi._bi_manager = None
        bi._bi_user_proxy = None
        bi._bi_synthesizer = None
        bi._bi_workflow = None
        bi._bi_swarm = None

    @patch('src.business_intelligence.logger')
    def test_build_bi_group_error_handling(self, mock_logger):
        """Test build_bi_group error handling."""
        # Reset global variables
        import src.business_intelligence as bi
        bi._bi_manager = None
        
        with patch('src.business_intelligence.create_bi_tools_list') as mock_tools:
            mock_tools.side_effect = Exception("Tools creation failed")
            
            with pytest.raises(Exception):
                build_bi_group()

    def test_build_bi_group_prompt_creation(self):
        """Test that enhanced prompts are created correctly."""
        with patch('src.business_intelligence.economist_prompt') as mock_econ:
            with patch('src.business_intelligence.lawyer_prompt') as mock_law:
                with patch('src.business_intelligence.sociologist_prompt') as mock_soc:
                    with patch('src.business_intelligence.synthesizer_prompt') as mock_synth:
                        mock_econ.return_value = "Economist prompt"
                        mock_law.return_value = "Lawyer prompt"
                        mock_soc.return_value = "Sociologist prompt"
                        mock_synth.return_value = "Synthesizer prompt"
                        
                        with patch('src.business_intelligence._anthropic_cfg') as mock_cfg:
                            with patch('src.business_intelligence._compose_system') as mock_compose:
                                with patch('src.business_intelligence.BusinessIntelligenceAgent'):
                                    with patch('src.business_intelligence.ConversableAgent'):
                                        with patch('src.business_intelligence.GroupChat'):
                                            with patch('src.business_intelligence.GroupChatManager'):
                                                with patch('src.business_intelligence.SequentialValidationWorkflow'):
                                                    with patch('src.business_intelligence.SwarmScenarioAnalysis'):
                                                        with patch('src.business_intelligence.settings'):
                                                            
                                                            build_bi_group()
                                                            
                                                            # Verify prompts were called
                                                            mock_econ.assert_called_once()
                                                            mock_law.assert_called_once()
                                                            mock_soc.assert_called_once()
                                                            mock_synth.assert_called_once()


class TestRunSequentialValidation:
    """Test run_sequential_validation function."""

    @patch('src.business_intelligence.build_bi_group')
    def test_run_sequential_validation_success(self, mock_build):
        """Test successful sequential validation run."""
        mock_workflow = Mock()
        mock_workflow.run_full_validation.return_value = {"result": "validation_complete"}
        mock_build.return_value = (None, None, None, mock_workflow, None)
        
        business_data = {"name": "Test Business"}
        result = run_sequential_validation(business_data)
        
        assert result == {"result": "validation_complete"}
        mock_workflow.run_full_validation.assert_called_once_with(business_data)

    @patch('src.business_intelligence.build_bi_group')
    def test_run_sequential_validation_workflow_error(self, mock_build):
        """Test sequential validation with workflow error."""
        mock_workflow = Mock()
        mock_workflow.run_full_validation.side_effect = Exception("Workflow failed")
        mock_build.return_value = (None, None, None, mock_workflow, None)
        
        business_data = {"name": "Test Business"}
        
        with pytest.raises(Exception):
            run_sequential_validation(business_data)


class TestRunSwarmAnalysis:
    """Test run_swarm_analysis function."""

    @patch('src.business_intelligence.build_bi_group')
    def test_run_swarm_analysis_success(self, mock_build):
        """Test successful swarm analysis run."""
        mock_swarm = Mock()
        mock_swarm.run_swarm_analysis.return_value = {"scenario_results": "data"}
        mock_swarm.synthesize_swarm_results.return_value = {"synthesis": "complete"}
        mock_build.return_value = (None, None, None, None, mock_swarm)
        
        business_data = {"name": "Test Business"}
        result = run_swarm_analysis(business_data)
        
        assert result == {"synthesis": "complete"}
        mock_swarm.run_swarm_analysis.assert_called_once_with(business_data, None)
        mock_swarm.synthesize_swarm_results.assert_called_once()

    @patch('src.business_intelligence.build_bi_group')
    def test_run_swarm_analysis_with_scenarios(self, mock_build):
        """Test swarm analysis with specific scenarios."""
        mock_swarm = Mock()
        mock_swarm.run_swarm_analysis.return_value = {"scenario_results": "data"}
        mock_swarm.synthesize_swarm_results.return_value = {"synthesis": "complete"}
        mock_build.return_value = (None, None, None, None, mock_swarm)
        
        business_data = {"name": "Test Business"}
        scenarios = ["optimistic", "pessimistic"]
        
        with patch('src.workflows.swarm_scenarios.ScenarioType') as mock_scenario_type:
            mock_scenario_type.side_effect = lambda x: f"scenario_{x}"
            
            result = run_swarm_analysis(business_data, scenarios)
            
            assert result == {"synthesis": "complete"}
            mock_swarm.run_swarm_analysis.assert_called_once()

    @patch('src.business_intelligence.build_bi_group')
    def test_run_swarm_analysis_invalid_scenarios(self, mock_build):
        """Test swarm analysis with invalid scenarios."""
        mock_swarm = Mock()
        mock_swarm.run_swarm_analysis.return_value = {"scenario_results": "data"}
        mock_swarm.synthesize_swarm_results.return_value = {"synthesis": "complete"}
        mock_build.return_value = (None, None, None, None, mock_swarm)
        
        business_data = {"name": "Test Business"}
        scenarios = ["invalid_scenario", "another_invalid"]
        
        with patch('src.workflows.swarm_scenarios.ScenarioType') as mock_scenario_type:
            mock_scenario_type.side_effect = ValueError("Invalid scenario")
            
            result = run_swarm_analysis(business_data, scenarios)
            
            # Should still complete with empty scenario list
            assert result == {"synthesis": "complete"}


class TestRunEnhancedSynthesis:
    """Test run_enhanced_synthesis function."""

    @patch('src.business_intelligence.build_bi_group')
    @patch('src.business_intelligence.document_tool_executor')
    def test_run_enhanced_synthesis_success(self, mock_doc_executor, mock_build):
        """Test successful enhanced synthesis."""
        mock_synthesizer = Mock()
        mock_synthesizer.generate_reply.return_value = "Synthesis response text"
        mock_build.return_value = (None, None, mock_synthesizer, None, None)
        mock_doc_executor.return_value = {"document": "executive_summary"}
        
        messages = [{"content": "Test message"}]
        result = run_enhanced_synthesis(messages)
        
        assert "synthesis_response" in result
        assert "generated_documents" in result
        assert "analysis_complete" in result
        assert result["analysis_complete"] is True
        assert result["synthesis_response"] == "Synthesis response text"
        assert len(result["generated_documents"]) == 1

    @patch('src.business_intelligence.build_bi_group')
    @patch('src.business_intelligence.document_tool_executor')
    def test_run_enhanced_synthesis_document_error(self, mock_doc_executor, mock_build):
        """Test enhanced synthesis with document generation error."""
        mock_synthesizer = Mock()
        mock_synthesizer.generate_reply.return_value = "Synthesis response text"
        mock_build.return_value = (None, None, mock_synthesizer, None, None)
        mock_doc_executor.side_effect = Exception("Document generation failed")
        
        messages = [{"content": "Test message"}]
        result = run_enhanced_synthesis(messages)
        
        assert "synthesis_response" in result
        assert "generated_documents" in result
        assert "analysis_complete" in result
        assert "document_error" in result
        assert result["analysis_complete"] is True
        assert result["synthesis_response"] == "Synthesis response text"
        assert result["generated_documents"] == []
        assert "Document generation failed" in result["document_error"]

    @patch('src.business_intelligence.build_bi_group')
    def test_run_enhanced_synthesis_synthesizer_error(self, mock_build):
        """Test enhanced synthesis with synthesizer error."""
        mock_synthesizer = Mock()
        mock_synthesizer.generate_reply.side_effect = Exception("Synthesis failed")
        mock_build.return_value = (None, None, mock_synthesizer, None, None)
        
        messages = [{"content": "Test message"}]
        
        with pytest.raises(Exception):
            run_enhanced_synthesis(messages)


class TestIntegration:
    """Test integration scenarios."""

    def test_all_functions_importable(self):
        """Test that all main functions can be imported."""
        try:
            from src.business_intelligence import (
                create_bi_tools_list,
                get_bi_capabilities,
                BusinessIntelligenceAgent,
                build_bi_group,
                run_sequential_validation,
                run_swarm_analysis,
                run_enhanced_synthesis
            )
            assert True
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    def test_module_level_constants(self):
        """Test module level constants and globals."""
        import src.business_intelligence as bi
        
        # Check that global variables exist
        assert hasattr(bi, '_bi_manager')
        assert hasattr(bi, '_bi_user_proxy')
        assert hasattr(bi, '_bi_synthesizer')
        assert hasattr(bi, '_bi_workflow')
        assert hasattr(bi, '_bi_swarm')

    @patch('src.business_intelligence._anthropic_cfg')
    @patch('src.business_intelligence.logger')
    def test_build_bi_group_complex_integration(self, mock_logger, mock_anthropic):
        """Test complex integration of build_bi_group with all components."""
        mock_anthropic.return_value = {"model": "claude", "api_key": "test"}
        
        with patch('src.business_intelligence.settings') as mock_settings:
            # Set all required settings
            mock_settings.model_specialists = "claude-3-sonnet"
            mock_settings.model_synth = "claude-3-sonnet"
            mock_settings.temperature_economist = 0.7
            mock_settings.temperature_lawyer = 0.5
            mock_settings.temperature_sociologist = 0.6
            mock_settings.temperature_synth = 0.4
            mock_settings.max_tokens_specialists = 4000
            mock_settings.max_tokens_synth = 4000
            mock_settings.top_p = 0.9
            
            with patch('src.business_intelligence.create_bi_tools_list') as mock_tools:
                mock_tools.return_value = [
                    {"name": "financial_calculator", "description": "Financial tool"},
                    {"name": "web_search", "description": "Web search"}
                ]
                
                with patch('src.business_intelligence.BusinessIntelligenceAgent') as mock_agent:
                    with patch('src.business_intelligence.ConversableAgent') as mock_user:
                        with patch('src.business_intelligence.GroupChat') as mock_chat:
                            with patch('src.business_intelligence.GroupChatManager') as mock_manager:
                                with patch('src.business_intelligence.SequentialValidationWorkflow') as mock_workflow:
                                    with patch('src.business_intelligence.SwarmScenarioAnalysis') as mock_swarm:
                                        with patch('src.business_intelligence._compose_system') as mock_compose:
                                            
                                            # Mock all prompt functions
                                            with patch('src.business_intelligence.economist_prompt') as mock_econ:
                                                with patch('src.business_intelligence.lawyer_prompt') as mock_law:
                                                    with patch('src.business_intelligence.sociologist_prompt') as mock_soc:
                                                        with patch('src.business_intelligence.synthesizer_prompt') as mock_synth:
                                                            
                                                            mock_econ.return_value = "Economist"
                                                            mock_law.return_value = "Lawyer" 
                                                            mock_soc.return_value = "Sociologist"
                                                            mock_synth.return_value = "Synthesizer"
                                                            mock_compose.return_value = "System message"
                                                            
                                                            # Reset globals for clean test
                                                            import src.business_intelligence as bi
                                                            bi._bi_manager = None
                                                            bi._bi_user_proxy = None
                                                            bi._bi_synthesizer = None
                                                            bi._bi_workflow = None
                                                            bi._bi_swarm = None
                                                            
                                                            result = build_bi_group()
                                                            
                                                            # Verify comprehensive setup
                                                            assert len(result) == 5
                                                            assert mock_tools.called
                                                            assert mock_agent.call_count == 4
                                                            assert mock_user.called
                                                            assert mock_chat.called
                                                            assert mock_manager.called
                                                            assert mock_workflow.called
                                                            assert mock_swarm.called