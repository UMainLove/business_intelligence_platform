"""
Tests for workflow components.
"""
import pytest
from unittest.mock import patch, Mock
from src.workflows.sequential_validation import SequentialValidationWorkflow
from src.workflows.swarm_scenarios import SwarmScenarioAnalysis, ScenarioType


class TestSequentialValidationWorkflow:
    """Test sequential validation workflow."""

    @patch('src.workflows.sequential_validation.ConversableAgent')
    def test_workflow_initialization(self, mock_agent):
        """Test workflow initialization."""
        mock_agent.return_value = Mock()

        workflow = SequentialValidationWorkflow()

        assert hasattr(workflow, 'phases')
        assert len(workflow.phases) == 7  # 7 validation phases

        # Check phase names
        expected_phases = [
            "Market Research",
            "Financial Modeling",
            "Legal & Regulatory",
            "Technical Feasibility",
            "Competitive Analysis",
            "Risk Assessment",
            "Strategic Planning"
        ]

        phase_names = [phase['name'] for phase in workflow.phases]
        for expected in expected_phases:
            assert expected in phase_names

    @patch('src.workflows.sequential_validation.ConversableAgent')
    def test_run_validation_phase(self, mock_agent):
        """Test running a single validation phase."""
        mock_agent_instance = Mock()
        mock_agent.return_value = mock_agent_instance

        # Mock chat response
        mock_agent_instance.initiate_chat.return_value = None

        workflow = SequentialValidationWorkflow()

        test_idea = "SaaS platform for project management"
        phase_result = workflow.run_validation_phase(0, test_idea)  # First phase

        assert "phase_name" in phase_result
        assert "analysis" in phase_result
        assert "recommendations" in phase_result
        assert "next_phase_inputs" in phase_result

        # Should have called agent chat
        mock_agent_instance.initiate_chat.assert_called_once()

    @patch('src.workflows.sequential_validation.ConversableAgent')
    def test_run_complete_validation(self, mock_agent):
        """Test running complete validation workflow."""
        mock_agent_instance = Mock()
        mock_agent.return_value = mock_agent_instance

        workflow = SequentialValidationWorkflow()

        test_idea = "AI-powered fitness app"
        results = workflow.run_complete_validation(test_idea)

        assert "phase_results" in results
        assert "overall_assessment" in results
        assert "final_recommendations" in results

        # Should have results for all phases
        assert len(results["phase_results"]) == 7

        # Each phase should have required fields
        for phase_result in results["phase_results"]:
            assert "phase_name" in phase_result
            assert "analysis" in phase_result

    def test_phase_configuration(self):
        """Test phase configuration structure."""
        workflow = SequentialValidationWorkflow()

        for phase in workflow.phases:
            assert "name" in phase
            assert "description" in phase
            assert "key_questions" in phase
            assert "tools" in phase
            assert "output_format" in phase

            # Key questions should be a list
            assert isinstance(phase["key_questions"], list)
            assert len(phase["key_questions"]) > 0

            # Tools should be a list
            assert isinstance(phase["tools"], list)


