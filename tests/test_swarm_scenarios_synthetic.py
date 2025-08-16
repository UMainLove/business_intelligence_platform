"""
Comprehensive synthetic tests for swarm_scenarios.py to achieve 95%+ coverage.
"""

from unittest.mock import Mock, patch

from src.workflows.swarm_scenarios import ScenarioResult, ScenarioType, SwarmScenarioAnalysis


class TestScenarioType:
    """Test ScenarioType enum."""

    def test_scenario_types_exist(self):
        """Test that all scenario types are defined."""
        assert ScenarioType.OPTIMISTIC
        assert ScenarioType.REALISTIC
        assert ScenarioType.PESSIMISTIC
        assert ScenarioType.BLACK_SWAN
        assert ScenarioType.COMPETITIVE_THREAT
        assert ScenarioType.REGULATORY_CHANGE
        assert ScenarioType.ECONOMIC_DOWNTURN
        assert ScenarioType.TECHNOLOGY_DISRUPTION

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

    def test_scenario_type_count(self):
        """Test that ScenarioType has expected number of values."""
        scenarios = list(ScenarioType)
        assert len(scenarios) == 8


class TestScenarioResult:
    """Test ScenarioResult dataclass."""

    def test_scenario_result_creation(self):
        """Test creating a ScenarioResult."""
        result = ScenarioResult(
            scenario_type=ScenarioType.ECONOMIC_DOWNTURN,
            scenario_name="Economic Downturn Analysis",
            probability=0.25,
            impact_score=4.5,
            analysis="Detailed economic analysis",
            mitigation_strategies=["Reduce costs", "Diversify revenue"],
            key_metrics={"revenue_impact": "-30%"},
            confidence_score=0.75,
        )

        assert result.scenario_type == ScenarioType.ECONOMIC_DOWNTURN
        assert result.scenario_name == "Economic Downturn Analysis"
        assert result.probability == 0.25
        assert result.impact_score == 4.5
        assert result.analysis == "Detailed economic analysis"
        assert len(result.mitigation_strategies) == 2
        assert result.key_metrics["revenue_impact"] == "-30%"
        assert result.confidence_score == 0.75

    def test_scenario_result_optimistic(self):
        """Test ScenarioResult for optimistic scenario."""
        result = ScenarioResult(
            scenario_type=ScenarioType.OPTIMISTIC,
            scenario_name="Best Case Scenario",
            probability=0.2,
            impact_score=8.5,
            analysis="High growth potential",
            mitigation_strategies=["Scale rapidly"],
            key_metrics={"growth_rate": "300%"},
            confidence_score=0.8,
        )

        assert result.scenario_type == ScenarioType.OPTIMISTIC
        assert result.impact_score == 8.5
        assert result.probability == 0.2

    def test_scenario_result_black_swan(self):
        """Test ScenarioResult for black swan scenario."""
        result = ScenarioResult(
            scenario_type=ScenarioType.BLACK_SWAN,
            scenario_name="Black Swan Event",
            probability=0.05,
            impact_score=9.0,
            analysis="Low probability, high impact event",
            mitigation_strategies=["Build resilience", "Emergency fund"],
            key_metrics={"disruption_level": "severe"},
            confidence_score=0.6,
        )

        assert result.scenario_type == ScenarioType.BLACK_SWAN
        assert result.probability == 0.05
        assert result.impact_score == 9.0


