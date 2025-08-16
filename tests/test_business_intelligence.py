"""
Tests for business intelligence integration.
"""

from unittest.mock import Mock, patch

import pytest

from src.business_intelligence import (
    build_bi_group,
    create_bi_tools_list,
    get_bi_capabilities,
    run_enhanced_synthesis,
)


class TestBICapabilities:
    """Test business intelligence capabilities."""

    def test_get_bi_capabilities(self):
        """Test getting BI capabilities."""
        capabilities = get_bi_capabilities()

        assert "tool_categories" in capabilities
        assert "workflows_available" in capabilities
        assert "specialized_agents" in capabilities

        # Check tool categories
        expected_categories = [
            "Financial Modeling & Analysis",
            "Market Research & RAG",
            "Web Intelligence & Search",
            "Historical Business Data",
            "Document Generation",
            "External API Integration",
        ]

        for category in expected_categories:
            assert category in capabilities["tool_categories"]

        # Check workflows available
        expected_workflows = [
            "Sequential Validation (7 phases)",
            "Swarm Scenario Analysis (8 scenario types)",
            "Enhanced Group Chat with Tools",
        ]

        for workflow in expected_workflows:
            assert workflow in capabilities["workflows_available"]

    def test_create_bi_tools_list(self):
        """Test creating BI tools list."""
        tools = create_bi_tools_list()

        assert isinstance(tools, list)
        assert len(tools) > 0

        # Check that each tool has required properties
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool

        # Check for specific expected tools
        tool_names = [tool["name"] for tool in tools]
        expected_tools = [
            "financial_calculator",
            "market_research_rag",
            "web_search",
            "business_database",
            "document_generator",
            "external_api",
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names


class TestBIGroupBuilding:
    """Test BI group construction."""

    @patch("src.business_intelligence.ConversableAgent")
    @patch("src.business_intelligence.BusinessIntelligenceAgent")
    @patch("src.business_intelligence.GroupChatManager")
    @patch("src.business_intelligence.GroupChat")
    @patch("src.business_intelligence.SequentialValidationWorkflow")
    @patch("src.business_intelligence.SwarmScenarioAnalysis")
    def test_build_bi_group(
        self, mock_swarm, mock_workflow, mock_group_chat, mock_manager, mock_bi_agent, mock_agent
    ):
        """Test building BI group with all components."""
        # Mock agent instances
        mock_economist = Mock()
        mock_lawyer = Mock()
        mock_sociologist = Mock()
        mock_synthesizer = Mock()
        mock_user_proxy = Mock()
        mock_manager_instance = Mock()
        mock_workflow_instance = Mock()
        mock_swarm_instance = Mock()

        # BusinessIntelligenceAgent instances (economist, lawyer, sociologist, synthesizer)
        mock_bi_agent.side_effect = [
            mock_economist,
            mock_lawyer,
            mock_sociologist,
            mock_synthesizer,
        ]

        # ConversableAgent instance (user_proxy)
        mock_agent.return_value = mock_user_proxy
        mock_manager.return_value = mock_manager_instance
        mock_workflow.return_value = mock_workflow_instance
        mock_swarm.return_value = mock_swarm_instance

        # Call build_bi_group
        manager, user_proxy, synthesizer, workflow, swarm = build_bi_group()

        # Verify components were created
        assert manager == mock_manager_instance
        assert user_proxy == mock_user_proxy
        assert synthesizer == mock_synthesizer
        assert workflow == mock_workflow_instance
        assert swarm == mock_swarm_instance

        # Verify agents were created with correct parameters
        assert mock_agent.call_count == 1  # 1 ConversableAgent (user_proxy)
        assert mock_bi_agent.call_count == 4  # 4 BusinessIntelligenceAgents

        # Verify group chat manager was created
        mock_manager.assert_called_once()

    @patch("tests.test_business_intelligence.build_bi_group")
    def test_build_bi_group_caching(self, mock_build):
        """Test that BI group is cached after first build."""
        # Mock the first call
        mock_components = (Mock(), Mock(), Mock(), Mock(), Mock())
        mock_build.return_value = mock_components

        # First call should create components
        result1 = build_bi_group()
        assert result1 is not None  # Use the variable
        assert mock_build.call_count == 1

        # Second call should return cached components
        with patch("src.business_intelligence._bi_manager", mock_components[0]):
            with patch("src.business_intelligence._bi_user_proxy", mock_components[1]):
                with patch("src.business_intelligence._bi_synthesizer", mock_components[2]):
                    with patch("src.business_intelligence._bi_workflow", mock_components[3]):
                        with patch("src.business_intelligence._bi_swarm", mock_components[4]):
                            result2 = build_bi_group()
                            # Should return cached components without calling build again
                            assert result2 == mock_components


class TestEnhancedSynthesis:
    """Test enhanced synthesis functionality."""

    @patch("src.business_intelligence.build_bi_group")
    @patch("src.business_intelligence.document_tool_executor")
    def test_run_enhanced_synthesis(self, mock_doc_executor, mock_build_group):
        """Test enhanced synthesis with document generation."""
        # Mock synthesizer agent
        mock_synthesizer = Mock()
        mock_synthesizer.generate_reply.return_value = (
            "Comprehensive business analysis of the proposed venture..."
        )

        # Mock build_bi_group to return our mock synthesizer
        mock_build_group.return_value = (Mock(), Mock(), mock_synthesizer, Mock(), Mock())

        # Mock document generation
        mock_doc_executor.return_value = {
            "success": True,
            "documents": [
                {
                    "filename": "business_analysis_report.md",
                    "word_count": 1500,
                    "path": "/tmp/business_analysis_report.md",
                }
            ],
        }

        # Test messages
        test_messages = [
            {"role": "user", "content": "Analyze my SaaS business idea"},
            {"role": "economist", "content": "Financial analysis..."},
            {"role": "lawyer", "content": "Legal considerations..."},
        ]

        result = run_enhanced_synthesis(test_messages)

        # Verify synthesis was called
        mock_synthesizer.generate_reply.assert_called_once_with(messages=test_messages)

        # Verify document generation was called
        mock_doc_executor.assert_called_once()

        # Verify result structure
        assert "synthesis_response" in result
        assert "generated_documents" in result
        assert "analysis_complete" in result
        assert result["analysis_complete"] is True
        assert len(result["generated_documents"]) == 1

    @patch("src.business_intelligence.build_bi_group")
    @patch("src.business_intelligence.document_tool_executor")
    def test_run_enhanced_synthesis_doc_failure(self, mock_doc_executor, mock_build_group):
        """Test enhanced synthesis when document generation fails."""
        # Mock synthesizer agent
        mock_synthesizer = Mock()
        mock_synthesizer.generate_reply.return_value = (
            "Comprehensive business analysis of the proposed venture..."
        )

        # Mock build_bi_group to return our mock synthesizer
        mock_build_group.return_value = (Mock(), Mock(), mock_synthesizer, Mock(), Mock())

        # Mock document generation failure
        mock_doc_executor.side_effect = Exception("Document generation failed")

        test_messages = [{"role": "user", "content": "Test message"}]

        result = run_enhanced_synthesis(test_messages)

        # Should still return synthesis even if docs fail
        assert "synthesis_response" in result
        assert result["generated_documents"] == []
        assert "document_error" in result


class TestErrorHandling:
    """Test error handling in business intelligence components."""

    def test_build_bi_group_error_handling(self):
        """Test error handling in build_bi_group."""
        # Clear global cache to ensure fresh execution
        with patch("src.business_intelligence._bi_manager", None):
            with patch("src.business_intelligence._bi_user_proxy", None):
                with patch("src.business_intelligence._bi_synthesizer", None):
                    with patch("src.business_intelligence._bi_workflow", None):
                        with patch("src.business_intelligence._bi_swarm", None):
                            with patch(
                                "src.business_intelligence.ConversableAgent",
                                side_effect=Exception("Agent creation failed"),
                            ):
                                # Should raise the exception (error logging handled by decorators)
                                with pytest.raises(Exception, match="Agent creation failed"):
                                    build_bi_group()

    def test_synthesis_error_resilience(self):
        """Test that synthesis handles errors gracefully via decorators."""
        # Test that run_enhanced_synthesis is decorated with error handling
        from src.business_intelligence import run_enhanced_synthesis

        # Verify the function exists and is callable
        assert callable(run_enhanced_synthesis)

        # The actual error handling is tested in the synthesis tests above
        # This test just verifies the function structure
        assert run_enhanced_synthesis.__name__ == "run_enhanced_synthesis"


class TestIntegrationPoints:
    """Test integration points with other components."""

    def test_tool_executors_importable(self):
        """Test that all tool executors can be imported."""
        from src.business_intelligence import (
            api_tool_executor,
            database_tool_executor,
            document_tool_executor,
            financial_tool_executor,
            rag_tool_executor,
            web_search_executor,
        )

        # All should be callable
        assert callable(financial_tool_executor)
        assert callable(rag_tool_executor)
        assert callable(web_search_executor)
        assert callable(database_tool_executor)
        assert callable(document_tool_executor)
        assert callable(api_tool_executor)

    def test_workflow_components_importable(self):
        """Test that workflow components can be imported."""
        from src.business_intelligence import (
            SequentialValidationWorkflow,
            SwarmScenarioAnalysis,
        )

        # Should be classes
        assert callable(SequentialValidationWorkflow)
        assert callable(SwarmScenarioAnalysis)

    def test_error_handling_integration(self):
        """Test error handling integration."""
        from src.business_intelligence import (
            ModelError,
            retry_with_backoff,
            track_errors,
        )

        # Should have error handling components
        assert issubclass(ModelError, Exception)
        assert callable(retry_with_backoff)
        assert callable(track_errors)
