# src/chat.py
import json
from typing import Any, Dict, List, Optional, Tuple

from autogen import ConversableAgent, GroupChat, GroupChatManager, LLMConfig

from .config import settings
from .memory import build_memory_from_messages, load_memory, memory_block, save_memory
from .roles import (
    economist_prompt,
    lawyer_prompt,
    sociologist_prompt,
    synthesizer_prompt,
)

# Singletons cached for the Streamlit session
_manager = None
_user_proxy = None
_synthesizer = None

# Session memory (in-memory copy + path for persistence)
_memory_dict = None
_MEMORY_PATH = "data/sessions/session_memory.json"


def _anthropic_cfg(
    model: str,
    temperature: float,
    max_tokens: int = 2048,
    top_p: Optional[float] = None,
) -> LLMConfig:
    """Enhanced LLMConfig for Anthropic with advanced parameters."""
    config = {
        "api_type": "anthropic",
        "model": model,
        "api_key": settings.anthropic_key,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    # Add optional parameters if provided
    if top_p is not None:
        config["top_p"] = top_p

    # Add top_k if not disabled
    if settings.top_k > 0:
        config["top_k"] = settings.top_k

    # Add thinking mode support for Opus models if enabled
    if "opus" in model.lower() and settings.thinking_enabled:
        config["thinking_budget_tokens"] = settings.thinking_budget_tokens

    return LLMConfig(**config)


def _compose_system(base: str) -> str:
    """Compose system prompt with base role prompt and optional session memory block."""
    mem_txt = memory_block(_memory_dict or {})
    return base if not mem_txt else f"{base}\n\n{mem_txt}"


def _construct_group_from_memory() -> Tuple[GroupChatManager, ConversableAgent, ConversableAgent]:
    """
    (Re)construct agents & manager using current _memory_dict with role-specific configurations.
    """
    # Role-specific LLM configurations
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

    with llm_economist:
        economist = ConversableAgent(
            name="economist",
            system_message=_compose_system(economist_prompt()),
        )
    with llm_lawyer:
        lawyer = ConversableAgent(name="lawyer", system_message=_compose_system(lawyer_prompt()))
    with llm_sociologist:
        sociologist = ConversableAgent(
            name="sociologist",
            system_message=_compose_system(sociologist_prompt()),
        )

    # One-shot synthesizer (not part of the group rotation)
    with llm_synth:
        synthesizer = ConversableAgent(name="synthesizer", system_message=synthesizer_prompt())

    # Human proxy
    user_proxy = ConversableAgent(
        name="human",
        system_message="You are the entrepreneur. Type DONE when you want the final report.",
        human_input_mode="ALWAYS",
    )

    chat = GroupChat(
        agents=[user_proxy, economist, lawyer, sociologist],
        speaker_selection_method="auto",
        max_round=6,  # guardrail since DONE is handled in the UI
    )

    # Use economist config for manager (balanced temperature)
    manager = GroupChatManager(
        name="orchestrator",
        groupchat=chat,
        llm_config=llm_economist,
    )
    return manager, user_proxy, synthesizer


def _rebuild_group(
    *, preserve_messages: bool = True
) -> Tuple[GroupChatManager, ConversableAgent, ConversableAgent]:
    """Rebuild agents with the latest memory; optionally keep the transcript."""
    global _manager, _user_proxy, _synthesizer
    prev = []
    if preserve_messages and _manager is not None:
        prev = list(_manager.groupchat.messages)

    manager, user_proxy, synthesizer = _construct_group_from_memory()
    if prev:
        manager.groupchat.messages.extend(prev)

    _manager, _user_proxy, _synthesizer = manager, user_proxy, synthesizer
    return _manager, _user_proxy, _synthesizer


def build_group() -> Tuple[GroupChatManager, ConversableAgent, ConversableAgent]:
    """Build (or return cached) agents + group chat manager."""
    global _manager, _user_proxy, _synthesizer, _memory_dict
    if _manager is not None:
        return _manager, _user_proxy, _synthesizer

    # initial load of persisted memory
    _memory_dict = load_memory(_MEMORY_PATH)
    _manager, _user_proxy, _synthesizer = _rebuild_group(preserve_messages=False)
    return _manager, _user_proxy, _synthesizer


# ---------- Memory controls exposed to UI ----------


def get_memory() -> dict:
    global _memory_dict
    if _memory_dict is None:
        _memory_dict = {}
        _ = build_group()
    return _memory_dict or {}


def set_memory(mem: dict) -> Tuple[GroupChatManager, ConversableAgent, ConversableAgent]:
    """Replace memory dict, persist it, and rebuild agents to apply prompts."""
    global _memory_dict
    _memory_dict = mem or {}
    save_memory(_MEMORY_PATH, _memory_dict)
    return _rebuild_group(preserve_messages=True)


def clear_memory() -> Tuple[GroupChatManager, ConversableAgent, ConversableAgent]:
    """Clear memory and rebuild agents (keeps the chat transcript)."""
    return set_memory({})


def update_memory_from_chat() -> dict:
    """Summarize current transcript into memory schema and set it."""
    m, _, _ = build_group()
    mem = build_memory_from_messages(m.groupchat.messages)
    set_memory(mem)
    return mem


# ---------- Synth run & transcript helpers ----------


def run_synthesizer() -> str:
    m, _, synthesizer = build_group()
    reply = synthesizer.generate_reply(messages=m.groupchat.messages)
    m.groupchat.messages.append({"name": "synthesizer", "content": reply})
    return reply


def run_synthesizer_json() -> dict:
    """Ask synthesizer for JSON report; store raw reply; return parsed dict (best-effort)."""
    m, _, synthesizer = build_group()
    raw = synthesizer.generate_reply(messages=m.groupchat.messages)
    m.groupchat.messages.append({"name": "synthesizer", "content": raw})
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError, ValueError):
        return {
            "executive_summary": raw[:800],
            "economic_viability": "",
            "legal_risks": "",
            "social_impact": "",
            "next_steps": [],
        }


def get_messages() -> List[Dict[str, Any]]:
    m, _, _ = build_group()
    return m.groupchat.messages


def reset_messages() -> None:
    m, _, _ = build_group()
    m.groupchat.messages.clear()
