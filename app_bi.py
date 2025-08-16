import json
import time
from pathlib import Path

import streamlit as st

from src.business_intelligence import (
    build_bi_group,
    get_bi_capabilities,
    run_enhanced_synthesis,
    run_sequential_validation,
    run_swarm_analysis,
)
from src.chat import (
    clear_memory,
    get_memory,
    get_messages,
    reset_messages,
    set_memory,
    update_memory_from_chat,
)
from src.config import settings
from src.error_handling import safe_execute
from src.health_monitor import health_monitor
from src.util import estimate_cost_usd, estimate_tokens_chars, get_cost_breakdown
from src.workflows.swarm_scenarios import ScenarioType

st.set_page_config(page_title="Business Intelligence Platform", page_icon="🧠", layout="wide")
st.title("🧠 Business Intelligence Platform")
st.caption(
    "AI-Powered Business Analysis with Market Research, Financial Modeling & Scenario Planning"
)


def render_history():
    """Render chat history with enhanced formatting."""
    for role, msg in st.session_state.history:
        # Use appropriate icons for different roles
        if role == "economist":
            icon = "💰"
        elif role == "lawyer":
            icon = "⚖️"
        elif role == "sociologist":
            icon = "👥"
        elif role == "synthesizer":
            icon = "📊"
        elif role == "human":
            icon = "👤"
        elif role == "error":
            icon = "⚠️"
        else:
            icon = role

        with st.chat_message(role, avatar=icon):
            # Enhanced message display
            if role == "error":
                st.error(msg)
            elif "tool_calls" in str(msg).lower() or "api" in str(msg).lower():
                st.info("🔧 Using business intelligence tools...")
                st.markdown(msg)
            else:
                st.markdown(msg)


# Initialize conversation state on first load
if "manager" not in st.session_state:
    # Initialize Business Intelligence Platform
    manager, user_proxy, synthesizer, workflow, swarm = build_bi_group()
    st.session_state.manager = manager
    st.session_state.user_proxy = user_proxy
    st.session_state.synthesizer = synthesizer
    st.session_state.workflow = workflow
    st.session_state.swarm = swarm
    st.session_state.history = []
    st.session_state.last_len = 0
    st.session_state.mode = "chat"  # chat, sequential, swarm
if "session_name" not in st.session_state:
    st.session_state.session_name = f"bi_session_{int(time.time())}"
if "bi_capabilities" not in st.session_state:
    st.session_state.bi_capabilities = get_bi_capabilities()

# Create main layout with tabs
tab1, tab2, tab3 = st.tabs(
    ["🎯 Interactive Analysis", "📋 Sequential Validation", "🌪️ Scenario Analysis"]
)

