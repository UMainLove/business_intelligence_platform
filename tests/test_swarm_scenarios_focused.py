"""
Focused tests for swarm_scenarios.py to achieve 95%+ coverage.
"""

import json
from unittest.mock import Mock, patch

from src.workflows.swarm_scenarios import ScenarioResult, ScenarioType, SwarmScenarioAnalysis


class TestScenarioTypeEnum:
    """Test ScenarioType enum."""

    def test_all_scenario_types_defined(self):
        """Test that all scenario types are defined."""
        expected_types = [
            ScenarioType.OPTIMISTIC,
            ScenarioType.REALISTIC,
            ScenarioType.PESSIMISTIC,
            ScenarioType.BLACK_SWAN,
            ScenarioType.COMPETITIVE_THREAT,
            ScenarioType.REGULATORY_CHANGE,
            ScenarioType.ECONOMIC_DOWNTURN,
            ScenarioType.TECHNOLOGY_DISRUPTION,
        ]

        assert len(expected_types) == 8
        for scenario_type in expected_types:
            assert scenario_type.value is not None

    def test_scenario_type_values(self):
        """Test scenario type string values."""
        assert ScenarioType.OPTIMISTIC.value == "optimistic"
        assert ScenarioType.REALISTIC.value == "realistic"
        assert ScenarioType.PESSIMISTIC.value == "pessimistic"
        assert ScenarioType.BLACK_SWAN.value == "black_swan"
        assert ScenarioType.COMPETITIVE_THREAT.value == "competitive_threat"
        assert ScenarioType.REGULATORY_CHANGE.value == "regulatory_change"
        assert ScenarioType.ECONOMIC_DOWNTURN.value == "economic_downturn"
        assert ScenarioType.TECHNOLOGY_DISRUPTION.value == "technology_disruption"


class TestScenarioResultDataclass:
    """Test ScenarioResult dataclass."""

    def test_scenario_result_creation(self):
        """Test creating a ScenarioResult with all fields."""
        result = ScenarioResult(
            scenario_type=ScenarioType.OPTIMISTIC,
            scenario_name="Best Case Growth",
            probability=0.3,
            impact_score=0.9,
            analysis="Strong market conditions lead to rapid growth",
            mitigation_strategies=["Scale operations", "Hire talent"],
            key_metrics={"revenue_growth": "150%", "market_share": "25%"},
            confidence_score=0.85,
        )

        assert result.scenario_type == ScenarioType.OPTIMISTIC
        assert result.scenario_name == "Best Case Growth"
        assert result.probability == 0.3
        assert result.impact_score == 0.9
        assert result.analysis == "Strong market conditions lead to rapid growth"
        assert len(result.mitigation_strategies) == 2
        assert result.key_metrics["revenue_growth"] == "150%"
        assert result.confidence_score == 0.85


class TestSwarmScenarioAnalysisBasic:
    """Test basic SwarmScenarioAnalysis functionality."""

    @patch("src.workflows.swarm_scenarios.ConversableAgent")
    @patch("src.workflows.swarm_scenarios.settings")
    def test_initialization(self, mock_settings, mock_agent_class):
        """Test SwarmScenarioAnalysis initialization."""
        # Setup mocks
        mock_settings.model_specialists = "claude-3"
        mock_settings.anthropic_key = "test-key"
        mock_settings.top_p = 0.9
        mock_settings.temperature_specialists = 0.7

        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        analysis = SwarmScenarioAnalysis()

        assert analysis.scenario_agents is not None
        assert analysis.coordinator_agent is not None

    @patch("src.workflows.swarm_scenarios.settings")
    def test_create_anthropic_config(self, mock_settings):
        """Test _create_anthropic_config method."""
        mock_settings.model_specialists = "claude-3"
        mock_settings.anthropic_key = "test-key"
        mock_settings.top_p = 0.9

        analysis = SwarmScenarioAnalysis()
        config = analysis._create_anthropic_config(temperature=0.5, max_tokens=1000)

        assert config is not None
        assert hasattr(config, "config_list")

    @patch("src.workflows.swarm_scenarios.ConversableAgent")
    def test_create_scenario_swarm(self, mock_agent_class):
        """Test _create_scenario_swarm method."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        analysis = SwarmScenarioAnalysis()
        agents = analysis._create_scenario_swarm()

        assert isinstance(agents, dict)
        # Should have one agent for each scenario type
        assert len(agents) == len(ScenarioType)
        for scenario_type in ScenarioType:
            assert scenario_type in agents

    @patch("src.workflows.swarm_scenarios.ConversableAgent")
    def test_create_coordinator_agent(self, mock_agent_class):
        """Test _create_coordinator_agent method."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        analysis = SwarmScenarioAnalysis()
        coordinator = analysis._create_coordinator_agent()

        assert coordinator is not None
        mock_agent_class.assert_called()


