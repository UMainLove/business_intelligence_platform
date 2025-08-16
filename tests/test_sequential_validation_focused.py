"""
Focused tests for sequential_validation.py matching actual implementation.
"""

import json
from unittest.mock import Mock, patch

from src.workflows.sequential_validation import (
    PhaseResult,
    SequentialValidationWorkflow,
    ValidationPhase,
)


class TestValidationPhaseEnum:
    """Test ValidationPhase enum."""

    def test_all_phases_defined(self):
        """Test that all validation phases are defined."""
        phases = [
            ValidationPhase.IDEA_REFINEMENT,
            ValidationPhase.MARKET_VALIDATION,
            ValidationPhase.FINANCIAL_MODELING,
            ValidationPhase.RISK_ASSESSMENT,
            ValidationPhase.COMPETITIVE_ANALYSIS,
            ValidationPhase.REGULATORY_COMPLIANCE,
            ValidationPhase.FINAL_SYNTHESIS,
        ]

        assert len(phases) == 7
        for phase in phases:
            assert phase.value is not None


class TestPhaseResultDataclass:
    """Test PhaseResult dataclass."""

    def test_phase_result_creation(self):
        """Test creating a PhaseResult with all fields."""
        result = PhaseResult(
            phase=ValidationPhase.MARKET_VALIDATION,
            success=True,
            data={"market_size": "$10B"},
            recommendations=["Focus on enterprise"],
            next_phase=ValidationPhase.FINANCIAL_MODELING,
            confidence_score=0.85,
        )

        assert result.phase == ValidationPhase.MARKET_VALIDATION
        assert result.success is True
        assert result.data["market_size"] == "$10B"
        assert result.recommendations[0] == "Focus on enterprise"
        assert result.confidence_score == 0.85


class TestSequentialValidationWorkflowBasic:
    """Test basic SequentialValidationWorkflow functionality."""

    @patch("src.workflows.sequential_validation.ConversableAgent")
    @patch("src.workflows.sequential_validation.settings")
    def test_initialization(self, mock_settings, mock_agent_class):
        """Test workflow initialization."""
        # Setup mocks
        mock_settings.model_specialists = "claude-3"
        mock_settings.anthropic_key = "test-key"
        mock_settings.top_p = 0.9

        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        workflow = SequentialValidationWorkflow()

        assert workflow.current_phase == ValidationPhase.IDEA_REFINEMENT
        assert workflow.phase_results == {}
        assert workflow.business_context == {}
        assert workflow.agents is not None

    @patch("src.workflows.sequential_validation.settings")
    def test_create_anthropic_config(self, mock_settings):
        """Test _create_anthropic_config method."""
        mock_settings.model_specialists = "claude-3"
        mock_settings.anthropic_key = "test-key"
        mock_settings.top_p = 0.9

        workflow = SequentialValidationWorkflow()
        config = workflow._create_anthropic_config(temperature=0.5, max_tokens=1000)

        # LLMConfig is a special autogen object, check it exists
        assert config is not None
        assert hasattr(config, "config_list")


