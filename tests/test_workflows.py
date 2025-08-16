"""
Tests for workflow components.
"""

from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

import pytest

from src.workflows.sequential_validation import (
    SequentialValidationWorkflow,
    ValidationPhase,
    PhaseResult
)
from src.workflows.swarm_scenarios import (
    ScenarioType,
    SwarmScenarioAnalysis,
    ScenarioResult
)


class TestSequentialValidationWorkflow:
    """Test sequential validation workflow."""

    @patch("src.workflows.sequential_validation.ConversableAgent")
    def test_workflow_initialization(self, mock_agent):
        """Test workflow initialization."""
        mock_agent.return_value = Mock()

        workflow = SequentialValidationWorkflow()

        # Check actual attributes from implementation
        assert hasattr(workflow, "current_phase")
        assert hasattr(workflow, "phase_results")
        assert hasattr(workflow, "business_context")
        assert hasattr(workflow, "agents")
        
        assert workflow.current_phase == ValidationPhase.IDEA_REFINEMENT
        assert workflow.phase_results == {}
        assert workflow.business_context == {}

    @patch("src.workflows.sequential_validation.ConversableAgent")
    def test_run_validation_phase(self, mock_agent):
        """Test running a single validation phase using execute_phase."""
        mock_agent_instance = Mock()
        mock_agent.return_value = mock_agent_instance
        mock_agent_instance.generate_reply.return_value = "Analysis complete"

        workflow = SequentialValidationWorkflow()

        test_data = {"business_idea": "SaaS platform for project management"}
        phase_result = workflow.execute_phase(ValidationPhase.IDEA_REFINEMENT, test_data)

        assert isinstance(phase_result, PhaseResult)
        assert phase_result.phase == ValidationPhase.IDEA_REFINEMENT
        assert phase_result.success is True
        assert phase_result.next_phase == ValidationPhase.MARKET_VALIDATION

    @patch("src.workflows.sequential_validation.ConversableAgent")
    def test_run_complete_validation(self, mock_agent):
        """Test running complete validation workflow using run_full_validation."""
        mock_agent_instance = Mock()
        mock_agent.return_value = mock_agent_instance
        mock_agent_instance.generate_reply.return_value = "Phase analysis"

        # Mock all tool executors to avoid dependencies
        with patch('src.workflows.sequential_validation.rag_tool_executor', return_value={}), \
             patch('src.workflows.sequential_validation.web_search_executor', return_value={}), \
             patch('src.workflows.sequential_validation.financial_tool_executor', return_value={}), \
             patch('src.workflows.sequential_validation.database_tool_executor', return_value={}), \
             patch('src.workflows.sequential_validation.api_tool_executor', return_value={}), \
             patch('src.workflows.sequential_validation.document_tool_executor', return_value={}):

            workflow = SequentialValidationWorkflow()

            test_data = {"business_idea": "AI-powered fitness app", "industry": "Health"}
            results = workflow.run_full_validation(test_data)

            assert isinstance(results, dict)
            # Should have PhaseResult objects for phases executed
            for phase, result in results.items():
                assert isinstance(phase, ValidationPhase)
                assert isinstance(result, PhaseResult)

    def test_phase_configuration(self):
        """Test phase configuration structure using actual ValidationPhase enum."""
        # Test all phases exist in the enum
        expected_phases = [
            ValidationPhase.IDEA_REFINEMENT,
            ValidationPhase.MARKET_VALIDATION,
            ValidationPhase.FINANCIAL_MODELING,
            ValidationPhase.RISK_ASSESSMENT,
            ValidationPhase.COMPETITIVE_ANALYSIS,
            ValidationPhase.REGULATORY_COMPLIANCE,
            ValidationPhase.FINAL_SYNTHESIS
        ]
        
        for phase in expected_phases:
            assert phase.value  # Each phase has a string value
            assert isinstance(phase.value, str)
        
        # Check there are 7 phases
        assert len(list(ValidationPhase)) == 7