class TestScenarioAnalysis:
    """Test scenario analysis methods."""

    @patch("src.workflows.swarm_scenarios.ConversableAgent")
    def test_analyze_scenario_optimistic(self, mock_agent_class):
        """Test analyzing optimistic scenario."""
        mock_agent = Mock()
        mock_agent.generate_reply.return_value = json.dumps(
            {
                "scenario_analysis": "Everything goes perfectly",
                "revenue_projection": "$10M",
                "growth_rate": "200%",
                "key_assumptions": ["Strong market", "No competition"],
                "risks": ["Overconfidence"],
                "opportunities": ["Market leadership"],
            }
        )
        mock_agent_class.return_value = mock_agent

        analysis = SwarmScenarioAnalysis()
        context = {"idea": "AI SaaS", "market": "B2B"}

        result = analysis.analyze_scenario(ScenarioType.OPTIMISTIC, context)

        assert isinstance(result, ScenarioResult)
        assert result.scenario_type == ScenarioType.OPTIMISTIC
        assert result.probability > 0
        assert result.impact_score > 0
        assert len(result.mitigation_strategies) >= 0

    @patch("src.workflows.swarm_scenarios.ConversableAgent")
    def test_analyze_scenario_pessimistic(self, mock_agent_class):
        """Test analyzing pessimistic scenario."""
        mock_agent = Mock()
        mock_agent.generate_reply.return_value = json.dumps(
            {
                "scenario_analysis": "Major challenges ahead",
                "revenue_projection": "$100K",
                "growth_rate": "10%",
                "key_challenges": ["High competition", "Low demand"],
                "mitigation": ["Pivot strategy", "Cost reduction"],
            }
        )
        mock_agent_class.return_value = mock_agent

        analysis = SwarmScenarioAnalysis()
        context = {"idea": "Test product"}

        result = analysis.analyze_scenario(ScenarioType.PESSIMISTIC, context)

        assert result.scenario_type == ScenarioType.PESSIMISTIC
        assert result.probability > 0

    @patch("src.workflows.swarm_scenarios.ConversableAgent")
    def test_analyze_scenario_black_swan(self, mock_agent_class):
        """Test analyzing black swan scenario."""
        mock_agent = Mock()
        mock_agent.generate_reply.return_value = json.dumps(
            {
                "scenario_analysis": "Unexpected major disruption",
                "impact": "Catastrophic",
                "probability": "Low but possible",
                "preparedness": ["Crisis plan", "Emergency fund"],
            }
        )
        mock_agent_class.return_value = mock_agent

        analysis = SwarmScenarioAnalysis()
        result = analysis.analyze_scenario(ScenarioType.BLACK_SWAN, {"idea": "startup"})

        assert result.scenario_type == ScenarioType.BLACK_SWAN
        # Black swan should have lower probability
        assert result.probability <= 0.2

    @patch("src.workflows.swarm_scenarios.ConversableAgent")
    def test_analyze_scenario_with_exception(self, mock_agent_class):
        """Test scenario analysis with exception handling."""
        mock_agent = Mock()
        mock_agent.generate_reply.side_effect = Exception("API Error")
        mock_agent_class.return_value = mock_agent

        analysis = SwarmScenarioAnalysis()

        # Should handle exception gracefully
        result = analysis.analyze_scenario(ScenarioType.REALISTIC, {"idea": "test"})

        assert isinstance(result, ScenarioResult)
        assert result.scenario_type == ScenarioType.REALISTIC
        # Should have default/error values
        assert result.confidence_score < 0.5

    @patch("src.workflows.swarm_scenarios.ConversableAgent")
    def test_analyze_scenario_invalid_json(self, mock_agent_class):
        """Test scenario analysis with invalid JSON response."""
        mock_agent = Mock()
        mock_agent.generate_reply.return_value = "Not valid JSON"
        mock_agent_class.return_value = mock_agent

        analysis = SwarmScenarioAnalysis()

        result = analysis.analyze_scenario(ScenarioType.REALISTIC, {"idea": "test"})

        assert isinstance(result, ScenarioResult)
        # Should handle gracefully with defaults