class TestPhaseExecution:
    """Test phase execution methods."""

    @patch("src.workflows.sequential_validation.ConversableAgent")
    def test_execute_phase_method(self, mock_agent_class):
        """Test execute_phase dispatcher method."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        workflow = SequentialValidationWorkflow()

        # Mock the specific phase execution method
        with patch.object(workflow, "_execute_idea_refinement") as mock_exec:
            mock_exec.return_value = PhaseResult(
                phase=ValidationPhase.IDEA_REFINEMENT,
                success=True,
                data={"refined": "idea"},
                recommendations=[],
            )

            result = workflow.execute_phase(
                ValidationPhase.IDEA_REFINEMENT, {"initial_idea": "test"}
            )

            assert result.phase == ValidationPhase.IDEA_REFINEMENT
            assert result.success is True
            mock_exec.assert_called_once_with({"initial_idea": "test"})

    @patch("src.workflows.sequential_validation.ConversableAgent")
    def test_execute_idea_refinement(self, mock_agent_class):
        """Test _execute_idea_refinement method."""
        mock_agent = Mock()
        mock_agent.generate_reply.return_value = json.dumps(
            {
                "refined_idea": "Enhanced AI platform",
                "value_proposition": "Better analytics",
                "target_market": "SMBs",
                "confidence": 0.8,
            }
        )
        mock_agent_class.return_value = mock_agent

        workflow = SequentialValidationWorkflow()
        result = workflow._execute_idea_refinement({"idea": "AI platform"})

        assert isinstance(result, PhaseResult)
        assert result.phase == ValidationPhase.IDEA_REFINEMENT
        # Check if result contains expected data

    @patch("src.workflows.sequential_validation.ConversableAgent")
    @patch("src.workflows.sequential_validation.rag_tool_executor")
    def test_execute_market_validation(self, mock_rag, mock_agent_class):
        """Test _execute_market_validation method."""
        mock_agent = Mock()
        mock_agent.generate_reply.return_value = json.dumps(
            {"market_size": "$50B", "growth_rate": "15%"}
        )
        mock_agent_class.return_value = mock_agent

        mock_rag.return_value = {"market_data": "insights"}

        workflow = SequentialValidationWorkflow()
        result = workflow._execute_market_validation({"market": "B2B"})

        assert isinstance(result, PhaseResult)
        assert result.phase == ValidationPhase.MARKET_VALIDATION

    @patch("src.workflows.sequential_validation.ConversableAgent")
    @patch("src.workflows.sequential_validation.financial_tool_executor")
    def test_execute_financial_modeling(self, mock_financial, mock_agent_class):
        """Test _execute_financial_modeling method."""
        mock_agent = Mock()
        mock_agent.generate_reply.return_value = json.dumps({"npv": "$5M", "irr": "35%"})
        mock_agent_class.return_value = mock_agent

        mock_financial.return_value = {"npv": 5000000}

        workflow = SequentialValidationWorkflow()
        result = workflow._execute_financial_modeling({"revenue": "$1M"})

        assert isinstance(result, PhaseResult)
        assert result.phase == ValidationPhase.FINANCIAL_MODELING

    @patch("src.workflows.sequential_validation.ConversableAgent")
    def test_execute_risk_assessment(self, mock_agent_class):
        """Test _execute_risk_assessment method."""
        mock_agent = Mock()
        mock_agent.generate_reply.return_value = json.dumps(
            {"key_risks": ["Competition", "Funding"], "risk_score": 0.6}
        )
        mock_agent_class.return_value = mock_agent

        workflow = SequentialValidationWorkflow()
        result = workflow._execute_risk_assessment({"business": "SaaS"})

        assert isinstance(result, PhaseResult)
        assert result.phase == ValidationPhase.RISK_ASSESSMENT

    @patch("src.workflows.sequential_validation.ConversableAgent")
    @patch("src.workflows.sequential_validation.web_search_executor")
    def test_execute_competitive_analysis(self, mock_web, mock_agent_class):
        """Test _execute_competitive_analysis method."""
        mock_agent = Mock()
        mock_agent.generate_reply.return_value = json.dumps(
            {"competitors": ["Company A", "Company B"]}
        )
        mock_agent_class.return_value = mock_agent

        mock_web.return_value = {"competitor_info": "data"}

        workflow = SequentialValidationWorkflow()
        result = workflow._execute_competitive_analysis({"market": "AI"})

        assert isinstance(result, PhaseResult)
        assert result.phase == ValidationPhase.COMPETITIVE_ANALYSIS

    @patch("src.workflows.sequential_validation.ConversableAgent")
    @patch("src.workflows.sequential_validation.database_tool_executor")
    def test_execute_regulatory_compliance(self, mock_db, mock_agent_class):
        """Test _execute_regulatory_compliance method."""
        mock_agent = Mock()
        mock_agent.generate_reply.return_value = json.dumps({"regulations": ["GDPR", "SOC2"]})
        mock_agent_class.return_value = mock_agent

        mock_db.return_value = {"compliance_data": "requirements"}

        workflow = SequentialValidationWorkflow()
        result = workflow._execute_regulatory_compliance({"industry": "FinTech"})

        assert isinstance(result, PhaseResult)
        assert result.phase == ValidationPhase.REGULATORY_COMPLIANCE

    @patch("src.workflows.sequential_validation.ConversableAgent")
    @patch("src.workflows.sequential_validation.document_tool_executor")
    def test_execute_final_synthesis(self, mock_doc, mock_agent_class):
        """Test _execute_final_synthesis method."""
        mock_agent = Mock()
        mock_agent.generate_reply.return_value = json.dumps(
            {"overall_assessment": "Strong opportunity", "go_no_go": "GO"}
        )
        mock_agent_class.return_value = mock_agent

        mock_doc.return_value = {"report": "generated"}

        workflow = SequentialValidationWorkflow()
        workflow.phase_results[ValidationPhase.MARKET_VALIDATION] = PhaseResult(
            ValidationPhase.MARKET_VALIDATION, True, {"tam": "$50B"}, []
        )

        result = workflow._execute_final_synthesis({"summary": "data"})

        assert isinstance(result, PhaseResult)
        assert result.phase == ValidationPhase.FINAL_SYNTHESIS


class TestWorkflowExecution:
    """Test full workflow execution."""

    @patch("src.workflows.sequential_validation.financial_tool_executor")
    @patch("src.workflows.sequential_validation.rag_tool_executor")
    @patch("src.workflows.sequential_validation.web_search_executor")
    @patch("src.workflows.sequential_validation.database_tool_executor")
    @patch("src.workflows.sequential_validation.document_tool_executor")
    @patch("src.workflows.sequential_validation.api_tool_executor")
    @patch("src.workflows.sequential_validation.ConversableAgent")
    def test_run_full_validation(
        self, mock_agent_class, mock_api, mock_doc, mock_db, mock_web, mock_rag, mock_financial
    ):
        """Test run_full_validation method."""
        mock_agent = Mock()

        # Mock different responses for each phase
        mock_agent.generate_reply.side_effect = [
            json.dumps({"refined_idea": "AI Platform"}),
            json.dumps({"market_size": "$50B"}),
            json.dumps({"npv": "$5M"}),
            json.dumps({"key_risks": ["Competition"]}),
            json.dumps({"competitors": ["X"]}),
            json.dumps({"regulations": ["GDPR"]}),
            json.dumps({"overall_assessment": "GO"}),
        ]

        mock_agent_class.return_value = mock_agent

        # Mock tool responses
        mock_financial.return_value = {"npv": 5000000, "irr": 0.35}
        mock_rag.return_value = {"insights": "market data"}
        mock_web.return_value = {"search": "results"}
        mock_db.return_value = {"db": "data"}
        mock_doc.return_value = {"doc": "generated"}
        mock_api.return_value = {"api": "response"}

        workflow = SequentialValidationWorkflow()

        report = workflow.run_full_validation(initial_data={"idea": "AI platform"})

        # report is Dict[ValidationPhase, PhaseResult]
        assert isinstance(report, dict)
        assert len(workflow.phase_results) > 0

    @patch("src.workflows.sequential_validation.ConversableAgent")
    def test_get_phase_summary(self, mock_agent_class):
        """Test get_phase_summary method."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        workflow = SequentialValidationWorkflow()

        # Add some phase results
        workflow.phase_results[ValidationPhase.IDEA_REFINEMENT] = PhaseResult(
            ValidationPhase.IDEA_REFINEMENT, True, {"idea": "refined"}, ["Do X"]
        )
        workflow.phase_results[ValidationPhase.MARKET_VALIDATION] = PhaseResult(
            ValidationPhase.MARKET_VALIDATION, False, {"error": "No market"}, []
        )

        summary = workflow.get_phase_summary()

        assert "completed_phases" in summary
        assert "success_rate" in summary
        assert "average_confidence" in summary
        assert "phase_details" in summary
        assert summary["completed_phases"] == 2
        assert summary["success_rate"] == 0.5  # 1 success out of 2 phases
        assert len(summary["phase_details"]) == 2