class TestSwarmScenarioAnalysis:
    """Test SwarmScenarioAnalysis class."""

    def test_analysis_initialization(self):
        """Test SwarmScenarioAnalysis initialization."""
        analysis = SwarmScenarioAnalysis()

        assert hasattr(analysis, "scenario_agents")
        assert hasattr(analysis, "coordinator_agent")
        assert isinstance(analysis.scenario_agents, dict)
        assert analysis.coordinator_agent is not None

    def test_scenario_agents_creation(self):
        """Test that all scenario agents are created."""
        analysis = SwarmScenarioAnalysis()

        # Check all scenario types have agents
        for scenario_type in ScenarioType:
            assert scenario_type in analysis.scenario_agents
            assert analysis.scenario_agents[scenario_type] is not None

    def test_agent_configurations(self):
        """Test agent configurations are correct."""
        analysis = SwarmScenarioAnalysis()

        # Test specific agent names
        assert analysis.scenario_agents[ScenarioType.OPTIMISTIC].name == "optimistic_analyst"
        assert analysis.scenario_agents[ScenarioType.PESSIMISTIC].name == "pessimistic_analyst"
        assert analysis.scenario_agents[ScenarioType.BLACK_SWAN].name == "black_swan_analyst"
        assert analysis.coordinator_agent.name == "swarm_coordinator"

    def test_create_anthropic_config(self):
        """Test anthropic config creation."""
        analysis = SwarmScenarioAnalysis()

        config = analysis._create_anthropic_config(0.5, 1000)

        # Verify config structure
        assert hasattr(config, "temperature")
        assert config.temperature == 0.5
        assert hasattr(config, "config_list")
        assert len(config.config_list) > 0
        assert config.config_list[0]["max_tokens"] == 1000

    def test_analyze_optimistic_scenario(self):
        """Test optimistic scenario analysis."""
        analysis = SwarmScenarioAnalysis()

        # Mock agent response
        with patch.object(
            analysis.scenario_agents[ScenarioType.OPTIMISTIC], "generate_reply"
        ) as mock_reply:
            mock_reply.return_value = (
                "Optimistic analysis: High growth potential with strong market adoption"
            )

            business_data = {
                "business_idea": "AI Platform",
                "industry": "Technology",
                "target_market": "B2B",
                "business_model": "SaaS",
            }

            result = analysis.analyze_scenario(ScenarioType.OPTIMISTIC, business_data)

            assert result.scenario_type == ScenarioType.OPTIMISTIC
            assert result.probability == 0.2  # Default for optimistic
            assert result.impact_score == 8.5  # Default for optimistic
            assert "Optimistic analysis" in result.analysis
            assert len(result.mitigation_strategies) > 0
            assert result.confidence_score == 0.7

    def test_analyze_pessimistic_scenario(self):
        """Test pessimistic scenario analysis."""
        analysis = SwarmScenarioAnalysis()

        # Mock agent response
        with patch.object(
            analysis.scenario_agents[ScenarioType.PESSIMISTIC], "generate_reply"
        ) as mock_reply:
            mock_reply.return_value = (
                "Pessimistic analysis: Significant challenges and risks identified"
            )

            business_data = {"business_idea": "Risky Venture", "industry": "Competitive Market"}

            result = analysis.analyze_scenario(ScenarioType.PESSIMISTIC, business_data)

            assert result.scenario_type == ScenarioType.PESSIMISTIC
            assert result.probability == 0.15  # Default for pessimistic
            assert result.impact_score == 3.0  # Default for pessimistic
            assert "Pessimistic analysis" in result.analysis

    def test_analyze_economic_downturn_scenario(self):
        """Test economic downturn scenario analysis."""
        analysis = SwarmScenarioAnalysis()

        # Mock agent response
        with patch.object(
            analysis.scenario_agents[ScenarioType.ECONOMIC_DOWNTURN], "generate_reply"
        ) as mock_reply:
            mock_reply.return_value = "Economic analysis: Recession would impact demand and funding"

            business_data = {"business_idea": "Consumer Service"}

            result = analysis.analyze_scenario(ScenarioType.ECONOMIC_DOWNTURN, business_data)

            assert result.scenario_type == ScenarioType.ECONOMIC_DOWNTURN
            assert result.probability == 0.25  # Default for economic downturn
            assert result.impact_score == 4.5  # Default for economic downturn

    def test_analyze_competitive_threat_scenario(self):
        """Test competitive threat scenario analysis."""
        analysis = SwarmScenarioAnalysis()

        # Mock agent response
        with patch.object(
            analysis.scenario_agents[ScenarioType.COMPETITIVE_THREAT], "generate_reply"
        ) as mock_reply:
            mock_reply.return_value = "Competitive analysis: Major threats from established players"

            business_data = {"business_idea": "Disruptive Tech"}

            result = analysis.analyze_scenario(ScenarioType.COMPETITIVE_THREAT, business_data)

            assert result.scenario_type == ScenarioType.COMPETITIVE_THREAT
            assert result.probability == 0.4  # Default for competitive threat

    def test_analyze_regulatory_change_scenario(self):
        """Test regulatory change scenario analysis."""
        analysis = SwarmScenarioAnalysis()

        # Mock agent response
        with patch.object(
            analysis.scenario_agents[ScenarioType.REGULATORY_CHANGE], "generate_reply"
        ) as mock_reply:
            mock_reply.return_value = "Regulatory analysis: New compliance requirements expected"

            business_data = {"business_idea": "FinTech Platform"}

            result = analysis.analyze_scenario(ScenarioType.REGULATORY_CHANGE, business_data)

            assert result.scenario_type == ScenarioType.REGULATORY_CHANGE
            assert result.probability == 0.3  # Default for regulatory change

    def test_analyze_technology_disruption_scenario(self):
        """Test technology disruption scenario analysis."""
        analysis = SwarmScenarioAnalysis()

        # Mock agent response
        with patch.object(
            analysis.scenario_agents[ScenarioType.TECHNOLOGY_DISRUPTION], "generate_reply"
        ) as mock_reply:
            mock_reply.return_value = "Technology analysis: AI advances may disrupt current model"

            business_data = {"business_idea": "Traditional Service"}

            result = analysis.analyze_scenario(ScenarioType.TECHNOLOGY_DISRUPTION, business_data)

            assert result.scenario_type == ScenarioType.TECHNOLOGY_DISRUPTION
            assert result.probability == 0.35  # Default for technology disruption

    def test_analyze_black_swan_scenario(self):
        """Test black swan scenario analysis."""
        analysis = SwarmScenarioAnalysis()

        # Mock agent response
        with patch.object(
            analysis.scenario_agents[ScenarioType.BLACK_SWAN], "generate_reply"
        ) as mock_reply:
            mock_reply.return_value = "Black swan analysis: Unpredictable events with major impact"

            business_data = {"business_idea": "Standard Business"}

            result = analysis.analyze_scenario(ScenarioType.BLACK_SWAN, business_data)

            assert result.scenario_type == ScenarioType.BLACK_SWAN
            assert result.probability == 0.05  # Default for black swan
            assert result.impact_score == 9.0  # Default for black swan

    def test_analyze_realistic_scenario(self):
        """Test realistic scenario analysis."""
        analysis = SwarmScenarioAnalysis()

        # Mock agent response
        with patch.object(
            analysis.scenario_agents[ScenarioType.REALISTIC], "generate_reply"
        ) as mock_reply:
            mock_reply.return_value = (
                "Realistic analysis: Balanced view of opportunities and challenges"
            )

            business_data = {"business_idea": "Typical Startup"}

            result = analysis.analyze_scenario(ScenarioType.REALISTIC, business_data)

            assert result.scenario_type == ScenarioType.REALISTIC
            assert result.probability == 0.6  # Default for realistic
            assert result.impact_score == 6.0  # Default for realistic

    def test_scenario_analysis_with_exception(self):
        """Test scenario analysis when agent raises exception."""
        analysis = SwarmScenarioAnalysis()

        # Mock agent to raise exception
        with patch.object(
            analysis.scenario_agents[ScenarioType.OPTIMISTIC], "generate_reply"
        ) as mock_reply:
            mock_reply.side_effect = Exception("Agent failed")

            result = analysis.analyze_scenario(ScenarioType.OPTIMISTIC, {})

            assert result.scenario_type == ScenarioType.OPTIMISTIC
            assert result.probability == 0.0
            assert result.impact_score == 0.0
            assert "Error in scenario analysis" in result.analysis
            assert result.confidence_score == 0.0

    def test_estimate_probability_method(self):
        """Test probability estimation for different scenario types."""
        analysis = SwarmScenarioAnalysis()

        # Test known probabilities
        assert analysis._estimate_probability(ScenarioType.OPTIMISTIC) == 0.2
        assert analysis._estimate_probability(ScenarioType.REALISTIC) == 0.6
        assert analysis._estimate_probability(ScenarioType.PESSIMISTIC) == 0.15
        assert analysis._estimate_probability(ScenarioType.BLACK_SWAN) == 0.05
        assert analysis._estimate_probability(ScenarioType.COMPETITIVE_THREAT) == 0.4
        assert analysis._estimate_probability(ScenarioType.REGULATORY_CHANGE) == 0.3
        assert analysis._estimate_probability(ScenarioType.ECONOMIC_DOWNTURN) == 0.25
        assert analysis._estimate_probability(ScenarioType.TECHNOLOGY_DISRUPTION) == 0.35

    def test_estimate_impact_method(self):
        """Test impact estimation for different scenario types."""
        analysis = SwarmScenarioAnalysis()

        # Test known impact scores
        assert analysis._estimate_impact(ScenarioType.OPTIMISTIC, "test") == 8.5
        assert analysis._estimate_impact(ScenarioType.REALISTIC, "test") == 6.0
        assert analysis._estimate_impact(ScenarioType.PESSIMISTIC, "test") == 3.0
        assert analysis._estimate_impact(ScenarioType.BLACK_SWAN, "test") == 9.0

    def test_extract_strategies_method(self):
        """Test strategy extraction method."""
        analysis = SwarmScenarioAnalysis()

        strategies = analysis._extract_strategies("Some analysis text")

        assert isinstance(strategies, list)
        assert len(strategies) == 4  # Default strategies
        assert "Monitor key indicators" in strategies
        assert "Build strategic reserves" in strategies

    def test_extract_metrics_method(self):
        """Test metrics extraction method."""
        analysis = SwarmScenarioAnalysis()

        metrics = analysis._extract_metrics("Some analysis text")

        assert isinstance(metrics, dict)
        assert "revenue_impact" in metrics
        assert "timeline_impact" in metrics
        assert "resource_requirements" in metrics

    def test_run_swarm_analysis_all_scenarios(self):
        """Test running swarm analysis with all scenarios."""
        analysis = SwarmScenarioAnalysis()

        # Mock analyze_scenario to avoid threading complexity
        def mock_analyze_scenario(scenario_type, business_data):
            return ScenarioResult(
                scenario_type=scenario_type,
                scenario_name=f"{scenario_type.value} Test",
                probability=analysis._estimate_probability(scenario_type),
                impact_score=analysis._estimate_impact(scenario_type, "test"),
                analysis=f"Analysis for {scenario_type.value}",
                mitigation_strategies=["Strategy 1"],
                key_metrics={},
                confidence_score=0.8,
            )

        with patch.object(analysis, "analyze_scenario", side_effect=mock_analyze_scenario):
            business_data = {"business_idea": "Test Business"}
            results = analysis.run_swarm_analysis(business_data)

            # Should analyze all scenario types
            assert len(results) == len(ScenarioType)
            assert all(scenario_type in results for scenario_type in ScenarioType)

            # Verify each result
            for scenario_type, result in results.items():
                assert result.scenario_type == scenario_type
                assert result.probability == analysis._estimate_probability(scenario_type)

    def test_run_swarm_analysis_specific_scenarios(self):
        """Test running swarm analysis with specific scenarios."""
        analysis = SwarmScenarioAnalysis()

        # Mock analyze_scenario to avoid threading complexity
        def mock_analyze_scenario(scenario_type, business_data):
            return ScenarioResult(
                scenario_type=scenario_type,
                scenario_name=f"{scenario_type.value} Test",
                probability=analysis._estimate_probability(scenario_type),
                impact_score=analysis._estimate_impact(scenario_type, "test"),
                analysis=f"Analysis for {scenario_type.value}",
                mitigation_strategies=["Strategy 1"],
                key_metrics={},
                confidence_score=0.8,
            )

        with patch.object(analysis, "analyze_scenario", side_effect=mock_analyze_scenario):
            specific_scenarios = [ScenarioType.OPTIMISTIC, ScenarioType.PESSIMISTIC]
            business_data = {"business_idea": "Test Business"}

            results = analysis.run_swarm_analysis(business_data, specific_scenarios)

            # Should only have results for specified scenarios
            assert len(results) == 2
            assert ScenarioType.OPTIMISTIC in results
            assert ScenarioType.PESSIMISTIC in results

    def test_run_swarm_analysis_with_exception(self):
        """Test swarm analysis when a scenario raises an exception."""
        analysis = SwarmScenarioAnalysis()

        # Mock analyze_scenario to raise exception
        def mock_analyze_scenario(scenario_type, business_data):
            if scenario_type == ScenarioType.OPTIMISTIC:
                raise Exception("Scenario failed")
            return ScenarioResult(
                scenario_type=scenario_type,
                scenario_name="Test",
                probability=0.5,
                impact_score=7.0,
                analysis="Success",
                mitigation_strategies=[],
                key_metrics={},
                confidence_score=0.8,
            )

        with patch.object(analysis, "analyze_scenario", side_effect=mock_analyze_scenario):
            results = analysis.run_swarm_analysis({}, [ScenarioType.OPTIMISTIC])

            # Should have error result
            assert len(results) == 1
            assert ScenarioType.OPTIMISTIC in results
            result = results[ScenarioType.OPTIMISTIC]
            assert result.probability == 0.0
            assert result.impact_score == 0.0
            assert "Scenario analysis failed" in result.analysis

    def test_synthesize_swarm_results(self):
        """Test synthesis of swarm results."""
        analysis = SwarmScenarioAnalysis()

        # Create mock scenario results
        scenario_results = {
            ScenarioType.OPTIMISTIC: ScenarioResult(
                scenario_type=ScenarioType.OPTIMISTIC,
                scenario_name="Optimistic",
                probability=0.2,
                impact_score=8.5,
                analysis="Positive outlook" * 50,  # Make it longer than 500 chars
                mitigation_strategies=["Scale fast", "Capture market", "Build moat"],
                key_metrics={},
                confidence_score=0.8,
            ),
            ScenarioType.PESSIMISTIC: ScenarioResult(
                scenario_type=ScenarioType.PESSIMISTIC,
                scenario_name="Pessimistic",
                probability=0.15,
                impact_score=3.0,
                analysis="Challenging conditions",
                mitigation_strategies=["Cut costs", "Pivot"],
                key_metrics={},
                confidence_score=0.6,
            ),
        }

        # Mock coordinator agent
        with patch.object(analysis.coordinator_agent, "generate_reply") as mock_reply:
            mock_reply.return_value = "Comprehensive synthesis of scenario analysis"

            business_data = {"business_idea": "Test Business"}

            synthesis = analysis.synthesize_swarm_results(scenario_results, business_data)

            # Verify synthesis structure
            assert "synthesis_analysis" in synthesis
            assert "scenario_results" in synthesis
            assert "overall_metrics" in synthesis
            assert "key_recommendations" in synthesis
            assert "monitoring_indicators" in synthesis

            # Check overall metrics
            metrics = synthesis["overall_metrics"]
            assert "average_impact_score" in metrics
            assert "risk_weighted_score" in metrics
            assert "scenarios_analyzed" in metrics
            assert metrics["scenarios_analyzed"] == 2

            # Verify coordinator was called
            mock_reply.assert_called_once()

    def test_synthesize_swarm_results_with_exception(self):
        """Test synthesis when coordinator agent fails."""
        analysis = SwarmScenarioAnalysis()

        scenario_results = {
            ScenarioType.OPTIMISTIC: ScenarioResult(
                scenario_type=ScenarioType.OPTIMISTIC,
                scenario_name="Test",
                probability=0.5,
                impact_score=7.0,
                analysis="Test",
                mitigation_strategies=[],
                key_metrics={},
                confidence_score=0.7,
            )
        }

        # Mock coordinator agent to raise exception
        with patch.object(analysis.coordinator_agent, "generate_reply") as mock_reply:
            mock_reply.side_effect = Exception("Coordinator failed")

            synthesis = analysis.synthesize_swarm_results(scenario_results, {})

            # Should handle error gracefully
            assert "Error in synthesis" in synthesis["synthesis_analysis"]
            assert synthesis["scenario_results"] == scenario_results
            assert synthesis["overall_metrics"] == {}

    def test_extract_key_recommendations(self):
        """Test extraction of key recommendations."""
        analysis = SwarmScenarioAnalysis()

        recommendations = analysis._extract_key_recommendations("Some synthesis text")

        assert isinstance(recommendations, list)
        assert len(recommendations) == 4  # Default recommendations
        assert "Implement scenario monitoring system" in recommendations

    def test_extract_monitoring_indicators(self):
        """Test extraction of monitoring indicators."""
        analysis = SwarmScenarioAnalysis()

        indicators = analysis._extract_monitoring_indicators("Some synthesis text")

        assert isinstance(indicators, list)
        assert len(indicators) == 5  # Default indicators
        assert "Market share changes" in indicators
        assert "Economic indicators" in indicators