class TestSwarmScenarioAnalysis:
    """Test swarm scenario analysis."""

    def test_scenario_types(self):
        """Test scenario type enumeration using actual ScenarioType enum."""
        # Check actual scenario types from implementation
        expected_scenarios = [
            ScenarioType.OPTIMISTIC,
            ScenarioType.REALISTIC,
            ScenarioType.PESSIMISTIC,
            ScenarioType.BLACK_SWAN,
            ScenarioType.COMPETITIVE_THREAT,
            ScenarioType.REGULATORY_CHANGE,
            ScenarioType.ECONOMIC_DOWNTURN,
            ScenarioType.TECHNOLOGY_DISRUPTION
        ]

        for scenario in expected_scenarios:
            assert scenario.value  # Each scenario has a string value
            assert isinstance(scenario.value, str)
        
        # Check there are 8 scenario types
        assert len(list(ScenarioType)) == 8

    @patch("src.workflows.swarm_scenarios.ConversableAgent")
    def test_swarm_initialization(self, mock_agent):
        """Test swarm analysis initialization."""
        mock_agent.return_value = Mock()

        swarm = SwarmScenarioAnalysis()

        # Check actual attributes from implementation
        assert hasattr(swarm, "scenario_agents")
        assert hasattr(swarm, "coordinator_agent")
        
        # scenario_agents is a dict, not a list
        assert isinstance(swarm.scenario_agents, dict)
        assert len(swarm.scenario_agents) == 8  # One agent per scenario type
        
        # Check all scenario types have agents
        for scenario_type in ScenarioType:
            assert scenario_type in swarm.scenario_agents

    @patch("src.workflows.swarm_scenarios.ConversableAgent")
    def test_run_scenario_analysis(self, mock_agent):
        """Test running single scenario analysis using analyze_scenario."""
        mock_agent_instance = Mock()
        mock_agent.return_value = mock_agent_instance
        mock_agent_instance.generate_reply.return_value = "Scenario analysis complete"

        swarm = SwarmScenarioAnalysis()

        test_business = {"business_idea": "E-commerce marketplace", "industry": "Retail"}
        scenario_result = swarm.analyze_scenario(ScenarioType.ECONOMIC_DOWNTURN, test_business)

        assert isinstance(scenario_result, ScenarioResult)
        assert scenario_result.scenario_type == ScenarioType.ECONOMIC_DOWNTURN
        assert scenario_result.probability > 0
        assert scenario_result.impact_score > 0
        assert isinstance(scenario_result.mitigation_strategies, list)

    @patch("src.workflows.swarm_scenarios.ConversableAgent")
    def test_run_comprehensive_analysis(self, mock_agent):
        """Test running comprehensive swarm analysis using run_swarm_analysis."""
        mock_agent_instance = Mock()
        mock_agent.return_value = mock_agent_instance
        mock_agent_instance.generate_reply.return_value = "Analysis complete"

        swarm = SwarmScenarioAnalysis()

        test_business = {"business_idea": "FinTech startup", "industry": "Finance"}
        
        # Mock analyze_scenario to avoid threading complexity
        def mock_analyze(scenario_type, business_data):
            return ScenarioResult(
                scenario_type=scenario_type,
                scenario_name=f"{scenario_type.value} Analysis",
                probability=0.5,
                impact_score=5.0,
                analysis="Test analysis",
                mitigation_strategies=["Strategy 1"],
                key_metrics={},
                confidence_score=0.7
            )
        
        with patch.object(swarm, 'analyze_scenario', side_effect=mock_analyze):
            results = swarm.run_swarm_analysis(test_business)

            assert isinstance(results, dict)
            # Should have results for all scenarios by default
            assert len(results) == 8
            
            # Check all results are ScenarioResult objects
            for scenario_type, result in results.items():
                assert isinstance(scenario_type, ScenarioType)
                assert isinstance(result, ScenarioResult)

    def test_scenario_configuration(self):
        """Test scenario configuration structure."""
        swarm = SwarmScenarioAnalysis()

        # Each scenario type has an agent
        for scenario_type in ScenarioType:
            agent = swarm.scenario_agents[scenario_type]
            assert agent is not None
            assert hasattr(agent, 'name')
            assert hasattr(agent, 'system_message')

    @patch("src.workflows.swarm_scenarios.ConversableAgent")
    def test_risk_categorization(self, mock_agent):
        """Test risk categorization logic using synthesize_swarm_results."""
        mock_agent_instance = Mock()
        mock_agent.return_value = mock_agent_instance
        mock_agent_instance.generate_reply.return_value = "Synthesis complete"

        swarm = SwarmScenarioAnalysis()

        # Create mock scenario results with different risk levels
        mock_results = {
            ScenarioType.OPTIMISTIC: ScenarioResult(
                scenario_type=ScenarioType.OPTIMISTIC,
                scenario_name="Optimistic",
                probability=0.2,
                impact_score=8.5,
                analysis="High growth",
                mitigation_strategies=[],
                key_metrics={},
                confidence_score=0.8
            ),
            ScenarioType.BLACK_SWAN: ScenarioResult(
                scenario_type=ScenarioType.BLACK_SWAN,
                scenario_name="Black Swan",
                probability=0.05,
                impact_score=9.0,
                analysis="Low prob high impact",
                mitigation_strategies=[],
                key_metrics={},
                confidence_score=0.6
            )
        }

        synthesis = swarm.synthesize_swarm_results(mock_results, {"business_idea": "Test"})

        assert "synthesis_analysis" in synthesis
        assert "scenario_results" in synthesis
        assert "overall_metrics" in synthesis
        
        # Check metrics calculation
        metrics = synthesis["overall_metrics"]
        assert "average_impact_score" in metrics
        assert "risk_weighted_score" in metrics
        assert metrics["scenarios_analyzed"] == 2