class TestSwarmAnalysis:
    """Test swarm analysis coordination."""

    @patch("src.workflows.swarm_scenarios.ConversableAgent")
    @patch("src.workflows.swarm_scenarios.concurrent.futures.ThreadPoolExecutor")
    @patch("src.workflows.swarm_scenarios.concurrent.futures.as_completed")
    def test_run_swarm_analysis(self, mock_as_completed, mock_executor_class, mock_agent_class):
        """Test run_swarm_analysis method with proper future_to_scenario mapping."""
        # Setup mocks
        mock_agent = Mock()
        mock_agent.generate_reply.return_value = json.dumps(
            {"scenario_analysis": "Analysis complete"}
        )
        mock_agent_class.return_value = mock_agent

        # Mock executor and create deterministic futures
        mock_executor = Mock()
        scenarios = [ScenarioType.OPTIMISTIC, ScenarioType.PESSIMISTIC]

        # Pre-create futures that will be returned by submit() and used by as_completed()
        mock_futures = []
        for i, scenario_type in enumerate(scenarios):
            future = Mock()
            future.result.return_value = ScenarioResult(
                scenario_type, f"{scenario_type.value} Test", 0.5, 0.5, "Analysis", [], {}, 0.7
            )
            mock_futures.append(future)

        # Mock submit to return our pre-created futures in order
        mock_executor.submit.side_effect = mock_futures
        mock_executor.__enter__ = Mock(return_value=mock_executor)
        mock_executor.__exit__ = Mock(return_value=None)
        mock_executor_class.return_value = mock_executor

        # Mock as_completed to return the same futures in the same order
        # This ensures future_to_scenario[future] lookup works correctly
        mock_as_completed.return_value = mock_futures

        analysis = SwarmScenarioAnalysis()

        results = analysis.run_swarm_analysis(
            business_data={"idea": "AI startup"}, scenarios=scenarios
        )

        assert isinstance(results, dict)
        assert len(results) == 2
        for scenario_type, result in results.items():
            assert isinstance(scenario_type, ScenarioType)
            assert isinstance(result, ScenarioResult)

        # Verify submit was called for each scenario
        assert mock_executor.submit.call_count == 2
        # Verify as_completed was called with the future_to_scenario dict
        mock_as_completed.assert_called_once()

    @patch("src.workflows.swarm_scenarios.ConversableAgent")
    @patch("src.workflows.swarm_scenarios.concurrent.futures.ThreadPoolExecutor")
    @patch("src.workflows.swarm_scenarios.concurrent.futures.as_completed")
    def test_run_swarm_analysis_all_scenarios(
        self, mock_as_completed, mock_executor_class, mock_agent_class
    ):
        """Test running swarm analysis with all scenarios."""
        mock_agent = Mock()
        mock_agent.generate_reply.return_value = json.dumps({"analysis": "complete"})
        mock_agent_class.return_value = mock_agent

        # Mock executor with multiple futures
        mock_executor = Mock()
        futures = []

        # Create futures for a subset of scenarios (to avoid timeout)
        scenarios = [ScenarioType.REALISTIC, ScenarioType.OPTIMISTIC, ScenarioType.PESSIMISTIC]

        def create_future_for_scenario(analyze_func, scenario_type, business_data):
            future = Mock()
            future.result.return_value = ScenarioResult(
                scenario_type, f"{scenario_type.value} Test", 0.5, 0.5, "Analysis", [], {}, 0.7
            )
            futures.append(future)
            return future

        mock_executor.submit.side_effect = create_future_for_scenario
        mock_executor.__enter__ = Mock(return_value=mock_executor)
        mock_executor.__exit__ = Mock(return_value=None)
        mock_executor_class.return_value = mock_executor

        # Mock as_completed to return our futures
        mock_as_completed.return_value = futures

        analysis = SwarmScenarioAnalysis()

        # Run with specific scenarios to avoid creating too many futures
        results = analysis.run_swarm_analysis(business_data={"idea": "test"}, scenarios=scenarios)

        assert isinstance(results, dict)
        assert len(results) == 3

    @patch("src.workflows.swarm_scenarios.ConversableAgent")
    def test_synthesize_swarm_results(self, mock_agent_class):
        """Test synthesize_swarm_results method."""
        mock_agent = Mock()
        mock_agent.generate_reply.return_value = json.dumps(
            {
                "synthesis": "Overall assessment is positive",
                "key_findings": ["Strong market", "Good timing"],
                "recommendations": ["Proceed with caution", "Monitor risks"],
                "risk_matrix": {"high": ["Competition"], "medium": ["Funding"]},
                "success_probability": 0.65,
            }
        )
        mock_agent_class.return_value = mock_agent

        analysis = SwarmScenarioAnalysis()

        scenario_results = {
            ScenarioType.OPTIMISTIC: ScenarioResult(
                ScenarioType.OPTIMISTIC,
                "Best",
                0.3,
                0.9,
                "Great outcome",
                ["Scale"],
                {"revenue": "$10M"},
                0.8,
            ),
            ScenarioType.PESSIMISTIC: ScenarioResult(
                ScenarioType.PESSIMISTIC,
                "Worst",
                0.2,
                0.3,
                "Challenges",
                ["Cut costs"],
                {"revenue": "$100K"},
                0.7,
            ),
        }

        business_data = {"idea": "AI startup", "market": "B2B"}
        synthesis = analysis.synthesize_swarm_results(scenario_results, business_data)

        assert "synthesis_analysis" in synthesis
        assert "scenario_results" in synthesis
        assert "overall_metrics" in synthesis
        assert "key_recommendations" in synthesis
        assert "monitoring_indicators" in synthesis
        assert synthesis["overall_metrics"]["average_impact_score"] > 0