class TestSwarmIntegration:
    """Test integration scenarios."""

    def test_full_swarm_analysis_integration(self):
        """Test complete swarm analysis workflow."""
        analysis = SwarmScenarioAnalysis()

        # Mock all scenario agents
        for scenario_type, agent in analysis.scenario_agents.items():
            agent.generate_reply = Mock(return_value=f"Analysis for {scenario_type.value}")

        # Mock coordinator agent
        analysis.coordinator_agent.generate_reply = Mock(return_value="Comprehensive synthesis")

        business_data = {
            "business_idea": "AI-powered analytics platform",
            "industry": "Technology",
            "target_market": "Enterprise",
            "business_model": "SaaS",
            "market_size": "$50B",
            "growth_rate": "25%",
        }

        # Mock analyze_scenario to avoid threading complexity
        def mock_analyze_scenario(scenario_type, business_data):
            return ScenarioResult(
                scenario_type=scenario_type,
                scenario_name=f"{scenario_type.value} Analysis",
                probability=analysis._estimate_probability(scenario_type),
                impact_score=analysis._estimate_impact(scenario_type, "test"),
                analysis=f"Analysis for {scenario_type.value}",
                mitigation_strategies=["Strategy 1", "Strategy 2"],
                key_metrics={"test": "value"},
                confidence_score=0.7,
            )

        with patch.object(analysis, "analyze_scenario", side_effect=mock_analyze_scenario):
            scenario_results = analysis.run_swarm_analysis(business_data)

            # Verify all scenarios were analyzed
            assert len(scenario_results) == len(ScenarioType)

            # Run synthesis
            synthesis = analysis.synthesize_swarm_results(scenario_results, business_data)

            # Verify complete workflow
            assert "synthesis_analysis" in synthesis
            assert synthesis["overall_metrics"]["scenarios_analyzed"] == len(ScenarioType)

            # Note: agents are not called directly when we mock analyze_scenario
            # The important thing is that all scenarios were analyzed
            assert all(result.scenario_type in ScenarioType for result in scenario_results.values())

            # Verify coordinator was called for synthesis
            analysis.coordinator_agent.generate_reply.assert_called_once()

    def test_scenario_prompt_generation(self):
        """Test that scenario-specific prompts are generated correctly."""
        analysis = SwarmScenarioAnalysis()

        business_data = {
            "business_idea": "Test Business",
            "industry": "Tech",
            "target_market": "B2B",
        }

        # Mock an agent to capture the prompt
        captured_prompt = None

        def capture_prompt(messages):
            nonlocal captured_prompt
            captured_prompt = messages[0]["content"]
            return "Mock response"

        with patch.object(
            analysis.scenario_agents[ScenarioType.OPTIMISTIC],
            "generate_reply",
            side_effect=capture_prompt,
        ):
            analysis.analyze_scenario(ScenarioType.OPTIMISTIC, business_data)

            # Verify prompt contains business data
            assert "Test Business" in captured_prompt
            assert "Tech" in captured_prompt
            assert "B2B" in captured_prompt
            assert "optimistic conditions" in captured_prompt
            assert "best-case outcomes" in captured_prompt

    def test_probability_and_impact_consistency(self):
        """Test that probability and impact estimates are consistent."""
        analysis = SwarmScenarioAnalysis()

        # Test that optimistic scenario has higher impact than pessimistic
        opt_impact = analysis._estimate_impact(ScenarioType.OPTIMISTIC, "test")
        pess_impact = analysis._estimate_impact(ScenarioType.PESSIMISTIC, "test")
        assert opt_impact > pess_impact

        # Test that black swan has low probability but high impact
        black_swan_prob = analysis._estimate_probability(ScenarioType.BLACK_SWAN)
        black_swan_impact = analysis._estimate_impact(ScenarioType.BLACK_SWAN, "test")
        assert black_swan_prob < 0.1  # Very low probability
        assert black_swan_impact > 8.0  # Very high impact

        # Test that realistic scenario has highest probability
        realistic_prob = analysis._estimate_probability(ScenarioType.REALISTIC)
        assert realistic_prob > 0.5