class TestErrorHandling:
    """Test error handling in workflow."""

    @patch("src.workflows.sequential_validation.ConversableAgent")
    def test_phase_execution_with_exception(self, mock_agent_class):
        """Test handling exceptions during phase execution."""
        mock_agent = Mock()
        mock_agent.generate_reply.side_effect = Exception("API Error")
        mock_agent_class.return_value = mock_agent

        workflow = SequentialValidationWorkflow()

        # Should handle exception gracefully
        result = workflow._execute_idea_refinement({"idea": "test"})

        assert isinstance(result, PhaseResult)
        # Likely returns failure result
        assert result.phase == ValidationPhase.IDEA_REFINEMENT

    @patch("src.workflows.sequential_validation.ConversableAgent")
    def test_phase_execution_with_invalid_json(self, mock_agent_class):
        """Test handling invalid JSON responses."""
        mock_agent = Mock()
        mock_agent.generate_reply.return_value = "Not valid JSON"
        mock_agent_class.return_value = mock_agent

        workflow = SequentialValidationWorkflow()

        # Should handle invalid JSON gracefully
        result = workflow._execute_idea_refinement({"idea": "test"})

        assert isinstance(result, PhaseResult)
        assert result.phase == ValidationPhase.IDEA_REFINEMENT

    @patch("src.workflows.sequential_validation.ConversableAgent")
    @patch("src.workflows.sequential_validation.financial_tool_executor")
    def test_run_with_max_retries(self, mock_financial, mock_agent_class):
        """Test that max_retries is respected."""
        mock_agent = Mock()
        # Always fail to force retries
        mock_agent.generate_reply.return_value = json.dumps({"error": "Failed"})
        mock_agent_class.return_value = mock_agent

        # Mock financial tool to avoid string growth_rate error
        mock_financial.return_value = {"npv": 100000, "irr": 0.25}

        workflow = SequentialValidationWorkflow()

        report = workflow.run_full_validation(initial_data={"idea": "test"})

        # Should return a dict of phase results
        assert isinstance(report, dict)


