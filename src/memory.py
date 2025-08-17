# src/memory.py
"""
Session memory: collect key facts/assumptions and expose a system-prompt block
that we prepend to each specialist agent. Compatible with AG2 0.9.7.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, cast

from anthropic import Anthropic
from anthropic.types import MessageParam

from .config import settings

# ---------- Minimal schema we keep ----------
DEFAULT_MEMORY: Dict[str, Any] = {
    "idea": "",
    "target_market": "",
    "customer": "",
    "region": "",
    "pricing_model": "",
    "key_constraints": [],
    "risks": [],
    "assumptions": [],
}


def memory_block(mem: Dict[str, Any]) -> str:
    """Render memory as a compact system-prompt block."""
    lines: List[str] = ["## Session Memory (facts & assumptions)"]

    def add(label, value):
        if isinstance(value, list):
            if value:
                lines.append(f"- {label}: " + "; ".join([str(v) for v in value]))
        else:
            if value:
                lines.append(f"- {label}: {value}")

    add("Idea", mem.get("idea"))
    add("Target market", mem.get("target_market"))
    add("Customer", mem.get("customer"))
    add("Region", mem.get("region"))
    add("Pricing model", mem.get("pricing_model"))
    add("Key constraints", mem.get("key_constraints", []))
    add("Risks", mem.get("risks", []))
    add("Assumptions", mem.get("assumptions", []))
    if len(lines) == 1:
        return ""  # empty memory → no extra prompt
    return "\n".join(lines)


# ---------- Persistence (optional) ----------


def load_memory(path: str) -> Dict[str, Any]:
    try:
        p = Path(path)
        if not p.exists():
            return DEFAULT_MEMORY.copy()
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_MEMORY.copy()


def save_memory(path: str, mem: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(mem, indent=2), encoding="utf-8")


# ---------- LLM-powered summarization ----------
PROMPT_JSON = (
    "From the conversation below, extract ONLY a compact JSON object with keys:\n"
    '{"idea": str, "target_market": str, "customer": str, "region": str, '
    '"pricing_model": str, "key_constraints": [str], "risks": [str], "assumptions": [str]}\n'
    "Keep lists short (<=5 items). No extra text."
)


def build_memory_from_messages(
    messages: List[Dict[str, str]], model: str | None = None
) -> Dict[str, Any]:
    """
    Ask Claude to distill the current chat into our memory schema.
    Uses the memory model (Haiku) by default for fast extraction.
    """
    client = Anthropic(api_key=settings.anthropic_key)
    model = model or settings.model_memory
    # Map our transcript to Anthropic format
    msgs = []
    for m in messages:
        role = "user" if m.get("name") == "human" else "assistant"
        msgs.append({"role": role, "content": m.get("content", "")})
    msgs.append({"role": "user", "content": PROMPT_JSON})

    # Use optimized settings for memory extraction
    resp = client.messages.create(
        model=model,
        max_tokens=settings.max_tokens_memory,
        temperature=settings.temperature_memory,
        top_p=settings.top_p,
        messages=cast(List[MessageParam], msgs),
    )
    content_block = resp.content[0]
    if hasattr(content_block, "text"):
        txt = content_block.text.strip()
    else:
        txt = str(content_block)
    try:
        data = json.loads(txt)
    except Exception:
        data = DEFAULT_MEMORY.copy()
        data["idea"] = txt[:400]
    # Normalize keys
    mem = DEFAULT_MEMORY.copy()
    mem.update({k: v for k, v in data.items() if k in mem})
    # Trim long fields
    for key in ["idea", "target_market", "customer", "region", "pricing_model"]:
        mem[key] = (mem.get(key) or "")[:300]
    for key in ["key_constraints", "risks", "assumptions"]:
        mem[key] = list((mem.get(key) or []))[:5]
    return mem