# Sidebar: actions & info
with st.sidebar:
    st.text_input("Session name", key="session_name")

    # System Health Status
    st.markdown("---")
    st.subheader("🏥 System Health")

    # Add health check button
    if st.button("🔄 Check Health", help="Check system health status"):
        with st.spinner("Checking system health..."):
            health_data = safe_execute(
                health_monitor.get_comprehensive_health,
                fallback_value={"overall_status": "unknown", "error": "Health check failed"},
                error_context="System health check",
            )
            st.session_state.last_health_check = health_data

    # Display health status
    if hasattr(st.session_state, "last_health_check"):
        health = st.session_state.last_health_check
        status = health.get("overall_status", "unknown")

        # Status indicator
        if status == "healthy":
            st.success("🟢 System Healthy")
        elif status == "degraded":
            st.warning("🟡 System Degraded")
        elif status == "unhealthy":
            st.error("🔴 System Unhealthy")
        else:
            st.info("🔵 Status Unknown")

        # Error summary
        if "checks" in health and "errors" in health["checks"]:
            error_check = health["checks"]["errors"]
            if error_check["details"].get("total_errors", 0) > 0:
                st.metric(
                    "Recent Errors",
                    error_check["details"]["total_errors"],
                    help="Errors in the last hour",
                )

    # Business Intelligence Capabilities
    st.markdown("---")
    st.subheader("🧠 BI Capabilities")
    capabilities = st.session_state.bi_capabilities

    with st.expander("📊 Available Tools", expanded=False):
        for category in capabilities["tool_categories"]:
            st.caption(f"• {category}")

    with st.expander("🔄 Analysis Workflows", expanded=False):
        for workflow in capabilities["workflows_available"]:
            st.caption(f"• {workflow}")

    with st.expander("🤖 AI Specialists", expanded=False):
        for agent in capabilities["specialized_agents"]:
            st.caption(f"• {agent}")

    st.markdown("---")
    st.subheader("Session Controls")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Reset", use_container_width=True):
            reset_messages()
            st.session_state.history = []
            st.session_state.last_len = 0
            st.rerun()

    with col2:
        if st.button("📊 BI Mode", use_container_width=True):
            # Switch to Business Intelligence mode
            st.session_state.mode = "bi"
            st.rerun()

    st.markdown("---")
    st.subheader("Models & Configuration")

    # Models
    st.caption("🧑‍💼 Specialists")
    st.code(settings.model_specialists, language="text")
    st.caption("📊 Synthesizer")
    st.code(settings.model_synth, language="text")
    st.caption("🧠 Memory Extractor")
    st.code(settings.model_memory, language="text")

    # Temperature settings
    with st.expander("Temperature Settings", expanded=False):
        st.caption(f"Economist: {settings.temperature_economist}")
        st.caption(f"Lawyer: {settings.temperature_lawyer}")
        st.caption(f"Sociologist: {settings.temperature_sociologist}")
        st.caption(f"Synthesizer: {settings.temperature_synth}")
        st.caption(f"Memory: {settings.temperature_memory}")

    # Token limits
    with st.expander("Token Limits", expanded=False):
        st.caption(f"Specialists: {settings.max_tokens_specialists:,}")
        st.caption(f"Synthesizer: {settings.max_tokens_synth:,}")
        st.caption(f"Memory: {settings.max_tokens_memory:,}")

    # Advanced parameters
    with st.expander("Advanced Parameters", expanded=False):
        st.caption(f"Top-p: {settings.top_p}")
        st.caption(f"Top-k: {settings.top_k if settings.top_k > 0 else 'disabled'}")
        if settings.thinking_enabled:
            st.caption(f"Thinking budget: {settings.thinking_budget_tokens:,} tokens")

    st.markdown("---")
    st.subheader("Export & Documents")

    if st.button("💾 Export Transcript", use_container_width=True):
        messages = get_messages()
        Path("data/sessions").mkdir(parents=True, exist_ok=True)
        out = Path("data/sessions") / f"{st.session_state.session_name}_{int(time.time())}.json"
        out.write_text(json.dumps(messages, indent=2), encoding="utf-8")
        st.success(f"Saved: {out}")

    # Show generated documents
    docs_path = Path("data/generated_docs")
    if docs_path.exists():
        docs = list(docs_path.glob("*.md"))
        if docs:
            st.write(f"📄 {len(docs)} documents generated")
            with st.expander("Recent Documents", expanded=False):
                for doc in sorted(docs, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                    st.caption(f"• {doc.name}")

    st.markdown("---")
    st.subheader("Memory")
    cur_mem = get_memory()
    mem_text = st.text_area(
        "Current memory (editable)",
        value="\n".join(
            [
                f"Idea: {cur_mem.get('idea', '')}",
                f"Target market: {cur_mem.get('target_market', '')}",
                f"Customer: {cur_mem.get('customer', '')}",
                f"Region: {cur_mem.get('region', '')}",
                f"Pricing model: {cur_mem.get('pricing_model', '')}",
                f"Key constraints: {', '.join(cur_mem.get('key_constraints', []))}",
                f"Risks: {', '.join(cur_mem.get('risks', []))}",
                f"Assumptions: {', '.join(cur_mem.get('assumptions', []))}",
            ]
        ),
        height=180,
    )
    colA, colB, colC = st.columns(3)
    with colA:
        if st.button("🧠 Update from chat", use_container_width=True):
            mem = update_memory_from_chat()
            st.success("Memory updated from conversation.")
            st.rerun()
    with colB:
        if st.button("💾 Save edits", use_container_width=True):
            parsed = {
                "idea": "",
                "target_market": "",
                "customer": "",
                "region": "",
                "pricing_model": "",
                "key_constraints": [],
                "risks": [],
                "assumptions": [],
            }
            for line in mem_text.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    k = k.strip().lower()
                    v = v.strip()
                    if k in parsed and isinstance(parsed[k], list):
                        parsed[k] = [s.strip() for s in v.split(",") if s.strip()]
                    elif k in parsed:
                        parsed[k] = v
            m, u, s = set_memory(parsed)  # rebuilds agents & keeps transcript
            st.session_state.manager, st.session_state.user_proxy, st.session_state.synthesizer = (
                m,
                u,
                s,
            )
            st.success("Memory saved and applied to agents.")
    with colC:
        if st.button("🧹 Clear", use_container_width=True):
            m, u, s = clear_memory()  # rebuilds agents & keeps transcript
            st.session_state.manager, st.session_state.user_proxy, st.session_state.synthesizer = (
                m,
                u,
                s,
            )
            st.success("Memory cleared.")
            st.rerun()

    st.markdown("---")
    st.subheader("Cost Estimation")
    msgs = get_messages()
    approx_tokens = estimate_tokens_chars(msgs)
    cost = estimate_cost_usd(
        approx_tokens,
        price_in_specialists=settings.price_in_specialists,
        price_out_specialists=settings.price_out_specialists,
        price_in_synth=settings.price_in_synth,
        price_out_synth=settings.price_out_synth,
        use_bi_pricing=True,  # Use enhanced BI platform pricing
    )

    # Show enhanced pricing breakdown
    if approx_tokens > 0:
        cost_breakdown = get_cost_breakdown(approx_tokens, use_bi_pricing=True)

        with st.expander("Enhanced BI Cost Breakdown", expanded=False):
            st.caption(f"**Pricing Model:** {cost_breakdown['pricing_model']}")
            if cost_breakdown.get("cost_increase_vs_standard", 0) > 0:
                st.caption(
                    f"**Cost increase vs standard:** +{cost_breakdown['cost_increase_vs_standard']:.1f}% (due to tool usage)"
                )

            st.caption("**Token Distribution:**")
            breakdown = cost_breakdown["breakdown"]
            st.caption(
                f"• Input (context): {breakdown['input']['percentage']:.1f}% | {breakdown['input']['tokens']:,} tokens | ${breakdown['input']['cost']:.4f}"
            )
            st.caption(
                f"• Specialists output: {breakdown['specialists_output']['percentage']:.1f}% | {breakdown['specialists_output']['tokens']:,} tokens | ${breakdown['specialists_output']['cost']:.4f}"
            )
            st.caption(
                f"• Synthesizer output: {breakdown['synthesizer_output']['percentage']:.1f}% | {breakdown['synthesizer_output']['tokens']:,} tokens | ${breakdown['synthesizer_output']['cost']:.4f}"
            )
            if breakdown.get("tool_overhead"):
                st.caption(
                    f"• Tool overhead: {breakdown['tool_overhead']['percentage']:.1f}% | {breakdown['tool_overhead']['tokens']:,} tokens | ${breakdown['tool_overhead']['cost']:.4f}"
                )

            st.caption(
                f"**Model Rates:** Specialists ${settings.price_in_specialists}/1K in, ${settings.price_out_specialists}/1K out | Synthesizer ${settings.price_in_synth}/1K in, ${settings.price_out_synth}/1K out"
            )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total tokens", value=f"{approx_tokens:,}")
    with col2:
        if cost is not None:
            st.metric("BI Platform cost", value=f"${cost:,.4f}")
    with col3:
        if approx_tokens > 0:
            standard_cost = estimate_cost_usd(approx_tokens, use_bi_pricing=False)
            if standard_cost:
                savings_pct = ((cost / standard_cost - 1) * 100) if cost > standard_cost else 0
                st.metric("vs Standard", value=f"+{savings_pct:.1f}%", delta="Enhanced features")

# Tab 1: Interactive Analysis
with tab1:
    st.markdown("### 🎯 Interactive Business Analysis")
    st.markdown("Chat with AI specialists who have access to advanced business intelligence tools.")

    # Display current configuration info
    with st.expander("ℹ️ Current Configuration", expanded=False):
        st.info(
            f"**Active Models:**\n"
            f"- Specialists: {settings.model_specialists.split('-')[-1]}\n"
            f"- Synthesizer: {settings.model_synth.split('-')[-1]}\n"
            f"- Memory: {settings.model_memory.split('-')[-1]}\n\n"
            f"**Performance:** Optimized with role-specific temperatures and token limits\n\n"
            f"**Available Tools:** Financial modeling, Market research, Web intelligence, Historical data, Document generation, External APIs"
        )

    # Render chat history
    render_history()

    # Chat input
    prompt = st.chat_input(
        "Describe your business idea… (type DONE for comprehensive report, SEQUENTIAL for phased analysis, SWARM for scenario planning)"
    )

    if prompt:
        # Handle special commands
        if prompt.strip().upper() == "SEQUENTIAL":
            st.session_state.mode = "sequential"
            st.rerun()
        elif prompt.strip().upper() == "SWARM":
            st.session_state.mode = "swarm"
            st.rerun()
        elif prompt.strip().upper() == "DONE":
            # Enhanced synthesis with document generation
            st.session_state.history.append(("human", prompt))

            with st.spinner("Generating comprehensive analysis and documents..."):
                msgs = get_messages()
                synthesis_result = run_enhanced_synthesis(msgs)

                # Display synthesis
                st.session_state.history.append(
                    ("synthesizer", synthesis_result["synthesis_response"])
                )

                # Display generated documents
                if synthesis_result.get("generated_documents"):
                    for doc in synthesis_result["generated_documents"]:
                        st.success(f"📄 Generated: {doc['filename']} ({doc['word_count']} words)")

            st.rerun()
        else:
            # Regular chat interaction with enhanced agents
            st.session_state.history.append(("human", prompt))

            with st.spinner("AI specialists analyzing with business intelligence tools..."):
                try:
                    # Safely execute chat interaction
                    chat_result = safe_execute(
                        st.session_state.user_proxy.initiate_chat,
                        recipient=st.session_state.manager,
                        message=prompt,
                        fallback_value=None,
                        error_context=f"Chat interaction with prompt: {prompt[:50]}...",
                    )

                    if chat_result is None:
                        st.error(
                            "⚠️ Chat interaction failed. Please try again with a different prompt."
                        )
                        # Add error message to history
                        st.session_state.history.append(
                            (
                                "error",
                                "Chat interaction failed. The system may be experiencing issues.",
                            )
                        )
                    else:
                        # Collect new agent messages
                        msgs = get_messages()
                        for m in msgs[st.session_state.last_len :]:
                            st.session_state.history.append((m["name"], m["content"]))
                        st.session_state.last_len = len(msgs)
                except Exception as e:
                    st.error(f"⚠️ Unexpected error during chat: {str(e)}")
                    st.session_state.history.append(("error", f"Unexpected error: {str(e)}"))

            st.rerun()

# Tab 2: Sequential Validation
with tab2:
    st.markdown("### 📋 Sequential Business Validation")
    st.markdown("Structured 7-phase validation process with specialized analysis at each stage.")

    # Sequential validation form
    with st.form("sequential_validation"):
        st.subheader("Business Information")

        col1, col2 = st.columns(2)
        with col1:
            business_name = st.text_input("Business Name")
            business_idea = st.text_area("Business Idea Description", height=100)
            industry = st.selectbox(
                "Industry",
                [
                    "SaaS",
                    "E-commerce",
                    "FinTech",
                    "HealthTech",
                    "EdTech",
                    "AI/ML",
                    "Marketplace",
                    "Consumer",
                    "Enterprise",
                    "Other",
                ],
            )

        with col2:
            target_market = st.text_input("Target Market")
            business_model = st.selectbox(
                "Business Model",
                [
                    "Subscription",
                    "Marketplace",
                    "E-commerce",
                    "Advertising",
                    "Freemium",
                    "Enterprise License",
                    "Transaction Fee",
                    "Other",
                ],
            )
            region = st.selectbox(
                "Primary Region", ["North America", "Europe", "Asia", "Global", "Other"]
            )

        submitted = st.form_submit_button("🚀 Run Sequential Validation")

        if submitted and business_idea:
            business_data = {
                "business_name": business_name or "Unnamed Venture",
                "business_idea": business_idea,
                "industry": industry,
                "target_market": target_market,
                "business_model": business_model.lower(),
                "region": region,
            }

            with st.spinner("Running comprehensive 7-phase validation..."):
                validation_results = run_sequential_validation(business_data)

            # Display results
            st.success("✅ Sequential validation completed!")

            # Phase results
            for phase, result in validation_results.items():
                with st.expander(
                    f"Phase {list(validation_results.keys()).index(phase) + 1}: {phase.value.replace('_', ' ').title()}",
                    expanded=result.success,
                ):
                    if result.success:
                        st.success(f"✅ Completed (Confidence: {result.confidence_score:.1%})")
                        st.write("**Analysis:**")
                        st.write(result.data.get("analysis", "Analysis completed"))

                        if result.recommendations:
                            st.write("**Recommendations:**")
                            for rec in result.recommendations:
                                st.write(f"• {rec}")
                    else:
                        st.error("❌ Phase failed")
                        st.write(result.data.get("error", "Unknown error"))

# Tab 3: Scenario Analysis
with tab3:
    st.markdown("### 🌪️ Swarm Scenario Analysis")
    st.markdown(
        "Multi-agent scenario planning to stress-test your business under different conditions."
    )

    with st.form("swarm_analysis"):
        st.subheader("Scenario Configuration")

        col1, col2 = st.columns(2)
        with col1:
            business_idea_swarm = st.text_area("Business Idea", height=80)
            industry_swarm = st.text_input("Industry")
            target_market_swarm = st.text_input("Target Market")

        with col2:
            # Scenario selection
            scenarios = st.multiselect(
                "Select Scenarios to Analyze",
                options=[s.value for s in ScenarioType],
                default=["optimistic", "realistic", "pessimistic", "competitive_threat"],
            )

        run_swarm = st.form_submit_button("🌊 Run Swarm Analysis")

        if run_swarm and business_idea_swarm:
            swarm_data = {
                "business_idea": business_idea_swarm,
                "industry": industry_swarm,
                "target_market": target_market_swarm,
            }

            with st.spinner(f"Running swarm analysis across {len(scenarios)} scenarios..."):
                swarm_results = run_swarm_analysis(swarm_data, scenarios)

            # Display synthesis
            st.success("🌊 Swarm analysis completed!")

            # Overall metrics
            metrics = swarm_results.get("overall_metrics", {})

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Scenarios Analyzed", metrics.get("scenarios_analyzed", 0))
            with col2:
                st.metric("Avg Impact Score", f"{metrics.get('average_impact_score', 0):.1f}/10")
            with col3:
                st.metric("High Probability Risks", metrics.get("high_probability_risks", 0))
            with col4:
                st.metric("High Impact Scenarios", metrics.get("high_impact_scenarios", 0))

            # Synthesis analysis
            st.subheader("Strategic Synthesis")
            st.write(swarm_results.get("synthesis_analysis", "Analysis completed"))

            # Individual scenarios
            st.subheader("Scenario Details")
            for scenario_type, result in swarm_results.get("scenario_results", {}).items():
                with st.expander(
                    f"{scenario_type.value.title()} Scenario (Impact: {result.impact_score:.1f}/10, Probability: {result.probability:.1%})"
                ):
                    st.write(result.analysis)

                    if result.mitigation_strategies:
                        st.write("**Mitigation Strategies:**")
                        for strategy in result.mitigation_strategies:
                            st.write(f"• {strategy}")

# Show chat history if not in special modes
if st.session_state.get("mode") == "chat" or not hasattr(st.session_state, "mode"):
    if len(st.session_state.history) == 0:
        render_history()
