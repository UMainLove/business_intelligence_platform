"""
Business Intelligence Platform integration with AG2 and all tools.
"""

from .workflows.swarm_scenarios import SwarmScenarioAnalysis
from .workflows.sequential_validation import SequentialValidationWorkflow
from .tools.api_tools import api_tool_executor, create_api_tool_spec
from .tools.document_tools import document_tool_executor, create_document_tool_spec
from .tools.database_tools import create_database_tool_spec
from .tools.database_production import database_tool_executor
from .tools.web_tools import web_search_executor, create_web_search_tool_spec
from .tools.rag_tools import rag_tool_executor, create_rag_tool_spec
from .tools.financial_tools import financial_tool_executor, create_financial_tool_spec
from typing import Dict, Any, List
from autogen import ConversableAgent, GroupChat, GroupChatManager
from autogen.tools import Tool
import logging

from .config import settings
from .chat import _anthropic_cfg, _compose_system
from .roles import economist_prompt, lawyer_prompt, sociologist_prompt, synthesizer_prompt
from .error_handling import (
    ModelError,
    handle_errors,
    retry_with_backoff,
    MODEL_RETRY_CONFIG,
    track_errors,
)

logger = logging.getLogger(__name__)

# Import all tools

# Import workflows

# Global instances for Streamlit session
_bi_manager = None
_bi_user_proxy = None
_bi_synthesizer = None
_bi_workflow = None
_bi_swarm = None