class TestWorkflowIntegration:
    """Test workflow integration with other components."""

    @patch("src.workflows.sequential_validation.financial_tool_executor")
    @patch("src.workflows.sequential_validation.ConversableAgent")
    def test_sequential_workflow_tool_integration(self, mock_agent, mock_financial):
        """Test sequential workflow tool integration."""
        mock_agent.return_value = Mock(generate_reply=Mock(return_value="Analysis"))
        mock_financial.return_value = {"npv": 50000, "irr": 0.25}

        workflow = SequentialValidationWorkflow()

        # Test that financial modeling phase uses financial tools
        test_data = {
            "projected_revenue": 1000000,
            "growth_rate": 0.25,
            "cac": 100,
            "ltv": 1000
        }
        
        result = workflow.execute_phase(ValidationPhase.FINANCIAL_MODELING, test_data)
        
        # Financial tool should be called during financial modeling phase
        mock_financial.assert_called()
        assert result.phase == ValidationPhase.FINANCIAL_MODELING

    @patch("src.workflows.sequential_validation.database_tool_executor")
    @patch("src.workflows.sequential_validation.ConversableAgent")
    def test_swarm_workflow_database_integration(self, mock_agent, mock_database):
        """Test workflow database integration in risk assessment."""
        mock_agent.return_value = Mock(generate_reply=Mock(return_value="Analysis"))
        mock_database.return_value = {"historical_data": "Industry benchmarks"}

        workflow = SequentialValidationWorkflow()

        # Test that risk assessment phase uses database tools
        test_data = {"industry": "SaaS", "business_model": "Subscription"}
        
        result = workflow.execute_phase(ValidationPhase.RISK_ASSESSMENT, test_data)
        
        # Database tool should be called during risk assessment
        mock_database.assert_called()
        assert result.phase == ValidationPhase.RISK_ASSESSMENT


class TestWorkflowErrorHandling:
    """Test error handling in workflows."""

    @patch("src.workflows.sequential_validation.ConversableAgent")
    def test_sequential_workflow_error_recovery(self, mock_agent):
        """Test sequential workflow error recovery."""
        # Mock agent that fails on generate_reply
        mock_agent_instance = Mock()
        mock_agent.return_value = mock_agent_instance
        mock_agent_instance.generate_reply.side_effect = Exception("Agent error")

        workflow = SequentialValidationWorkflow()

        # Should handle errors gracefully
        result = workflow.execute_phase(ValidationPhase.IDEA_REFINEMENT, {"business_idea": "Test"})
        
        # Error should be captured in result
        assert result.success is False
        assert "error" in result.data

    @patch("src.workflows.swarm_scenarios.ConversableAgent")
    def test_swarm_workflow_partial_failure(self, mock_agent):
        """Test swarm workflow handling partial failures."""
        mock_agent_instance = Mock()
        mock_agent.return_value = mock_agent_instance
        mock_agent_instance.generate_reply.side_effect = Exception("Agent failed")

        swarm = SwarmScenarioAnalysis()

        # analyze_scenario should handle exceptions
        result = swarm.analyze_scenario(ScenarioType.OPTIMISTIC, {"business_idea": "Test"})
        
        # Should return error result, not raise exception
        assert result.scenario_type == ScenarioType.OPTIMISTIC
        assert result.probability == 0.0
        assert result.impact_score == 0.0
        assert "Error in scenario analysis" in result.analysis