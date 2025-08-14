"""
Sequential chat workflow for phased business validation.
"""
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
from autogen import ConversableAgent, LLMConfig
from ..config import settings
from ..tools import (
    financial_tool_executor, rag_tool_executor, web_search_executor,
    database_tool_executor, document_tool_executor, api_tool_executor
)

class ValidationPhase(Enum):
    """Validation phases in sequential order."""
    IDEA_REFINEMENT = "idea_refinement"
    MARKET_VALIDATION = "market_validation"
    FINANCIAL_MODELING = "financial_modeling"
    RISK_ASSESSMENT = "risk_assessment"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    FINAL_SYNTHESIS = "final_synthesis"

@dataclass
class PhaseResult:
    """Result from a validation phase."""
    phase: ValidationPhase
    success: bool
    data: Dict[str, Any]
    recommendations: List[str]
    next_phase: ValidationPhase = None
    confidence_score: float = 0.0

class SequentialValidationWorkflow:
    """Orchestrates sequential business validation workflow."""
    
    def __init__(self):
        self.current_phase = ValidationPhase.IDEA_REFINEMENT
        self.phase_results: Dict[ValidationPhase, PhaseResult] = {}
        self.business_context = {}
        self.agents = self._create_specialized_agents()
    
    def _create_anthropic_config(self, temperature: float, max_tokens: int = 2000) -> LLMConfig:
        """Create anthropic configuration for agents."""
        return LLMConfig(
            api_type="anthropic",
            model=settings.model_specialists,
            api_key=settings.anthropic_key,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=settings.top_p
        )
    
    def _create_specialized_agents(self) -> Dict[str, ConversableAgent]:
        """Create specialized agents for each phase."""
        agents = {}
        
        # Idea Refinement Agent
        agents['idea_refiner'] = ConversableAgent(
            name="idea_refiner",
            system_message=(
                "You are an expert business consultant specializing in idea refinement and opportunity assessment. "
                "Help entrepreneurs clarify their business concepts, identify core value propositions, and define target markets. "
                "Ask probing questions to uncover assumptions and refine the business idea."
            ),
            llm_config=self._create_anthropic_config(0.4),  # Higher creativity
            human_input_mode="NEVER"
        )
        
        # Market Validation Agent
        agents['market_validator'] = ConversableAgent(
            name="market_validator",
            system_message=(
                "You are a market research expert. Analyze market size, customer needs, and market dynamics. "
                "Use available tools to gather market intelligence and validate market assumptions. "
                "Focus on TAM/SAM/SOM analysis and customer discovery insights."
            ),
            llm_config=self._create_anthropic_config(0.2),  # More factual
            human_input_mode="NEVER"
        )
        
        # Financial Modeling Agent
        agents['financial_modeler'] = ConversableAgent(
            name="financial_modeler",
            system_message=(
                "You are a financial modeling expert. Build comprehensive financial models, analyze unit economics, "
                "and project business performance. Use financial tools to calculate key metrics like NPV, IRR, payback period. "
                "Create realistic revenue projections and identify funding requirements."
            ),
            llm_config=self._create_anthropic_config(0.1),  # Very precise
            human_input_mode="NEVER"
        )
        
        # Risk Assessment Agent
        agents['risk_assessor'] = ConversableAgent(
            name="risk_assessor",
            system_message=(
                "You are a risk management expert. Identify, assess, and prioritize business risks across all dimensions: "
                "market, financial, operational, legal, and strategic. Develop mitigation strategies for identified risks. "
                "Quantify risk impact and probability where possible."
            ),
            llm_config=self._create_anthropic_config(0.3),  # Balanced
            human_input_mode="NEVER"
        )
        
        # Competitive Analysis Agent
        agents['competitive_analyst'] = ConversableAgent(
            name="competitive_analyst",
            system_message=(
                "You are a competitive intelligence expert. Analyze competitive landscape, identify key competitors, "
                "assess competitive advantages and threats. Use web search and database tools to gather competitor intelligence. "
                "Develop competitive positioning strategies."
            ),
            llm_config=self._create_anthropic_config(0.2),  # Factual
            human_input_mode="NEVER"
        )
        
        # Regulatory Compliance Agent
        agents['compliance_expert'] = ConversableAgent(
            name="compliance_expert",
            system_message=(
                "You are a regulatory and legal compliance expert. Identify applicable regulations, licensing requirements, "
                "and legal structures. Assess compliance costs and timelines. Use external APIs to research current regulations. "
                "Provide actionable compliance roadmaps."
            ),
            llm_config=self._create_anthropic_config(0.1),  # Very precise
            human_input_mode="NEVER"
        )
        
        # Synthesis Agent
        agents['synthesizer'] = ConversableAgent(
            name="synthesizer",
            system_message=(
                "You are a senior business strategist. Synthesize insights from all validation phases into a comprehensive "
                "business assessment. Identify critical success factors, key assumptions to test, and recommended next steps. "
                "Generate executive summary and strategic recommendations."
            ),
            llm_config=self._create_anthropic_config(0.15),  # Structured
            human_input_mode="NEVER"
        )
        
        return agents
    
    def execute_phase(self, phase: ValidationPhase, input_data: Dict[str, Any]) -> PhaseResult:
        """Execute a specific validation phase."""
        
        if phase == ValidationPhase.IDEA_REFINEMENT:
            return self._execute_idea_refinement(input_data)
        elif phase == ValidationPhase.MARKET_VALIDATION:
            return self._execute_market_validation(input_data)
        elif phase == ValidationPhase.FINANCIAL_MODELING:
            return self._execute_financial_modeling(input_data)
        elif phase == ValidationPhase.RISK_ASSESSMENT:
            return self._execute_risk_assessment(input_data)
        elif phase == ValidationPhase.COMPETITIVE_ANALYSIS:
            return self._execute_competitive_analysis(input_data)
        elif phase == ValidationPhase.REGULATORY_COMPLIANCE:
            return self._execute_regulatory_compliance(input_data)
        elif phase == ValidationPhase.FINAL_SYNTHESIS:
            return self._execute_final_synthesis(input_data)
        else:
            return PhaseResult(
                phase=phase,
                success=False,
                data={'error': f'Unknown phase: {phase}'},
                recommendations=[]
            )
    
    def _execute_idea_refinement(self, input_data: Dict[str, Any]) -> PhaseResult:
        """Execute idea refinement phase."""
        agent = self.agents['idea_refiner']
        
        # Prepare context
        business_idea = input_data.get('business_idea', '')
        target_market = input_data.get('target_market', '')
        
        prompt = f"""
        Business Idea: {business_idea}
        Target Market: {target_market}
        
        Please help refine this business idea by:
        1. Identifying the core value proposition
        2. Clarifying the target customer segments
        3. Defining the problem being solved
        4. Suggesting improvements to the concept
        5. Highlighting key assumptions to validate
        
        Provide a structured analysis with specific recommendations.
        """
        
        try:
            response = agent.generate_reply(messages=[{"role": "user", "content": prompt}])
            
            # Parse response and extract key insights
            refined_data = {
                'original_idea': business_idea,
                'refined_concept': response,
                'value_proposition': 'Extracted from analysis',  # In production, use NLP to extract
                'target_segments': ['Segment 1', 'Segment 2'],
                'key_assumptions': ['Assumption 1', 'Assumption 2']
            }
            
            return PhaseResult(
                phase=ValidationPhase.IDEA_REFINEMENT,
                success=True,
                data=refined_data,
                recommendations=[
                    "Validate core value proposition with target customers",
                    "Define minimum viable product (MVP) scope",
                    "Research competitive alternatives"
                ],
                next_phase=ValidationPhase.MARKET_VALIDATION,
                confidence_score=0.8
            )
            
        except Exception as e:
            return PhaseResult(
                phase=ValidationPhase.IDEA_REFINEMENT,
                success=False,
                data={'error': str(e)},
                recommendations=["Review business idea description", "Try again with more specific details"]
            )
    
    def _execute_market_validation(self, input_data: Dict[str, Any]) -> PhaseResult:
        """Execute market validation phase."""
        agent = self.agents['market_validator']
        
        # Use RAG and web search tools
        industry = input_data.get('industry', '')
        target_market = input_data.get('target_market', '')
        
        # Get market research data
        market_data = rag_tool_executor("get_insights", {"query": f"{industry} market size trends"})
        web_trends = web_search_executor("market_trends", {"industry": industry})
        
        prompt = f"""
        Industry: {industry}
        Target Market: {target_market}
        
        Market Research Data:
        {market_data}
        
        Web Trends:
        {web_trends}
        
        Please analyze:
        1. Total Addressable Market (TAM)
        2. Serviceable Addressable Market (SAM)
        3. Serviceable Obtainable Market (SOM)
        4. Market growth trends and drivers
        5. Customer segments and needs
        6. Market entry barriers
        
        Provide specific market sizing and validation insights.
        """
        
        try:
            response = agent.generate_reply(messages=[{"role": "user", "content": prompt}])
            
            validated_data = {
                'market_size_analysis': response,
                'tam': '$XXXb',  # Extract from analysis
                'sam': '$XXm',
                'som': '$Xm',
                'market_data': market_data,
                'web_trends': web_trends,
                'growth_rate': 'X% CAGR'
            }
            
            return PhaseResult(
                phase=ValidationPhase.MARKET_VALIDATION,
                success=True,
                data=validated_data,
                recommendations=[
                    "Conduct customer interviews to validate assumptions",
                    "Build MVP to test market demand",
                    "Analyze customer acquisition channels"
                ],
                next_phase=ValidationPhase.FINANCIAL_MODELING,
                confidence_score=0.75
            )
            
        except Exception as e:
            return PhaseResult(
                phase=ValidationPhase.MARKET_VALIDATION,
                success=False,
                data={'error': str(e)},
                recommendations=["Gather more market data", "Define target market more specifically"]
            )
    
    def _execute_financial_modeling(self, input_data: Dict[str, Any]) -> PhaseResult:
        """Execute financial modeling phase."""
        agent = self.agents['financial_modeler']
        
        # Use financial tools
        projected_revenue = input_data.get('projected_revenue', 1000000)
        growth_rate = input_data.get('growth_rate', 0.25)
        
        # Calculate financial projections
        projections = financial_tool_executor("projection", {
            "initial_revenue": projected_revenue,
            "growth_rate": growth_rate,
            "years": 5
        })
        
        # Calculate unit economics if provided
        unit_economics = {}
        if input_data.get('cac') and input_data.get('ltv'):
            unit_economics = financial_tool_executor("unit_economics", {
                "customer_acquisition_cost": input_data['cac'],
                "customer_lifetime_value": input_data['ltv'],
                "monthly_churn_rate": input_data.get('churn_rate', 0.05),
                "average_revenue_per_user": input_data.get('arpu', 100)
            })
        
        prompt = f"""
        Financial Projections:
        {projections}
        
        Unit Economics:
        {unit_economics}
        
        Please create a comprehensive financial model including:
        1. Revenue projections and assumptions
        2. Cost structure analysis
        3. Profitability timeline
        4. Cash flow analysis
        5. Funding requirements
        6. Key financial metrics and ratios
        7. Sensitivity analysis
        
        Provide specific financial insights and recommendations.
        """
        
        try:
            response = agent.generate_reply(messages=[{"role": "user", "content": prompt}])
            
            financial_data = {
                'financial_model': response,
                'projections': projections,
                'unit_economics': unit_economics,
                'funding_needs': '$XXm',  # Extract from analysis
                'break_even_timeline': 'XX months',
                'key_metrics': {}
            }
            
            return PhaseResult(
                phase=ValidationPhase.FINANCIAL_MODELING,
                success=True,
                data=financial_data,
                recommendations=[
                    "Validate pricing assumptions with customers",
                    "Test unit economics with pilot customers",
                    "Prepare financial model for investors"
                ],
                next_phase=ValidationPhase.RISK_ASSESSMENT,
                confidence_score=0.7
            )
            
        except Exception as e:
            return PhaseResult(
                phase=ValidationPhase.FINANCIAL_MODELING,
                success=False,
                data={'error': str(e)},
                recommendations=["Gather more financial assumptions", "Define revenue model clearly"]
            )
    
    def _execute_risk_assessment(self, input_data: Dict[str, Any]) -> PhaseResult:
        """Execute risk assessment phase."""
        agent = self.agents['risk_assessor']
        
        # Get historical data for risk benchmarking
        industry = input_data.get('industry', '')
        business_model = input_data.get('business_model', '')
        
        historical_data = database_tool_executor("success_rates", {"industry": industry})
        
        prompt = f"""
        Business Context:
        - Industry: {industry}
        - Business Model: {business_model}
        
        Historical Industry Data:
        {historical_data}
        
        Please conduct a comprehensive risk assessment:
        1. Market risks (competition, market size, customer adoption)
        2. Financial risks (funding, cash flow, profitability)
        3. Operational risks (execution, team, technology)
        4. Legal and regulatory risks
        5. Strategic risks (competitive response, market timing)
        
        For each risk, provide:
        - Impact level (High/Medium/Low)
        - Probability (High/Medium/Low)
        - Mitigation strategies
        - Monitoring indicators
        """
        
        try:
            response = agent.generate_reply(messages=[{"role": "user", "content": prompt}])
            
            risk_data = {
                'risk_assessment': response,
                'historical_benchmarks': historical_data,
                'overall_risk_score': 6.5,  # Calculate from analysis
                'high_priority_risks': [],
                'mitigation_plan': {}
            }
            
            return PhaseResult(
                phase=ValidationPhase.RISK_ASSESSMENT,
                success=True,
                data=risk_data,
                recommendations=[
                    "Implement risk monitoring dashboard",
                    "Develop contingency plans for high-impact risks",
                    "Regular risk assessment reviews"
                ],
                next_phase=ValidationPhase.COMPETITIVE_ANALYSIS,
                confidence_score=0.8
            )
            
        except Exception as e:
            return PhaseResult(
                phase=ValidationPhase.RISK_ASSESSMENT,
                success=False,
                data={'error': str(e)},
                recommendations=["Define business model more clearly", "Provide industry context"]
            )
    
    def _execute_competitive_analysis(self, input_data: Dict[str, Any]) -> PhaseResult:
        """Execute competitive analysis phase."""
        agent = self.agents['competitive_analyst']
        
        business_idea = input_data.get('business_idea', '')
        target_market = input_data.get('target_market', '')
        
        # Use web search and API tools
        competitors = web_search_executor("competitors", {
            "business_idea": business_idea,
            "target_market": target_market
        })
        
        prompt = f"""
        Business Idea: {business_idea}
        Target Market: {target_market}
        
        Competitive Intelligence:
        {competitors}
        
        Please analyze:
        1. Direct and indirect competitors
        2. Competitive advantages and differentiators
        3. Market positioning opportunities
        4. Competitive threats and responses
        5. Barriers to entry
        6. White space opportunities
        
        Provide actionable competitive insights and positioning strategy.
        """
        
        try:
            response = agent.generate_reply(messages=[{"role": "user", "content": prompt}])
            
            competitive_data = {
                'competitive_analysis': response,
                'competitors_data': competitors,
                'competitive_advantages': [],
                'positioning_strategy': '',
                'competitive_risks': []
            }
            
            return PhaseResult(
                phase=ValidationPhase.COMPETITIVE_ANALYSIS,
                success=True,
                data=competitive_data,
                recommendations=[
                    "Develop unique value proposition",
                    "Monitor competitive moves regularly",
                    "Build defensible competitive moats"
                ],
                next_phase=ValidationPhase.REGULATORY_COMPLIANCE,
                confidence_score=0.75
            )
            
        except Exception as e:
            return PhaseResult(
                phase=ValidationPhase.COMPETITIVE_ANALYSIS,
                success=False,
                data={'error': str(e)},
                recommendations=["Define competitive scope more clearly"]
            )
    
    def _execute_regulatory_compliance(self, input_data: Dict[str, Any]) -> PhaseResult:
        """Execute regulatory compliance phase."""
        agent = self.agents['compliance_expert']
        
        industry = input_data.get('industry', '')
        region = input_data.get('region', 'US')
        
        # Use API tools for regulatory data
        regulations = api_tool_executor("regulations", {
            "industry": industry,
            "region": region
        })
        
        prompt = f"""
        Industry: {industry}
        Operating Region: {region}
        
        Regulatory Information:
        {regulations}
        
        Please analyze:
        1. Applicable regulations and compliance requirements
        2. Licensing and permit requirements
        3. Compliance costs and timelines
        4. Legal structure recommendations
        5. Ongoing compliance obligations
        6. Regulatory risks and penalties
        
        Provide a compliance roadmap with specific next steps.
        """
        
        try:
            response = agent.generate_reply(messages=[{"role": "user", "content": prompt}])
            
            compliance_data = {
                'compliance_analysis': response,
                'regulatory_data': regulations,
                'compliance_costs': '',
                'timeline': '',
                'legal_structure': ''
            }
            
            return PhaseResult(
                phase=ValidationPhase.REGULATORY_COMPLIANCE,
                success=True,
                data=compliance_data,
                recommendations=[
                    "Consult with legal experts",
                    "Begin compliance implementation early",
                    "Budget for ongoing compliance costs"
                ],
                next_phase=ValidationPhase.FINAL_SYNTHESIS,
                confidence_score=0.8
            )
            
        except Exception as e:
            return PhaseResult(
                phase=ValidationPhase.REGULATORY_COMPLIANCE,
                success=False,
                data={'error': str(e)},
                recommendations=["Research industry-specific regulations"]
            )
    
    def _execute_final_synthesis(self, input_data: Dict[str, Any]) -> PhaseResult:
        """Execute final synthesis phase."""
        agent = self.agents['synthesizer']
        
        # Compile all phase results
        all_phases_data = {
            phase.value: result.data for phase, result in self.phase_results.items()
        }
        
        prompt = f"""
        All Validation Phase Results:
        {all_phases_data}
        
        Please synthesize insights into a comprehensive business assessment:
        1. Executive summary of key findings
        2. Business viability assessment
        3. Critical success factors
        4. Key risks and mitigation strategies
        5. Investment recommendation (Go/No-Go/Pivot)
        6. Next steps and milestones
        7. Resource requirements
        8. Timeline for implementation
        
        Provide a structured final assessment with clear recommendations.
        """
        
        try:
            response = agent.generate_reply(messages=[{"role": "user", "content": prompt}])
            
            # Generate final documents
            business_plan = document_tool_executor("business_plan", {
                'name': input_data.get('business_name', 'Business Venture'),
                'executive_summary': 'Generated from synthesis',
                'industry': input_data.get('industry', ''),
                'target_market': input_data.get('target_market', ''),
                'business_model': input_data.get('business_model', '')
            })
            
            synthesis_data = {
                'final_assessment': response,
                'all_phases_data': all_phases_data,
                'business_plan_document': business_plan,
                'overall_score': 7.5,  # Calculate weighted score from all phases
                'recommendation': 'GO',  # Extract from analysis
                'next_steps': []
            }
            
            return PhaseResult(
                phase=ValidationPhase.FINAL_SYNTHESIS,
                success=True,
                data=synthesis_data,
                recommendations=[
                    "Execute recommended next steps",
                    "Regular progress reviews",
                    "Continuous market validation"
                ],
                confidence_score=0.85
            )
            
        except Exception as e:
            return PhaseResult(
                phase=ValidationPhase.FINAL_SYNTHESIS,
                success=False,
                data={'error': str(e)},
                recommendations=["Review all phase results", "Ensure complete data"]
            )
    
    def run_full_validation(self, initial_data: Dict[str, Any]) -> Dict[ValidationPhase, PhaseResult]:
        """Run complete sequential validation workflow."""
        self.business_context = initial_data.copy()
        current_data = initial_data.copy()
        
        # Define phase execution order
        phases = [
            ValidationPhase.IDEA_REFINEMENT,
            ValidationPhase.MARKET_VALIDATION,
            ValidationPhase.FINANCIAL_MODELING,
            ValidationPhase.RISK_ASSESSMENT,
            ValidationPhase.COMPETITIVE_ANALYSIS,
            ValidationPhase.REGULATORY_COMPLIANCE,
            ValidationPhase.FINAL_SYNTHESIS
        ]
        
        for phase in phases:
            result = self.execute_phase(phase, current_data)
            self.phase_results[phase] = result
            
            if result.success:
                # Update context with new insights
                current_data.update(result.data)
            else:
                # Stop execution on failure (could implement retry logic)
                break
        
        return self.phase_results
    
    def get_phase_summary(self) -> Dict[str, Any]:
        """Get summary of all completed phases."""
        summary = {
            'total_phases': len(ValidationPhase),
            'completed_phases': len(self.phase_results),
            'success_rate': len([r for r in self.phase_results.values() if r.success]) / len(self.phase_results) if self.phase_results else 0,
            'average_confidence': sum(r.confidence_score for r in self.phase_results.values()) / len(self.phase_results) if self.phase_results else 0,
            'phase_details': {}
        }
        
        for phase, result in self.phase_results.items():
            summary['phase_details'][phase.value] = {
                'success': result.success,
                'confidence': result.confidence_score,
                'recommendations_count': len(result.recommendations)
            }
        
        return summary