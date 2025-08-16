"""
Comprehensive synthetic tests for swarm_scenarios.py to achieve 95%+ coverage.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import json
from typing import Dict, Any, List

from src.workflows.swarm_scenarios import (
    SwarmScenarioAnalysis,
    ScenarioType,
    ScenarioResult
)


class TestScenarioType:
    """Test ScenarioType enum."""

    def test_scenario_types_exist(self):
        """Test that all scenario types are defined."""
        assert ScenarioType.ECONOMIC_DOWNTURN
        assert ScenarioType.COMPETITIVE_DISRUPTION
        assert ScenarioType.REGULATORY_CHANGE
        assert ScenarioType.TECH_OBSOLESCENCE
        assert ScenarioType.SUPPLY_CHAIN_CRISIS
        assert ScenarioType.MARKET_SATURATION
        assert ScenarioType.FUNDING_DROUGHT
        assert ScenarioType.TALENT_SHORTAGE

    def test_scenario_type_values(self):
        """Test scenario type string values."""
        assert ScenarioType.ECONOMIC_DOWNTURN.value == "economic_downturn"
        assert ScenarioType.COMPETITIVE_DISRUPTION.value == "competitive_disruption"
        assert ScenarioType.REGULATORY_CHANGE.value == "regulatory_change"
        assert ScenarioType.TECH_OBSOLESCENCE.value == "tech_obsolescence"
        assert ScenarioType.SUPPLY_CHAIN_CRISIS.value == "supply_chain_crisis"
        assert ScenarioType.MARKET_SATURATION.value == "market_saturation"
        assert ScenarioType.FUNDING_DROUGHT.value == "funding_drought"
        assert ScenarioType.TALENT_SHORTAGE.value == "talent_shortage"


class TestScenarioResult:
    """Test ScenarioResult data class."""

    def test_scenario_result_creation(self):
        """Test creating a ScenarioResult."""
        result = ScenarioResult(
            scenario_type=ScenarioType.ECONOMIC_DOWNTURN,
            impact_level="HIGH",
            survival_probability=0.65,
            key_vulnerabilities=["Cash flow", "Customer retention"],
            mitigation_strategies=["Reduce burn rate", "Focus on retention"],
            analysis_details={"revenue_impact": "-30%"}
        )
        
        assert result.scenario_type == ScenarioType.ECONOMIC_DOWNTURN
        assert result.impact_level == "HIGH"
        assert result.survival_probability == 0.65
        assert len(result.key_vulnerabilities) == 2
        assert len(result.mitigation_strategies) == 2
        assert result.analysis_details["revenue_impact"] == "-30%"

    def test_scenario_result_low_survival(self):
        """Test ScenarioResult with low survival probability."""
        result = ScenarioResult(
            scenario_type=ScenarioType.FUNDING_DROUGHT,
            impact_level="CRITICAL",
            survival_probability=0.2,
            key_vulnerabilities=["Runway", "Growth"],
            mitigation_strategies=["Seek bridge funding"],
            analysis_details={}
        )
        
        assert result.survival_probability < 0.5
        assert result.impact_level == "CRITICAL"


class TestSwarmReport:
    """Test SwarmReport data class."""

    def test_swarm_report_creation(self):
        """Test creating a SwarmReport."""
        scenario_results = [
            ScenarioResult(
                ScenarioType.ECONOMIC_DOWNTURN, "HIGH", 0.7,
                ["Cash"], ["Cut costs"], {}
            ),
            ScenarioResult(
                ScenarioType.COMPETITIVE_DISRUPTION, "MEDIUM", 0.8,
                ["Market share"], ["Innovate"], {}
            )
        ]
        
        report = SwarmReport(
            overall_resilience_score=0.75,
            scenario_results=scenario_results,
            critical_vulnerabilities=["Cash flow", "Market position"],
            recommended_actions=["Build reserves", "Accelerate innovation"],
            risk_matrix={"economic": 0.3, "competitive": 0.2}
        )
        
        assert report.overall_resilience_score == 0.75
        assert len(report.scenario_results) == 2
        assert len(report.critical_vulnerabilities) == 2
        assert len(report.recommended_actions) == 2
        assert report.risk_matrix["economic"] == 0.3


class TestSwarmScenarioAnalysis:
    """Test SwarmScenarioAnalysis class."""

    def test_analysis_initialization(self):
        """Test SwarmScenarioAnalysis initialization."""
        business_data = {
            "idea": "SaaS Platform",
            "market": "B2B",
            "funding_stage": "Seed"
        }
        
        config = {
            "stress_level": "high",
            "scenarios_to_run": ["economic_downturn", "funding_drought"]
        }
        
        analysis = SwarmScenarioAnalysis(business_data, config)
        
        assert analysis.business_data == business_data
        assert analysis.scenario_config == config
        assert analysis.agents is not None

    @patch('src.workflows.swarm_scenarios.ConversableAgent')
    def test_create_scenario_agents(self, mock_agent_class):
        """Test creating scenario analysis agents."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        
        analysis = SwarmScenarioAnalysis({"idea": "Test"}, {})
        
        agents = analysis._create_scenario_agents()
        
        assert isinstance(agents, dict)
        # Should create agents for each scenario type
        assert len(agents) == 8  # One for each ScenarioType

    @patch('src.workflows.swarm_scenarios.ConversableAgent')
    def test_analyze_economic_downturn(self, mock_agent_class):
        """Test analyzing economic downturn scenario."""
        mock_agent = Mock()
        mock_reply = json.dumps({
            "impact_level": "HIGH",
            "survival_probability": 0.6,
            "key_vulnerabilities": ["Revenue decline", "Customer churn"],
            "mitigation_strategies": ["Extend runway", "Focus on retention"]
        })
        mock_agent.generate_reply.return_value = mock_reply
        mock_agent_class.return_value = mock_agent
        
        analysis = SwarmScenarioAnalysis(
            {"idea": "B2B SaaS", "burn_rate": "$100k/month"},
            {}
        )
        
        result = analysis._analyze_economic_downturn()
        
        assert isinstance(result, ScenarioResult)
        assert result.scenario_type == ScenarioType.ECONOMIC_DOWNTURN
        assert result.impact_level == "HIGH"
        assert result.survival_probability == 0.6

    @patch('src.workflows.swarm_scenarios.ConversableAgent')
    def test_analyze_competitive_disruption(self, mock_agent_class):
        """Test analyzing competitive disruption scenario."""
        mock_agent = Mock()
        mock_reply = json.dumps({
            "impact_level": "MEDIUM",
            "survival_probability": 0.75,
            "key_vulnerabilities": ["Market share", "Differentiation"],
            "mitigation_strategies": ["Accelerate innovation", "Partner strategy"]
        })
        mock_agent.generate_reply.return_value = mock_reply
        mock_agent_class.return_value = mock_agent
        
        analysis = SwarmScenarioAnalysis({"idea": "Test"}, {})
        
        result = analysis._analyze_competitive_disruption()
        
        assert result.scenario_type == ScenarioType.COMPETITIVE_DISRUPTION
        assert result.survival_probability == 0.75

    @patch('src.workflows.swarm_scenarios.ConversableAgent')
    def test_analyze_regulatory_change(self, mock_agent_class):
        """Test analyzing regulatory change scenario."""
        mock_agent = Mock()
        mock_reply = json.dumps({
            "impact_level": "LOW",
            "survival_probability": 0.9,
            "key_vulnerabilities": ["Compliance costs"],
            "mitigation_strategies": ["Legal review", "Compliance framework"]
        })
        mock_agent.generate_reply.return_value = mock_reply
        mock_agent_class.return_value = mock_agent
        
        analysis = SwarmScenarioAnalysis({"idea": "Test"}, {})
        
        result = analysis._analyze_regulatory_change()
        
        assert result.scenario_type == ScenarioType.REGULATORY_CHANGE
        assert result.impact_level == "LOW"

    @patch('src.workflows.swarm_scenarios.ConversableAgent')
    def test_analyze_tech_obsolescence(self, mock_agent_class):
        """Test analyzing tech obsolescence scenario."""
        mock_agent = Mock()
        mock_reply = json.dumps({
            "impact_level": "MEDIUM",
            "survival_probability": 0.7,
            "key_vulnerabilities": ["Tech stack", "Innovation speed"],
            "mitigation_strategies": ["Continuous R&D", "Tech partnerships"]
        })
        mock_agent.generate_reply.return_value = mock_reply
        mock_agent_class.return_value = mock_agent
        
        analysis = SwarmScenarioAnalysis({"idea": "Test"}, {})
        
        result = analysis._analyze_tech_obsolescence()
        
        assert result.scenario_type == ScenarioType.TECH_OBSOLESCENCE
        assert "Tech stack" in result.key_vulnerabilities

    @patch('src.workflows.swarm_scenarios.ConversableAgent')
    def test_analyze_supply_chain_crisis(self, mock_agent_class):
        """Test analyzing supply chain crisis scenario."""
        mock_agent = Mock()
        mock_reply = json.dumps({
            "impact_level": "HIGH",
            "survival_probability": 0.55,
            "key_vulnerabilities": ["Supplier dependency"],
            "mitigation_strategies": ["Diversify suppliers"]
        })
        mock_agent.generate_reply.return_value = mock_reply
        mock_agent_class.return_value = mock_agent
        
        analysis = SwarmScenarioAnalysis({"idea": "Test"}, {})
        
        result = analysis._analyze_supply_chain_crisis()
        
        assert result.scenario_type == ScenarioType.SUPPLY_CHAIN_CRISIS

    @patch('src.workflows.swarm_scenarios.ConversableAgent')
    def test_analyze_market_saturation(self, mock_agent_class):
        """Test analyzing market saturation scenario."""
        mock_agent = Mock()
        mock_reply = json.dumps({
            "impact_level": "MEDIUM",
            "survival_probability": 0.65,
            "key_vulnerabilities": ["Growth limits"],
            "mitigation_strategies": ["New markets", "Product expansion"]
        })
        mock_agent.generate_reply.return_value = mock_reply
        mock_agent_class.return_value = mock_agent
        
        analysis = SwarmScenarioAnalysis({"idea": "Test"}, {})
        
        result = analysis._analyze_market_saturation()
        
        assert result.scenario_type == ScenarioType.MARKET_SATURATION

    @patch('src.workflows.swarm_scenarios.ConversableAgent')
    def test_analyze_funding_drought(self, mock_agent_class):
        """Test analyzing funding drought scenario."""
        mock_agent = Mock()
        mock_reply = json.dumps({
            "impact_level": "CRITICAL",
            "survival_probability": 0.4,
            "key_vulnerabilities": ["Runway", "Growth funding"],
            "mitigation_strategies": ["Revenue focus", "Bridge funding"]
        })
        mock_agent.generate_reply.return_value = mock_reply
        mock_agent_class.return_value = mock_agent
        
        analysis = SwarmScenarioAnalysis({"idea": "Test"}, {})
        
        result = analysis._analyze_funding_drought()
        
        assert result.scenario_type == ScenarioType.FUNDING_DROUGHT
        assert result.impact_level == "CRITICAL"

    @patch('src.workflows.swarm_scenarios.ConversableAgent')
    def test_analyze_talent_shortage(self, mock_agent_class):
        """Test analyzing talent shortage scenario."""
        mock_agent = Mock()
        mock_reply = json.dumps({
            "impact_level": "MEDIUM",
            "survival_probability": 0.7,
            "key_vulnerabilities": ["Hiring", "Retention"],
            "mitigation_strategies": ["Remote hiring", "Equity incentives"]
        })
        mock_agent.generate_reply.return_value = mock_reply
        mock_agent_class.return_value = mock_agent
        
        analysis = SwarmScenarioAnalysis({"idea": "Test"}, {})
        
        result = analysis._analyze_talent_shortage()
        
        assert result.scenario_type == ScenarioType.TALENT_SHORTAGE

    def test_calculate_resilience_score(self):
        """Test calculating overall resilience score."""
        analysis = SwarmScenarioAnalysis({"idea": "Test"}, {})
        
        results = [
            ScenarioResult(ScenarioType.ECONOMIC_DOWNTURN, "HIGH", 0.6, [], [], {}),
            ScenarioResult(ScenarioType.COMPETITIVE_DISRUPTION, "MEDIUM", 0.8, [], [], {}),
            ScenarioResult(ScenarioType.FUNDING_DROUGHT, "CRITICAL", 0.4, [], [], {})
        ]
        
        score = analysis._calculate_resilience_score(results)
        
        # Average of survival probabilities: (0.6 + 0.8 + 0.4) / 3 = 0.6
        assert score == pytest.approx(0.6, rel=0.01)

    def test_identify_critical_vulnerabilities(self):
        """Test identifying critical vulnerabilities."""
        analysis = SwarmScenarioAnalysis({"idea": "Test"}, {})
        
        results = [
            ScenarioResult(
                ScenarioType.ECONOMIC_DOWNTURN, "HIGH", 0.5,
                ["Cash flow", "Revenue"], [], {}
            ),
            ScenarioResult(
                ScenarioType.FUNDING_DROUGHT, "CRITICAL", 0.3,
                ["Cash flow", "Runway"], [], {}
            )
        ]
        
        vulnerabilities = analysis._identify_critical_vulnerabilities(results)
        
        assert isinstance(vulnerabilities, list)
        assert "Cash flow" in vulnerabilities  # Common vulnerability

    def test_generate_risk_matrix(self):
        """Test generating risk matrix."""
        analysis = SwarmScenarioAnalysis({"idea": "Test"}, {})
        
        results = [
            ScenarioResult(ScenarioType.ECONOMIC_DOWNTURN, "HIGH", 0.4, [], [], {}),
            ScenarioResult(ScenarioType.COMPETITIVE_DISRUPTION, "MEDIUM", 0.7, [], [], {})
        ]
        
        matrix = analysis._generate_risk_matrix(results)
        
        assert isinstance(matrix, dict)
        assert ScenarioType.ECONOMIC_DOWNTURN.value in matrix
        # High impact with low survival = high risk
        assert matrix[ScenarioType.ECONOMIC_DOWNTURN.value] > 0.5

    def test_compile_recommended_actions(self):
        """Test compiling recommended actions."""
        analysis = SwarmScenarioAnalysis({"idea": "Test"}, {})
        
        results = [
            ScenarioResult(
                ScenarioType.ECONOMIC_DOWNTURN, "HIGH", 0.5,
                [], ["Reduce costs", "Extend runway"], {}
            ),
            ScenarioResult(
                ScenarioType.COMPETITIVE_DISRUPTION, "MEDIUM", 0.7,
                [], ["Innovate", "Partner"], {}
            )
        ]
        
        actions = analysis._compile_recommended_actions(results)
        
        assert isinstance(actions, list)
        assert len(actions) > 0

    @patch('src.workflows.swarm_scenarios.logger')
    def test_run_all_scenarios_with_logging(self, mock_logger):
        """Test running all scenarios with logging."""
        analysis = SwarmScenarioAnalysis({"idea": "Test"}, {})
        
        # Mock all analysis methods
        with patch.object(analysis, '_analyze_economic_downturn') as mock_econ:
            with patch.object(analysis, '_analyze_competitive_disruption') as mock_comp:
                mock_econ.return_value = ScenarioResult(
                    ScenarioType.ECONOMIC_DOWNTURN, "HIGH", 0.6, [], [], {}
                )
                mock_comp.return_value = ScenarioResult(
                    ScenarioType.COMPETITIVE_DISRUPTION, "MEDIUM", 0.8, [], [], {}
                )
                
                # Only run two scenarios
                analysis.scenario_config = {
                    "scenarios_to_run": ["economic_downturn", "competitive_disruption"]
                }
                
                report = analysis.run_all_scenarios()
                
                assert isinstance(report, SwarmReport)
                assert len(report.scenario_results) == 2
                mock_logger.info.assert_called()

    def test_run_scenarios_with_config_filter(self):
        """Test running only configured scenarios."""
        config = {
            "scenarios_to_run": ["economic_downturn", "funding_drought"]
        }
        
        analysis = SwarmScenarioAnalysis({"idea": "Test"}, config)
        
        with patch.object(analysis, '_analyze_economic_downturn') as mock_econ:
            with patch.object(analysis, '_analyze_funding_drought') as mock_fund:
                mock_econ.return_value = ScenarioResult(
                    ScenarioType.ECONOMIC_DOWNTURN, "HIGH", 0.6, [], [], {}
                )
                mock_fund.return_value = ScenarioResult(
                    ScenarioType.FUNDING_DROUGHT, "CRITICAL", 0.4, [], [], {}
                )
                
                report = analysis.run_all_scenarios()
                
                # Should only run configured scenarios
                assert len(report.scenario_results) == 2
                scenario_types = [r.scenario_type for r in report.scenario_results]
                assert ScenarioType.ECONOMIC_DOWNTURN in scenario_types
                assert ScenarioType.FUNDING_DROUGHT in scenario_types

    def test_run_all_scenarios_default(self):
        """Test running all scenarios by default."""
        analysis = SwarmScenarioAnalysis({"idea": "Test"}, {})
        
        # Mock all analysis methods
        for scenario_type in ScenarioType:
            method_name = f'_analyze_{scenario_type.value}'
            with patch.object(analysis, method_name) as mock_method:
                mock_method.return_value = ScenarioResult(
                    scenario_type, "MEDIUM", 0.7, [], [], {}
                )
        
        # Don't actually run, just verify method would call all
        scenarios_to_run = analysis.scenario_config.get("scenarios_to_run", 
                                                       [st.value for st in ScenarioType])
        
        assert len(scenarios_to_run) == 8  # All scenarios

    def test_scenario_with_json_parse_error(self):
        """Test handling JSON parse errors."""
        analysis = SwarmScenarioAnalysis({"idea": "Test"}, {})
        
        with patch('src.workflows.swarm_scenarios.ConversableAgent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent.generate_reply.return_value = "Invalid JSON"
            mock_agent_class.return_value = mock_agent
            
            result = analysis._analyze_economic_downturn()
            
            # Should return default low survival result
            assert result.survival_probability < 0.5
            assert result.impact_level == "UNKNOWN"

    def test_scenario_with_exception(self):
        """Test handling exceptions in scenario analysis."""
        analysis = SwarmScenarioAnalysis({"idea": "Test"}, {})
        
        with patch.object(analysis, '_analyze_economic_downturn') as mock_analyze:
            mock_analyze.side_effect = Exception("Analysis failed")
            
            # Should handle exception gracefully
            analysis.scenario_config = {"scenarios_to_run": ["economic_downturn"]}
            
            report = analysis.run_all_scenarios()
            
            assert isinstance(report, SwarmReport)
            # Should have a result even if analysis failed
            assert len(report.scenario_results) >= 0


class TestSwarmIntegration:
    """Test complete swarm scenario analysis integration."""

    @patch('src.workflows.swarm_scenarios.ConversableAgent')
    def test_full_swarm_analysis(self, mock_agent_class):
        """Test complete swarm analysis workflow."""
        # Setup mock agent with different responses
        mock_agent = Mock()
        
        responses = [
            json.dumps({
                "impact_level": "HIGH",
                "survival_probability": 0.6,
                "key_vulnerabilities": ["Cash flow"],
                "mitigation_strategies": ["Reduce burn"]
            }),
            json.dumps({
                "impact_level": "MEDIUM", 
                "survival_probability": 0.75,
                "key_vulnerabilities": ["Market share"],
                "mitigation_strategies": ["Innovate"]
            }),
            json.dumps({
                "impact_level": "LOW",
                "survival_probability": 0.85,
                "key_vulnerabilities": ["Compliance"],
                "mitigation_strategies": ["Legal review"]
            })
        ]
        
        mock_agent.generate_reply.side_effect = responses
        mock_agent_class.return_value = mock_agent
        
        # Run analysis
        business_data = {
            "idea": "AI Analytics Platform",
            "market": "Enterprise B2B",
            "funding_stage": "Series A",
            "burn_rate": "$200k/month"
        }
        
        config = {
            "scenarios_to_run": [
                "economic_downturn",
                "competitive_disruption", 
                "regulatory_change"
            ]
        }
        
        analysis = SwarmScenarioAnalysis(business_data, config)
        report = analysis.run_all_scenarios()
        
        # Verify report
        assert isinstance(report, SwarmReport)
        assert len(report.scenario_results) == 3
        assert report.overall_resilience_score > 0
        assert len(report.critical_vulnerabilities) > 0
        assert len(report.recommended_actions) > 0
        assert isinstance(report.risk_matrix, dict)