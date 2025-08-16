import json
import time
from pathlib import Path

import streamlit as st

from src.chat import (
    build_group,
    clear_memory,
    get_memory,
    get_messages,
    reset_messages,
    run_synthesizer_json,
    set_memory,
    update_memory_from_chat,
)
from src.config import settings
from src.util import estimate_cost_usd, estimate_tokens_chars

st.set_page_config(page_title="Business-Idea Pre-Validator", page_icon="💬", layout="centered")
st.title("💬 Business-Idea Pre-Validator (Economist · Lawyer · Sociologist)")

# Initialize conversation state on first load
if "manager" not in st.session_state:
    manager, user_proxy, synthesizer = build_group()
    st.session_state.manager = manager
    st.session_state.user_proxy = user_proxy
    st.session_state.synthesizer = synthesizer
    st.session_state.history = []
    st.session_state.last_len = 0
if "session_name" not in st.session_state:
    st.session_state.session_name = f"session_{int(time.time())}"


def render_history():
    for role, msg in st.session_state.history:
        with st.chat_message(role):
            st.markdown(msg)


# Sidebar: actions & info
with st.sidebar:
    st.text_input("Session name", key="session_name")

    st.subheader("Session")
    if st.button("🔄 Reset conversation", use_container_width=True):
        reset_messages()
        st.session_state.history = []
        st.session_state.last_len = 0
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
    st.subheader("Export")
    if st.button("💾 Export transcript", use_container_width=True):
        messages = get_messages()
        Path("data/sessions").mkdir(parents=True, exist_ok=True)
        out = Path("data/sessions") / f"{st.session_state.session_name}_{int(time.time())}.json"
        out.write_text(json.dumps(messages, indent=2), encoding="utf-8")
        st.success(f"Saved: {out}")

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
    )

    # Show pricing info
    with st.expander("Pricing Details", expanded=False):
        st.caption(
            f"Specialists: ${settings.price_in_specialists}/1K in, ${settings.price_out_specialists}/1K out"
        )
        st.caption(
            f"Synthesizer: ${settings.price_in_synth}/1K in, ${settings.price_out_synth}/1K out"
        )
        st.caption("Heuristic: tokens ≈ chars/4")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Approx tokens", value=f"{approx_tokens:,}")
    with col2:
        if cost is not None:
            st.metric("Est. cost (USD)", value=f"${cost:,.4f}")

# Display current configuration info
with st.expander("ℹ️ Current Configuration", expanded=False):
    st.info(
        f"**Active Models:**\n"
        f"- Specialists: {settings.model_specialists.split('-')[-1]}\n"
        f"- Synthesizer: {settings.model_synth.split('-')[-1]}\n"
        f"- Memory: {settings.model_memory.split('-')[-1]}\n\n"
        f"**Performance:** Optimized with role-specific temperatures and token limits"
    )

# Chat input
prompt = st.chat_input("Describe your business idea… (type DONE for the final report)")
if prompt:
    # show user message immediately
    st.session_state.history.append(("human", prompt))
    render_history()

    if prompt.strip().upper() == "DONE":
        # Produce a structured final report (JSON → nice Markdown) and save .md
        report = run_synthesizer_json()
        md = (
            f"## Executive summary\n{report.get('executive_summary', '')}\n\n"
            f"## Economic viability\n{report.get('economic_viability', '')}\n\n"
            f"## Legal risks\n{report.get('legal_risks', '')}\n\n"
            f"## Social impact\n{report.get('social_impact', '')}\n\n"
            "## Next steps\n" + "\n".join(f"- {s}" for s in report.get("next_steps", []))
        )
        st.session_state.history.append(("synthesizer", md))
        render_history()

        # Save a Markdown export too
        Path("data/sessions").mkdir(parents=True, exist_ok=True)
        out_md = Path("data/sessions") / f"{st.session_state.session_name}_{int(time.time())}.md"
        out_md.write_text(md, encoding="utf-8")
        st.sidebar.success(f"Saved report: {out_md}")
    else:
        # run/continue the multi-agent conversation
        st.session_state.user_proxy.initiate_chat(
            recipient=st.session_state.manager,
            message=prompt,
        )

        # collect new agent messages and display
        msgs = get_messages()
        for m in msgs[st.session_state.last_len :]:
            st.session_state.history.append((m["name"], m["content"]))
        st.session_state.last_len = len(msgs)

        render_history()

# On first load, show any existing history
if not prompt:
    render_history()