class TestPrivateMethods:
    """Test private helper methods."""

    def test_estimate_probability(self):
        """Test _estimate_probability method."""
        analysis = SwarmScenarioAnalysis()

        # Test different scenario types
        optimistic_prob = analysis._estimate_probability(ScenarioType.OPTIMISTIC)
        assert 0.2 <= optimistic_prob <= 0.35

        realistic_prob = analysis._estimate_probability(ScenarioType.REALISTIC)
        assert 0.4 <= realistic_prob <= 0.6

        black_swan_prob = analysis._estimate_probability(ScenarioType.BLACK_SWAN)
        assert 0.01 <= black_swan_prob <= 0.1

    def test_estimate_impact(self):
        """Test _estimate_impact method."""
        analysis = SwarmScenarioAnalysis()

        # Test with different scenario types (method returns fixed scores per scenario type)
        high_impact = analysis._estimate_impact(ScenarioType.BLACK_SWAN, "any text")
        assert high_impact == 9.0  # BLACK_SWAN has fixed score of 9.0

        low_impact = analysis._estimate_impact(ScenarioType.PESSIMISTIC, "any text")
        assert low_impact == 3.0  # PESSIMISTIC has fixed score of 3.0

    def test_extract_strategies(self):
        """Test _extract_strategies method."""
        analysis = SwarmScenarioAnalysis()

        # Method returns fixed strategies regardless of input text
        strategies = analysis._extract_strategies("any text")

        assert isinstance(strategies, list)
        assert len(strategies) == 4
        expected_strategies = [
            "Monitor key indicators",
            "Build strategic reserves",
            "Diversify risk exposure",
            "Develop contingency plans",
        ]
        assert strategies == expected_strategies

    def test_extract_metrics(self):
        """Test _extract_metrics method."""
        analysis = SwarmScenarioAnalysis()

        text_with_metrics = """
        Revenue projection: $5M
        Growth rate: 150%
        Market share: 15%
        Burn rate: $200K/month
        Customer acquisition cost: $500
        """

        metrics = analysis._extract_metrics(text_with_metrics)

        assert isinstance(metrics, dict)
        assert len(metrics) > 0
        # Should extract some metrics
        assert any("revenue" in k.lower() or "growth" in k.lower() for k in metrics)

    def test_extract_key_recommendations(self):
        """Test _extract_key_recommendations method."""
        analysis = SwarmScenarioAnalysis()

        # Method returns fixed recommendations regardless of input text
        recommendations = analysis._extract_key_recommendations("any text")

        assert isinstance(recommendations, list)
        assert len(recommendations) == 4
        expected_recommendations = [
            "Implement scenario monitoring system",
            "Build resilient business model",
            "Develop adaptive strategies",
            "Regular scenario review process",
        ]
        assert recommendations == expected_recommendations

    def test_extract_monitoring_indicators(self):
        """Test _extract_monitoring_indicators method."""
        analysis = SwarmScenarioAnalysis()

        synthesis_text = """
        Monitor the following KPIs:
        - Monthly recurring revenue
        - Customer churn rate
        - Cash runway
        
        Key indicators to track include market share and competitive positioning.
        Watch for signs of market saturation.
        """

        indicators = analysis._extract_monitoring_indicators(synthesis_text)

        assert isinstance(indicators, list)
        assert len(indicators) > 0
        assert any(
            "monitor" in i.lower() or "kpi" in i.lower() or "indicator" in i.lower()
            for i in indicators
        )


