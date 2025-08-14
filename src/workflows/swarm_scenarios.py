"""
Swarm intelligence for scenario analysis and stress testing business ideas.
"""

import concurrent.futures
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List

from autogen import ConversableAgent, LLMConfig

from ..config import settings


class ScenarioType(Enum):
    """Types of scenarios for analysis."""

    OPTIMISTIC = "optimistic"
    REALISTIC = "realistic"
    PESSIMISTIC = "pessimistic"
    BLACK_SWAN = "black_swan"
    COMPETITIVE_THREAT = "competitive_threat"
    REGULATORY_CHANGE = "regulatory_change"
    ECONOMIC_DOWNTURN = "economic_downturn"
    TECHNOLOGY_DISRUPTION = "technology_disruption"


@dataclass
class ScenarioResult:
    """Result from scenario analysis."""

    scenario_type: ScenarioType
    scenario_name: str
    probability: float
    impact_score: float
    analysis: str
    mitigation_strategies: List[str]
    key_metrics: Dict[str, Any]
    confidence_score: float


class SwarmScenarioAnalysis:
    """Swarm-based scenario analysis for comprehensive business stress testing."""

    def __init__(self):
        self.scenario_agents = self._create_scenario_swarm()
        self.coordinator_agent = self._create_coordinator_agent()

    def _create_anthropic_config(self, temperature: float, max_tokens: int = 1800) -> LLMConfig:
        """Create anthropic configuration for swarm agents."""
        return LLMConfig(
            api_type="anthropic",
            model=settings.model_specialists,
            api_key=settings.anthropic_key,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=settings.top_p,
        )

    def _create_scenario_swarm(self) -> Dict[ScenarioType, ConversableAgent]:
        """Create specialized agents for different scenario types."""
        agents = {}

        # Optimistic Scenario Agent
        agents[ScenarioType.OPTIMISTIC] = ConversableAgent(
            name="optimistic_analyst",
            system_message=(
                "You are an optimistic scenario analyst. Analyze business opportunities under best-case conditions. "
                "Consider factors like rapid market adoption, successful execution, favorable market conditions, "
                "strong competitive positioning, and access to resources. Provide realistic but positive projections."
            ),
            llm_config=self._create_anthropic_config(0.3),
            human_input_mode="NEVER",
        )

        # Realistic Scenario Agent
        agents[ScenarioType.REALISTIC] = ConversableAgent(
            name="realistic_analyst",
            system_message=(
                "You are a realistic scenario analyst. Analyze business opportunities under most likely conditions. "
                "Consider typical market dynamics, normal execution challenges, average competitive responses, "
                "and standard resource constraints. Base projections on industry benchmarks and historical data."
            ),
            llm_config=self._create_anthropic_config(0.2),
            human_input_mode="NEVER",
        )

        # Pessimistic Scenario Agent
        agents[ScenarioType.PESSIMISTIC] = ConversableAgent(
            name="pessimistic_analyst",
            system_message=(
                "You are a pessimistic scenario analyst. Analyze business challenges under difficult conditions. "
                "Consider slow market adoption, execution difficulties, strong competition, unfavorable market conditions, "
                "and resource constraints. Identify potential failure modes and their implications."
            ),
            llm_config=self._create_anthropic_config(0.2),
            human_input_mode="NEVER",
        )

        # Black Swan Events Agent
        agents[ScenarioType.BLACK_SWAN] = ConversableAgent(
            name="black_swan_analyst",
            system_message=(
                "You are a black swan events analyst. Analyze low-probability, high-impact events that could affect the business. "
                "Consider unpredictable disruptions like pandemics, natural disasters, geopolitical events, "
                "technological breakthroughs, or market crashes. Focus on preparedness and resilience strategies."
            ),
            llm_config=self._create_anthropic_config(0.4),
            human_input_mode="NEVER",
        )

        # Competitive Threat Agent
        agents[ScenarioType.COMPETITIVE_THREAT] = ConversableAgent(
            name="competitive_threat_analyst",
            system_message=(
                "You are a competitive threat analyst. Analyze potential competitive responses and market disruptions. "
                "Consider new entrants, existing competitors' reactions, price wars, technological disruption by competitors, "
                "and changes in competitive landscape. Develop defensive and offensive strategies."
            ),
            llm_config=self._create_anthropic_config(0.3),
            human_input_mode="NEVER",
        )

        # Regulatory Change Agent
        agents[ScenarioType.REGULATORY_CHANGE] = ConversableAgent(
            name="regulatory_analyst",
            system_message=(
                "You are a regulatory change analyst. Analyze potential regulatory and policy changes affecting the business. "
                "Consider new regulations, policy shifts, compliance requirements changes, tax implications, "
                "and international regulatory variations. Assess compliance costs and strategic implications."
            ),
            llm_config=self._create_anthropic_config(0.2),
            human_input_mode="NEVER",
        )

        # Economic Conditions Agent
        agents[ScenarioType.ECONOMIC_DOWNTURN] = ConversableAgent(
            name="economic_analyst",
            system_message=(
                "You are an economic conditions analyst. Analyze business performance under various economic scenarios. "
                "Consider recession, inflation, interest rate changes, unemployment, consumer spending patterns, "
                "and capital market conditions. Assess impact on revenue, costs, and funding availability."
            ),
            llm_config=self._create_anthropic_config(0.2),
            human_input_mode="NEVER",
        )

        # Technology Disruption Agent
        agents[ScenarioType.TECHNOLOGY_DISRUPTION] = ConversableAgent(
            name="technology_disruption_analyst",
            system_message=(
                "You are a technology disruption analyst. Analyze potential technological changes affecting the business. "
                "Consider AI/ML advancement, automation, new platforms, infrastructure changes, "
                "and emerging technologies. Assess opportunities and threats from technological evolution."
            ),
            llm_config=self._create_anthropic_config(0.4),
            human_input_mode="NEVER",
        )

        return agents

    def _create_coordinator_agent(self) -> ConversableAgent:
        """Create coordinator agent to synthesize swarm results."""
        return ConversableAgent(
            name="swarm_coordinator",
            system_message=(
                "You are a scenario analysis coordinator. Synthesize insights from multiple scenario analysts "
                "into a comprehensive risk and opportunity assessment. Identify patterns, prioritize scenarios "
                "by probability and impact, and develop integrated strategies that work across scenarios."
            ),
            llm_config=self._create_anthropic_config(0.15),
            human_input_mode="NEVER",
        )

    def analyze_scenario(
        self, scenario_type: ScenarioType, business_data: Dict[str, Any]
    ) -> ScenarioResult:
        """Analyze a specific scenario type."""
        agent = self.scenario_agents[scenario_type]

        # Prepare scenario-specific prompt
        base_prompt = f"""
        Business Context:
        - Business Idea: {business_data.get("business_idea", "")}
        - Industry: {business_data.get("industry", "")}
        - Target Market: {business_data.get("target_market", "")}
        - Business Model: {business_data.get("business_model", "")}
        - Initial Funding: {business_data.get("initial_funding", "TBD")}

        Market Data:
        - Market Size: {business_data.get("market_size", "TBD")}
        - Growth Rate: {business_data.get("growth_rate", "TBD")}
        - Competitive Landscape: {business_data.get("competitors", "TBD")}

        Please analyze this business under {scenario_type.value} conditions:
        """

        scenario_prompts = {
            ScenarioType.OPTIMISTIC: base_prompt
            + """
            1. What are the best-case outcomes for this business?
            2. What conditions would lead to rapid success?
            3. What revenue and growth projections are possible?
            4. What competitive advantages could be maximized?
            5. What expansion opportunities exist?
            """,
            ScenarioType.REALISTIC: base_prompt
            + """
            1. What are the most likely business outcomes?
            2. What typical challenges will this business face?
            3. What are realistic revenue and growth projections?
            4. How will competitors likely respond?
            5. What resources and timeline are realistically needed?
            """,
            ScenarioType.PESSIMISTIC: base_prompt
            + """
            1. What are the main risks and challenges?
            2. What could cause this business to fail?
            3. What are the worst-case financial projections?
            4. How could competitors threaten success?
            5. What mitigation strategies are needed?
            """,
            ScenarioType.BLACK_SWAN: base_prompt
            + """
            1. What unpredictable events could impact this business?
            2. How vulnerable is the business to external shocks?
            3. What would happen during a major market disruption?
            4. How could the business build resilience?
            5. What early warning indicators should be monitored?
            """,
            ScenarioType.COMPETITIVE_THREAT: base_prompt
            + """
            1. What competitive threats are most dangerous?
            2. How might established players respond to this business?
            3. What if a major competitor launches a similar offering?
            4. How could new technologies disrupt the market?
            5. What defensive strategies are needed?
            """,
            ScenarioType.REGULATORY_CHANGE: base_prompt
            + """
            1. What regulatory changes could impact this business?
            2. How might new compliance requirements affect operations?
            3. What if key regulations become more restrictive?
            4. How could international expansion be affected?
            5. What regulatory risks need monitoring?
            """,
            ScenarioType.ECONOMIC_DOWNTURN: base_prompt
            + """
            1. How would economic recession affect this business?
            2. What happens to demand during economic downturns?
            3. How would funding availability be impacted?
            4. What cost reduction strategies would be needed?
            5. How could the business remain viable during tough times?
            """,
            ScenarioType.TECHNOLOGY_DISRUPTION: base_prompt
            + """
            1. What technological changes could disrupt this business?
            2. How might AI/automation affect the market?
            3. What if new platforms or technologies emerge?
            4. How could the business stay technologically competitive?
            5. What technology investments are critical?
            """,
        }

        prompt = scenario_prompts[scenario_type]

        try:
            response = agent.generate_reply(messages=[{"role": "user", "content": prompt}])

            # Extract key metrics and insights (simplified - in production use NLP)
            probability = self._estimate_probability(scenario_type)
            impact_score = self._estimate_impact(scenario_type, response)

            return ScenarioResult(
                scenario_type=scenario_type,
                scenario_name=f"{scenario_type.value.title()} Scenario Analysis",
                probability=probability,
                impact_score=impact_score,
                analysis=response,
                mitigation_strategies=self._extract_strategies(response),
                key_metrics=self._extract_metrics(response),
                confidence_score=0.7,  # Based on agent confidence
            )

        except Exception as e:
            return ScenarioResult(
                scenario_type=scenario_type,
                scenario_name=f"{scenario_type.value.title()} Scenario Analysis",
                probability=0.0,
                impact_score=0.0,
                analysis=f"Error in scenario analysis: {str(e)}",
                mitigation_strategies=[],
                key_metrics={},
                confidence_score=0.0,
            )

    def run_swarm_analysis(
        self, business_data: Dict[str, Any], scenarios: List[ScenarioType] = None
    ) -> Dict[ScenarioType, ScenarioResult]:
        """Run parallel swarm analysis across multiple scenarios."""

        if scenarios is None:
            scenarios = list(ScenarioType)

        results = {}

        # Run scenarios in parallel using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all scenario analyses
            future_to_scenario = {
                executor.submit(self.analyze_scenario, scenario, business_data): scenario
                for scenario in scenarios
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_scenario):
                scenario = future_to_scenario[future]
                try:
                    result = future.result()
                    results[scenario] = result
                except Exception as e:
                    # Create error result
                    results[scenario] = ScenarioResult(
                        scenario_type=scenario,
                        scenario_name=f"{scenario.value.title()} Scenario Analysis",
                        probability=0.0,
                        impact_score=0.0,
                        analysis=f"Scenario analysis failed: {str(e)}",
                        mitigation_strategies=[],
                        key_metrics={},
                        confidence_score=0.0,
                    )

        return results

    def synthesize_swarm_results(
        self, scenario_results: Dict[ScenarioType, ScenarioResult], business_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize results from swarm analysis using coordinator agent."""

        # Prepare synthesis prompt
        scenarios_summary = ""
        for scenario_type, result in scenario_results.items():
            scenarios_summary += f"""
            {scenario_type.value.upper()} SCENARIO (Probability: {result.probability:.1%}, Impact: {result.impact_score}/10):
            {result.analysis[:500]}...

            Key Mitigation Strategies:
            {", ".join(result.mitigation_strategies[:3])}

            ---
            """

        synthesis_prompt = f"""
        Business: {business_data.get("business_idea", "Business Venture")}

        SCENARIO ANALYSIS RESULTS:
        {scenarios_summary}

        Please provide a comprehensive synthesis:

        1. RISK-OPPORTUNITY MATRIX:
           - Highest probability scenarios and their implications
           - Highest impact scenarios and preparedness needed
           - Key opportunity scenarios to maximize

        2. INTEGRATED STRATEGY:
           - Strategies that work across multiple scenarios
           - Resource allocation priorities
           - Decision framework for different conditions

        3. MONITORING & EARLY WARNING SYSTEM:
           - Key indicators to track
           - Decision triggers and thresholds
           - Adaptation mechanisms

        4. RESILIENCE RECOMMENDATIONS:
           - How to build business resilience
           - Diversification strategies
           - Contingency planning priorities

        5. OVERALL ASSESSMENT:
           - Business viability across scenarios
           - Risk-adjusted recommendations
           - Strategic priorities
        """

        try:
            synthesis = self.coordinator_agent.generate_reply(
                messages=[{"role": "user", "content": synthesis_prompt}]
            )

            # Calculate overall scores
            avg_impact = sum(r.impact_score for r in scenario_results.values()) / len(
                scenario_results
            )
            risk_weighted_score = sum(
                r.probability * r.impact_score for r in scenario_results.values()
            )

            return {
                "synthesis_analysis": synthesis,
                "scenario_results": scenario_results,
                "overall_metrics": {
                    "average_impact_score": avg_impact,
                    "risk_weighted_score": risk_weighted_score,
                    "scenarios_analyzed": len(scenario_results),
                    "high_probability_risks": len(
                        [r for r in scenario_results.values() if r.probability > 0.3]
                    ),
                    "high_impact_scenarios": len(
                        [r for r in scenario_results.values() if r.impact_score > 7]
                    ),
                },
                "key_recommendations": self._extract_key_recommendations(synthesis),
                "monitoring_indicators": self._extract_monitoring_indicators(synthesis),
            }

        except Exception as e:
            return {
                "synthesis_analysis": f"Error in synthesis: {str(e)}",
                "scenario_results": scenario_results,
                "overall_metrics": {},
                "key_recommendations": [],
                "monitoring_indicators": [],
            }

    def _estimate_probability(self, scenario_type: ScenarioType) -> float:
        """Estimate probability for scenario type (simplified heuristic)."""
        probabilities = {
            ScenarioType.OPTIMISTIC: 0.2,
            ScenarioType.REALISTIC: 0.6,
            ScenarioType.PESSIMISTIC: 0.15,
            ScenarioType.BLACK_SWAN: 0.05,
            ScenarioType.COMPETITIVE_THREAT: 0.4,
            ScenarioType.REGULATORY_CHANGE: 0.3,
            ScenarioType.ECONOMIC_DOWNTURN: 0.25,
            ScenarioType.TECHNOLOGY_DISRUPTION: 0.35,
        }
        return probabilities.get(scenario_type, 0.3)

    def _estimate_impact(self, scenario_type: ScenarioType, analysis: str) -> float:
        """Estimate impact score from analysis (simplified heuristic)."""
        # In production, use NLP to analyze sentiment and extract impact indicators
        impact_scores = {
            ScenarioType.OPTIMISTIC: 8.5,
            ScenarioType.REALISTIC: 6.0,
            ScenarioType.PESSIMISTIC: 3.0,
            ScenarioType.BLACK_SWAN: 9.0,
            ScenarioType.COMPETITIVE_THREAT: 7.0,
            ScenarioType.REGULATORY_CHANGE: 6.5,
            ScenarioType.ECONOMIC_DOWNTURN: 4.5,
            ScenarioType.TECHNOLOGY_DISRUPTION: 7.5,
        }
        return impact_scores.get(scenario_type, 5.0)

    def _extract_strategies(self, analysis: str) -> List[str]:
        """Extract mitigation strategies from analysis (simplified)."""
        # In production, use NLP to extract actionable strategies
        return [
            "Monitor key indicators",
            "Build strategic reserves",
            "Diversify risk exposure",
            "Develop contingency plans",
        ]

    def _extract_metrics(self, analysis: str) -> Dict[str, Any]:
        """Extract key metrics from analysis (simplified)."""
        # In production, use NLP to extract quantitative metrics
        return {"revenue_impact": "TBD", "timeline_impact": "TBD", "resource_requirements": "TBD"}

    def _extract_key_recommendations(self, synthesis: str) -> List[str]:
        """Extract key recommendations from synthesis (simplified)."""
        return [
            "Implement scenario monitoring system",
            "Build resilient business model",
            "Develop adaptive strategies",
            "Regular scenario review process",
        ]

    def _extract_monitoring_indicators(self, synthesis: str) -> List[str]:
        """Extract monitoring indicators from synthesis (simplified)."""
        return [
            "Market share changes",
            "Competitive activity",
            "Regulatory announcements",
            "Economic indicators",
            "Technology trends",
        ]