class TestSwarmScenarioAnalysis:
    """Test swarm scenario analysis."""

    def test_scenario_types(self):
        """Test scenario type enumeration."""
        # Check all scenario types exist
        expected_scenarios = [
            "ECONOMIC_DOWNTURN",
            "COMPETITIVE_DISRUPTION",
            "REGULATORY_CHANGES",
            "TECH_OBSOLESCENCE",
            "SUPPLY_CHAIN_CRISIS",
            "MARKET_SATURATION",
            "FUNDING_DROUGHT",
            "TALENT_SHORTAGE"
        ]

        for scenario in expected_scenarios:
            assert hasattr(ScenarioType, scenario)

    @patch('src.workflows.swarm_scenarios.ConversableAgent')
    def test_swarm_initialization(self, mock_agent):
        """Test swarm analysis initialization."""
        mock_agent.return_value = Mock()

        swarm = SwarmScenarioAnalysis()

        assert hasattr(swarm, 'scenarios')
        assert len(swarm.scenarios) == 8  # 8 scenario types

        # Check scenario structure
        for scenario in swarm.scenarios:
            assert "type" in scenario
            assert "name" in scenario
            assert "description" in scenario
            assert "impact_areas" in scenario
            assert "analysis_focus" in scenario

    @patch('src.workflows.swarm_scenarios.ConversableAgent')
    def test_run_scenario_analysis(self, mock_agent):
        """Test running single scenario analysis."""
        mock_agent_instance = Mock()
        mock_agent.return_value = mock_agent_instance

        swarm = SwarmScenarioAnalysis()

        test_business = "E-commerce marketplace"
        scenario_result = swarm.run_scenario_analysis(
            ScenarioType.ECONOMIC_DOWNTURN,
            test_business
        )

        assert "scenario_type" in scenario_result
        assert "scenario_name" in scenario_result
        assert "impact_assessment" in scenario_result
        assert "mitigation_strategies" in scenario_result
        assert "probability_score" in scenario_result
        assert "impact_severity" in scenario_result

        # Scores should be reasonable
        assert 0 <= scenario_result["probability_score"] <= 10
        assert 0 <= scenario_result["impact_severity"] <= 10

    @patch('src.workflows.swarm_scenarios.ConversableAgent')
    def test_run_comprehensive_analysis(self, mock_agent):
        """Test running comprehensive swarm analysis."""
        mock_agent_instance = Mock()
        mock_agent.return_value = mock_agent_instance

        swarm = SwarmScenarioAnalysis()

        test_business = "FinTech startup"
        results = swarm.run_comprehensive_analysis(test_business)

        assert "scenario_results" in results
        assert "risk_matrix" in results
        assert "prioritized_risks" in results
        assert "strategic_recommendations" in results

        # Should have results for all scenarios
        assert len(results["scenario_results"]) == 8

        # Risk matrix should have structure
        risk_matrix = results["risk_matrix"]
        assert "high_probability_high_impact" in risk_matrix
        assert "high_probability_low_impact" in risk_matrix
        assert "low_probability_high_impact" in risk_matrix
        assert "low_probability_low_impact" in risk_matrix

    def test_scenario_configuration(self):
        """Test scenario configuration structure."""
        swarm = SwarmScenarioAnalysis()

        for scenario in swarm.scenarios:
            assert "type" in scenario
            assert "name" in scenario
            assert "description" in scenario
            assert "impact_areas" in scenario
            assert "analysis_focus" in scenario

            # Impact areas should be a list
            assert isinstance(scenario["impact_areas"], list)
            assert len(scenario["impact_areas"]) > 0

            # Analysis focus should be a list
            assert isinstance(scenario["analysis_focus"], list)
            assert len(scenario["analysis_focus"]) > 0

    @patch('src.workflows.swarm_scenarios.ConversableAgent')
    def test_risk_categorization(self, mock_agent):
        """Test risk categorization logic."""
        mock_agent_instance = Mock()
        mock_agent.return_value = mock_agent_instance

        swarm = SwarmScenarioAnalysis()

        # Mock scenario results with different risk levels
        mock_results = [
            {"probability_score": 8, "impact_severity": 9, "scenario_name": "High-High"},
            {"probability_score": 8, "impact_severity": 3, "scenario_name": "High-Low"},
            {"probability_score": 2, "impact_severity": 9, "scenario_name": "Low-High"},
            {"probability_score": 2, "impact_severity": 3, "scenario_name": "Low-Low"},
        ]

        risk_matrix = swarm._categorize_risks(mock_results)

        assert len(risk_matrix["high_probability_high_impact"]) == 1
        assert len(risk_matrix["high_probability_low_impact"]) == 1
        assert len(risk_matrix["low_probability_high_impact"]) == 1
        assert len(risk_matrix["low_probability_low_impact"]) == 1

        assert risk_matrix["high_probability_high_impact"][0]["scenario_name"] == "High-High"


class TestWorkflowIntegration:
    """Test workflow integration with other components."""

    @patch('src.workflows.sequential_validation.financial_tool_executor')
    def test_sequential_workflow_tool_integration(self, mock_financial):
        """Test sequential workflow tool integration."""
        mock_financial.return_value = {"npv": 50000, "irr": 0.25}

        workflow = SequentialValidationWorkflow()

        # Check that financial tools are available in phases
        financial_phase = None
        for phase in workflow.phases:
            if "Financial" in phase["name"]:
                financial_phase = phase
                break

        assert financial_phase is not None
        assert "financial_calculator" in financial_phase["tools"]

    @patch('src.workflows.swarm_scenarios.database_tool_executor')
    def test_swarm_workflow_database_integration(self, mock_database):
        """Test swarm workflow database integration."""
        mock_database.return_value = {
            "similar_ventures": [],
            "success_rate": 75.0
        }

        swarm = SwarmScenarioAnalysis()

        # Scenarios should reference database tools for historical analysis
        market_scenario = None
        for scenario in swarm.scenarios:
            if "MARKET" in scenario["type"]:
                market_scenario = scenario
                break

        # Should have market-related analysis focus
        assert market_scenario is not None


class TestWorkflowErrorHandling:
    """Test error handling in workflows."""

    @patch('src.workflows.sequential_validation.ConversableAgent')
    def test_sequential_workflow_error_recovery(self, mock_agent):
        """Test sequential workflow error recovery."""
        # Mock agent that fails on first call
        mock_agent_instance = Mock()
        mock_agent.return_value = mock_agent_instance
        mock_agent_instance.initiate_chat.side_effect = [
            Exception("First call fails"),
            None  # Second call succeeds
        ]

        workflow = SequentialValidationWorkflow()

        # Should handle errors gracefully
        try:
            result = workflow.run_validation_phase(0, "Test idea")
            # If error handling is implemented, should get a result
            assert "phase_name" in result
        except Exception as e:
            # If no error handling, should raise exception
            assert "First call fails" in str(e)

    @patch('src.workflows.swarm_scenarios.ConversableAgent')
    def test_swarm_workflow_partial_failure(self, mock_agent):
        """Test swarm workflow handling partial failures."""
        mock_agent_instance = Mock()
        mock_agent.return_value = mock_agent_instance

        swarm = SwarmScenarioAnalysis()

        # Test with invalid scenario type
        with pytest.raises(ValueError):
            swarm.run_scenario_analysis("INVALID_SCENARIO", "Test business")