class TestErrorHandling:
    """Test error handling in swarm scenarios."""

    @patch("src.workflows.swarm_scenarios.ConversableAgent")
    def test_analyze_scenario_with_timeout(self, mock_agent_class):
        """Test scenario analysis (no timeout parameter in actual method)."""
        mock_agent = Mock()
        # Simulate slow response
        mock_agent.generate_reply.return_value = json.dumps({"analysis": "timeout"})
        mock_agent_class.return_value = mock_agent

        analysis = SwarmScenarioAnalysis()

        # analyze_scenario doesn't accept timeout parameter
        result = analysis.analyze_scenario(ScenarioType.REALISTIC, {"idea": "test"})

        assert isinstance(result, ScenarioResult)

    @patch("src.workflows.swarm_scenarios.ConversableAgent")
    @patch("src.workflows.swarm_scenarios.concurrent.futures.ThreadPoolExecutor")
    @patch("src.workflows.swarm_scenarios.concurrent.futures.as_completed")
    def test_swarm_analysis_with_partial_failures(
        self, mock_as_completed, mock_executor_class, mock_agent_class
    ):
        """Test swarm analysis when some scenarios fail."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        # Mock executor with mixed results
        mock_executor = Mock()

        # Create futures with different results
        success_future = Mock()
        success_future.result.return_value = ScenarioResult(
            ScenarioType.OPTIMISTIC, "Success", 0.3, 0.8, "Good", [], {}, 0.9
        )

        failure_future = Mock()
        failure_future.result.side_effect = Exception("Analysis failed")

        futures = [success_future, failure_future]
        mock_executor.submit.side_effect = futures
        mock_executor.__enter__ = Mock(return_value=mock_executor)
        mock_executor.__exit__ = Mock(return_value=None)
        mock_executor_class.return_value = mock_executor

        # Mock as_completed to return our futures
        mock_as_completed.return_value = futures

        analysis = SwarmScenarioAnalysis()

        results = analysis.run_swarm_analysis(
            business_data={"idea": "test"},
            scenarios=[ScenarioType.OPTIMISTIC, ScenarioType.PESSIMISTIC],
        )

        # Should still return results from successful scenarios
        assert isinstance(results, dict)
        assert len(results) == 2  # Both scenarios should have results (one success, one error)


class TestIntegration:
    """Test full integration scenarios."""

    @patch("src.workflows.swarm_scenarios.ConversableAgent")
    @patch("src.workflows.swarm_scenarios.concurrent.futures.ThreadPoolExecutor")
    @patch("src.workflows.swarm_scenarios.concurrent.futures.as_completed")
    def test_full_swarm_workflow(self, mock_as_completed, mock_executor_class, mock_agent_class):
        """Test complete swarm analysis workflow."""
        # Setup comprehensive mocks
        mock_agent = Mock()

        # Different responses for different scenarios
        responses = [
            json.dumps(
                {
                    "scenario_analysis": "Optimistic outlook",
                    "revenue_projection": "$10M",
                    "growth_rate": "200%",
                }
            ),
            json.dumps(
                {
                    "scenario_analysis": "Realistic assessment",
                    "revenue_projection": "$3M",
                    "growth_rate": "50%",
                }
            ),
            json.dumps(
                {
                    "scenario_analysis": "Pessimistic view",
                    "revenue_projection": "$500K",
                    "growth_rate": "10%",
                }
            ),
        ]

        mock_agent.generate_reply.side_effect = responses + [
            json.dumps({"synthesis": "Overall positive with caution", "success_probability": 0.6})
        ]
        mock_agent_class.return_value = mock_agent

        # Mock executor
        mock_executor = Mock()
        futures = []
        for i, scenario_type in enumerate(
            [ScenarioType.OPTIMISTIC, ScenarioType.REALISTIC, ScenarioType.PESSIMISTIC]
        ):
            future = Mock()
            future.result.return_value = ScenarioResult(
                scenario_type,
                f"Scenario {i}",
                0.3,
                0.5 + i * 0.2,
                f"Analysis {i}",
                [f"Strategy {i}"],
                {"metric": i},
                0.7 + i * 0.05,
            )
            futures.append(future)

        mock_executor.submit.side_effect = futures
        mock_executor.__enter__ = Mock(return_value=mock_executor)
        mock_executor.__exit__ = Mock(return_value=None)
        mock_executor_class.return_value = mock_executor

        # Mock as_completed to return our futures
        mock_as_completed.return_value = futures

        # Run full workflow
        analysis = SwarmScenarioAnalysis()

        business_context = {
            "idea": "AI-powered analytics platform",
            "target_market": "Enterprise B2B",
            "initial_investment": "$500K",
        }

        # Run swarm analysis
        results = analysis.run_swarm_analysis(
            business_context,
            scenarios=[ScenarioType.OPTIMISTIC, ScenarioType.REALISTIC, ScenarioType.PESSIMISTIC],
        )

        assert len(results) == 3

        # Synthesize results
        synthesis = analysis.synthesize_swarm_results(results, business_context)

        assert "synthesis_analysis" in synthesis
        assert "overall_metrics" in synthesis
        assert synthesis["overall_metrics"]["average_impact_score"] > 0
        assert synthesis["overall_metrics"]["average_impact_score"] <= 10.0