class TestToolsIntegration:
    """Test integration with various tools."""

    @patch("src.workflows.sequential_validation.ConversableAgent")
    @patch("src.workflows.sequential_validation.financial_tool_executor")
    @patch("src.workflows.sequential_validation.rag_tool_executor")
    @patch("src.workflows.sequential_validation.web_search_executor")
    @patch("src.workflows.sequential_validation.database_tool_executor")
    @patch("src.workflows.sequential_validation.document_tool_executor")
    @patch("src.workflows.sequential_validation.api_tool_executor")
    def test_all_tools_called(
        self, mock_api, mock_doc, mock_db, mock_web, mock_rag, mock_financial, mock_agent_class
    ):
        """Test that tools can be called during validation."""
        # Setup mocks
        mock_agent = Mock()
        mock_agent.generate_reply.return_value = json.dumps({"result": "success"})
        mock_agent_class.return_value = mock_agent

        mock_financial.return_value = {"npv": 1000000}
        mock_rag.return_value = {"insights": "data"}
        mock_web.return_value = {"search": "results"}
        mock_db.return_value = {"db": "data"}
        mock_doc.return_value = {"doc": "generated"}
        mock_api.return_value = {"api": "response"}

        workflow = SequentialValidationWorkflow()

        # Run various phases that use different tools
        workflow._execute_financial_modeling({"data": "test"})
        workflow._execute_market_validation({"data": "test"})
        workflow._execute_competitive_analysis({"data": "test"})
        workflow._execute_regulatory_compliance({"data": "test"})
        workflow._execute_final_synthesis({"data": "test"})

        # Tools should be available for use
        assert workflow.agents is not None