class BusinessIntelligenceAgent(ConversableAgent):
    """Enhanced agent with business intelligence tools."""

    def __init__(self, name: str, system_message: str, llm_config: Dict, tools: List[Tool] = None):
        super().__init__(
            name=name,
            system_message=system_message,
            llm_config=llm_config,
            human_input_mode="NEVER",
        )

        # Register tools with the agent
        if tools:
            for tool in tools:
                self.register_for_llm(name=tool["name"], description=tool["description"])(
                    self._create_tool_function(tool["name"])
                )

    def _create_tool_function(self, tool_name: str):
        """Create tool execution function with proper annotations for AG2."""

        if tool_name == "financial_calculator":

            def financial_calculator(operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
                """Execute financial calculations and modeling operations."""
                try:
                    return financial_tool_executor(operation, params)
                except Exception as e:
                    return {"error": f"Financial tool execution failed: {str(e)}"}

            return financial_calculator

        elif tool_name == "market_research_rag":

            def market_research_rag(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
                """Search and retrieve market research data."""
                try:
                    return rag_tool_executor(action, params)
                except Exception as e:
                    return {"error": f"RAG tool execution failed: {str(e)}"}

            return market_research_rag

        elif tool_name == "web_search":

            def web_search(search_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
                """Search the web for market intelligence."""
                try:
                    return web_search_executor(search_type, params)
                except Exception as e:
                    return {"error": f"Web search tool execution failed: {str(e)}"}

            return web_search

        elif tool_name == "business_database":

            def business_database(query_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
                """Query historical business data and benchmarks."""
                try:
                    return database_tool_executor(query_type, params)
                except Exception as e:
                    return {"error": f"Database tool execution failed: {str(e)}"}

            return business_database

        elif tool_name == "document_generator":

            def document_generator(document_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
                """Generate business documents and reports."""
                try:
                    return document_tool_executor(document_type, data)
                except Exception as e:
                    return {"error": f"Document generator execution failed: {str(e)}"}

            return document_generator

        elif tool_name == "external_api":

            def external_api(api_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
                """Access external APIs for business intelligence."""
                try:
                    return api_tool_executor(api_type, params)
                except Exception as e:
                    return {"error": f"External API execution failed: {str(e)}"}

            return external_api

        else:

            def unknown_tool(tool: str = tool_name) -> Dict[str, Any]:
                """Handle unknown tool requests."""
                return {"error": f"Unknown tool: {tool}"}

            return unknown_tool


def create_bi_tools_list() -> List[Dict[str, Any]]:
    """Create list of all available business intelligence tools."""
    return [
        create_financial_tool_spec(),
        create_rag_tool_spec(),
        create_web_search_tool_spec(),
        create_database_tool_spec(),
        create_document_tool_spec(),
        create_api_tool_spec(),
    ]


@retry_with_backoff(**MODEL_RETRY_CONFIG)
@handle_errors(error_mapping={ValueError: ModelError, KeyError: ModelError})
@track_errors
def build_bi_group():
    """Build enhanced business intelligence group with tools."""
    global _bi_manager, _bi_user_proxy, _bi_synthesizer, _bi_workflow, _bi_swarm

    try:
        if _bi_manager is not None:
            return _bi_manager, _bi_user_proxy, _bi_synthesizer, _bi_workflow, _bi_swarm

        logger.info("Building Business Intelligence agent group...")
    except Exception as e:
        logger.error(f"Error in build_bi_group: {str(e)}")
        raise ModelError(f"Failed to build BI group: {str(e)}")

    # Get all available tools
    bi_tools = create_bi_tools_list()

    # Enhanced agent configurations
    llm_economist = _anthropic_cfg(
        settings.model_specialists,
        temperature=settings.temperature_economist,
        max_tokens=settings.max_tokens_specialists,
        top_p=settings.top_p,
    )

    llm_lawyer = _anthropic_cfg(
        settings.model_specialists,
        temperature=settings.temperature_lawyer,
        max_tokens=settings.max_tokens_specialists,
        top_p=settings.top_p,
    )

    llm_sociologist = _anthropic_cfg(
        settings.model_specialists,
        temperature=settings.temperature_sociologist,
        max_tokens=settings.max_tokens_specialists,
        top_p=settings.top_p,
    )

    llm_synth = _anthropic_cfg(
        settings.model_synth,
        temperature=settings.temperature_synth,
        max_tokens=settings.max_tokens_synth,
        top_p=settings.top_p,
    )

    # Create enhanced agents with tools
    enhanced_economist_prompt = f"""
    {economist_prompt()}

    AVAILABLE TOOLS:
    You have access to powerful business intelligence tools:
    - Financial Calculator: Perform complex financial modeling, NPV, IRR, payback calculations
    - Market Research RAG: Search market data, competitor analysis, industry reports
    - Web Search: Real-time market intelligence, competitor information, trends
    - Business Database: Historical success rates, industry benchmarks, similar ventures
    - Document Generator: Create business plans, financial models, market analysis
    - External APIs: Company data, patent searches, regulatory information, funding data

    Use these tools proactively to provide data-driven insights and quantitative analysis.
    """

    enhanced_lawyer_prompt = f"""
    {lawyer_prompt()}

    AVAILABLE TOOLS:
    You have access to legal and regulatory intelligence tools:
    - External APIs: Research current regulations, compliance requirements, legal precedents
    - Business Database: Legal risk patterns from similar ventures
    - Web Search: Recent regulatory changes, legal developments
    - Document Generator: Create compliance checklists, risk assessments

    Use these tools to provide current, specific legal guidance and compliance strategies.
    """

    enhanced_sociologist_prompt = f"""
    {sociologist_prompt()}

    AVAILABLE TOOLS:
    You have access to social and market intelligence tools:
    - Market Research RAG: Consumer behavior studies, adoption patterns, social trends
    - Web Search: Current social movements, cultural shifts, demographic changes
    - Business Database: User adoption patterns from historical data
    - External APIs: Social media trends, demographic data

    Use these tools to provide insights on user behavior, social impact, and adoption dynamics.
    """

    # Create BusinessIntelligenceAgent instances
    economist = BusinessIntelligenceAgent(
        name="economist",
        system_message=_compose_system(enhanced_economist_prompt),
        llm_config=llm_economist,
        tools=bi_tools,
    )

    lawyer = BusinessIntelligenceAgent(
        name="lawyer",
        system_message=_compose_system(enhanced_lawyer_prompt),
        llm_config=llm_lawyer,
        tools=bi_tools,
    )

    sociologist = BusinessIntelligenceAgent(
        name="sociologist",
        system_message=_compose_system(enhanced_sociologist_prompt),
        llm_config=llm_sociologist,
        tools=bi_tools,
    )

    # Enhanced synthesizer
    enhanced_synthesizer_prompt = f"""
    {synthesizer_prompt()}

    TOOLS AVAILABLE:
    - Document Generator: Create comprehensive business documents
    - All analysis tools used by specialists for verification

    Use the document generator to create professional business documents based on the analysis.
    """

    synthesizer = BusinessIntelligenceAgent(
        name="synthesizer",
        system_message=enhanced_synthesizer_prompt,
        llm_config=llm_synth,
        tools=bi_tools,
    )

    # Human proxy
    user_proxy = ConversableAgent(
        name="human",
        system_message=(
            "You are the entrepreneur seeking business intelligence analysis. "
            "The AI agents will use advanced tools to provide comprehensive insights. "
            "Type DONE when you want the final comprehensive report. "
            "Type SEQUENTIAL to run structured phased validation. "
            "Type SWARM to run scenario analysis with multiple perspectives."
        ),
        human_input_mode="ALWAYS",
    )

    # Group chat
    chat = GroupChat(
        agents=[user_proxy, economist, lawyer, sociologist],
        speaker_selection_method="auto",
        max_round=8,  # Increased for tool usage
        allow_repeat_speaker=False,
    )

    # Manager
    manager = GroupChatManager(
        name="bi_orchestrator",
        groupchat=chat,
        llm_config=llm_economist,
    )

    # Create workflow instances
    workflow = SequentialValidationWorkflow()
    swarm = SwarmScenarioAnalysis()

    _bi_manager = manager
    _bi_user_proxy = user_proxy
    _bi_synthesizer = synthesizer
    _bi_workflow = workflow
    _bi_swarm = swarm

    return manager, user_proxy, synthesizer, workflow, swarm


def run_sequential_validation(business_data: Dict[str, Any]) -> Dict[str, Any]:
    """Run structured sequential validation workflow."""
    _, _, _, workflow, _ = build_bi_group()

    return workflow.run_full_validation(business_data)


def run_swarm_analysis(
    business_data: Dict[str, Any], scenarios: List[str] = None
) -> Dict[str, Any]:
    """Run swarm scenario analysis."""
    _, _, _, _, swarm = build_bi_group()

    # Convert scenario strings to enums if provided
    from .workflows.swarm_scenarios import ScenarioType

    scenario_types = None
    if scenarios:
        scenario_types = []
        for scenario in scenarios:
            try:
                scenario_types.append(ScenarioType(scenario.lower()))
            except ValueError:
                continue

    # Run swarm analysis
    scenario_results = swarm.run_swarm_analysis(business_data, scenario_types)

    # Synthesize results
    synthesis = swarm.synthesize_swarm_results(scenario_results, business_data)

    return synthesis


def run_enhanced_synthesis(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run enhanced synthesis with document generation."""
    _, _, synthesizer, _, _ = build_bi_group()

    # Generate comprehensive response
    response = synthesizer.generate_reply(messages=messages)

    # Extract business data from conversation for document generation
    business_data = {
        "business_name": "Analyzed Business Venture",
        "executive_summary": response[:500],
        # More extraction logic would go here
    }

    # Generate supporting documents
    try:
        # Generate executive summary document
        exec_summary_doc = document_tool_executor("executive_summary", business_data)

        return {
            "synthesis_response": response,
            "generated_documents": [exec_summary_doc],
            "analysis_complete": True,
        }
    except Exception as e:
        return {
            "synthesis_response": response,
            "generated_documents": [],
            "analysis_complete": True,
            "document_error": str(e),
        }


def get_bi_capabilities() -> Dict[str, Any]:
    """Get information about business intelligence capabilities."""
    return {
        "tools_available": len(create_bi_tools_list()),
        "tool_categories": [
            "Financial Modeling & Analysis",
            "Market Research & RAG",
            "Web Intelligence & Search",
            "Historical Business Data",
            "Document Generation",
            "External API Integration",
        ],
        "workflows_available": [
            "Sequential Validation (7 phases)",
            "Swarm Scenario Analysis (8 scenario types)",
            "Enhanced Group Chat with Tools",
        ],
        "specialized_agents": [
            "Economist (with financial tools)",
            "Lawyer (with regulatory tools)",
            "Sociologist (with market intelligence)",
            "Synthesizer (with document generation)",
        ],
        "document_types": [
            "Business Plans",
            "Market Analysis Reports",
            "Financial Models",
            "Risk Assessments",
            "Executive Summaries",
        ],
    }
