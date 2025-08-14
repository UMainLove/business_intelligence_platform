# src/util.py
"""
Token & cost helpers for the agentic chat.

Defaults reflect Anthropic pricing (Aug 2025):
- Claude Sonnet 4 .......... $3 / 1M input, $15 / 1M output
- Claude Sonnet 3.7 Sonnet .. $3 / 1M input, $15 / 1M output

We expose two knobs:
1) Heuristic token estimator (chars/4)
2) Cost estimator using either:
- explicit PRICE_* values from .env (if set), or
- model-aware defaults for the two models above.

If you later change models or want precise usage, replace this with
SDK-provided token counts and per-call prices.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from .config import settings

# ---- Pricing (USD per 1K tokens) ---------------------------------------------

# Per 1K: $3 / 1M input -> 0.003  |  $15 / 1M output -> 0.015
_PER_1K = {"in": 0.003, "out": 0.015}

# Known model prefixes mapped to the same Sonnet pricing today.
# (Kept explicit so you can add different prices later if Anthropic changes them.)
MODEL_PRICE_MAP: Dict[str, Tuple[float, float]] = {
    "claude-sonnet-4": (_PER_1K["in"], _PER_1K["out"]),
    "claude-3-7-sonnet": (_PER_1K["in"], _PER_1K["out"]),
}


def _pick_prices(model_name: str) -> Tuple[float, float]:
    """Return (price_in_per_1k, price_out_per_1k) for a given Anthropic model name."""
    mn = (model_name or "").lower()
    for prefix, pair in MODEL_PRICE_MAP.items():
        if mn.startswith(prefix):
            return pair
    # Fallback: default to Sonnet rates if unknown
    return _PER_1K["in"], _PER_1K["out"]


def _resolve_prices_from_env_or_models() -> Tuple[float, float, float, float]:
    """
    Choose prices in this order:
    1) If .env PRICE_* values are > 0, use those.
    2) Else, infer from model names using MODEL_PRICE_MAP (Sonnet defaults).
    Returns: (price_in_specs, price_out_specs, price_in_synth, price_out_synth)
    """
    # Env overrides (0 or empty means "not set")
    pin_s = settings.price_in_specialists
    pout_s = settings.price_out_specialists
    pin_y = settings.price_in_synth
    pout_y = settings.price_out_synth

    have_env = any([pin_s, pout_s, pin_y, pout_y]) and all(
        x >= 0 for x in [pin_s, pout_s, pin_y, pout_y]
    )

    if have_env and (pin_s > 0 or pout_s > 0 or pin_y > 0 or pout_y > 0):
        # Use whatever is set; fall back to model defaults per field if any is 0
        def or_default(val: float, default: float) -> float:
            return default if (val is None or val <= 0) else val

        d_in_s, d_out_s = _pick_prices(settings.model_specialists)
        d_in_y, d_out_y = _pick_prices(settings.model_synth)
        return (
            or_default(pin_s, d_in_s),
            or_default(pout_s, d_out_s),
            or_default(pin_y, d_in_y),
            or_default(pout_y, d_out_y),
        )

    # No env overrides → use model-derived defaults
    in_s, out_s = _pick_prices(settings.model_specialists)
    in_y, out_y = _pick_prices(settings.model_synth)
    return in_s, out_s, in_y, out_y


# ---- Token estimation ---------------------------------------------------------


def estimate_tokens_chars(messages) -> int:
    """Very rough token estimate: characters / 4."""
    if not messages:
        return 0
    chars = sum(len(m.get("content", "")) for m in messages)
    return max(1, chars // 4)


# ---- Cost estimation ----------------------------------------------------------


# Enhanced split for Business Intelligence Platform with tool usage.
# BI platform uses significantly more tokens due to:
# - Tool integration and function calling
# - Multiple analysis workflows (sequential, swarm)
# - Enhanced agent prompts with tool descriptions
# - Document generation and comprehensive synthesis
BI_DEFAULT_SPLIT = {
    "input": 0.70,  # repeated transcript/context + tool results
    "output_specs": 0.20,  # enhanced specialists' replies with tool usage
    "output_synth": 0.05,  # comprehensive synthesis and document generation
    "tool_overhead": 0.05,  # additional tokens from tool integration
}
# Sanity: ensure it sums to 1.0
if abs(sum(BI_DEFAULT_SPLIT.values()) - 1.0) >= 1e-6:
    raise ValueError("BI_DEFAULT_SPLIT values must sum to 1.0")

# Legacy split for backward compatibility
DEFAULT_SPLIT = {
    "input": 0.81,  # repeated transcript/context fed to each specialist turn
    "output_specs": 0.15,  # specialists' combined replies
    "output_synth": 0.04,  # final one-shot report
}
if abs(sum(DEFAULT_SPLIT.values()) - 1.0) >= 1e-6:
    raise ValueError("DEFAULT_SPLIT values must sum to 1.0")


def estimate_cost_usd(
    approx_tokens: int,
    *,
    price_in_specialists: Optional[float] = None,  # USD per 1K tokens (override)
    price_out_specialists: Optional[float] = None,  # USD per 1K tokens (override)
    price_in_synth: Optional[float] = None,  # USD per 1K tokens (override)
    price_out_synth: Optional[float] = None,  # USD per 1K tokens (override)
    split: Optional[Dict[str, float]] = None,  # override token split
    use_bi_pricing: bool = True,  # use BI platform pricing model
) -> Optional[float]:
    """
    Enhanced cost estimate for Business Intelligence Platform.

    - approx_tokens: total tokens across the entire conversation (input+output)
    - use_bi_pricing: if True, uses enhanced BI split accounting for tool usage
    - If any price_* overrides are provided, they win; otherwise we pull defaults
    from the model names (Sonnet 4 & Sonnet 3.7 are both $0.003 in / $0.015 out per 1K).

    Returns None if approx_tokens <= 0.
    """
    if approx_tokens <= 0:
        return None

    # Prices: overrides > model-derived defaults
    in_s, out_s, in_y, out_y = _resolve_prices_from_env_or_models()

    if price_in_specialists is not None:
        in_s = price_in_specialists
    if price_out_specialists is not None:
        out_s = price_out_specialists
    if price_in_synth is not None:
        in_y = price_in_synth
    if price_out_synth is not None:
        out_y = price_out_synth

    # Choose appropriate split based on platform type
    if split is not None:
        sp = split
    elif use_bi_pricing:
        sp = BI_DEFAULT_SPLIT
    else:
        sp = DEFAULT_SPLIT

    total = float(approx_tokens)

    # Token buckets with enhanced BI accounting
    input_tokens = total * sp["input"]
    output_specs = total * sp["output_specs"]
    output_synth = total * sp["output_synth"]

    # Account for tool overhead in BI platform
    tool_overhead = total * sp.get("tool_overhead", 0)

    # Convert to cost using per-1K pricing
    cost = 0.0
    # Input tokens go to both specialists and synthesizer
    # Approximate split: 70% specialists, 30% synthesizer input
    specialist_input = input_tokens * 0.7
    synthesizer_input = input_tokens * 0.3
    cost += (specialist_input / 1000.0) * in_s
    cost += (synthesizer_input / 1000.0) * in_y
    cost += (output_specs / 1000.0) * out_s
    cost += (output_synth / 1000.0) * out_y

    # Add tool overhead cost (use specialist pricing as tools are called by specialists)
    if tool_overhead > 0:
        cost += (tool_overhead / 1000.0) * out_s

    return cost


def describe_pricing() -> Dict[str, float]:
    """
    Useful for debugging/telemetry in the UI sidebar.
    Returns a dict with the active per-1K prices.
    """
    in_s, out_s, in_y, out_y = _resolve_prices_from_env_or_models()
    return {
        "specialists_in_per_1k": in_s,
        "specialists_out_per_1k": out_s,
        "synth_in_per_1k": in_y,
        "synth_out_per_1k": out_y,
        "models": {
            "specialists": settings.model_specialists,
            "synth": settings.model_synth,
        },
    }


def get_cost_breakdown(approx_tokens: int, use_bi_pricing: bool = True) -> Dict[str, Any]:
    """
    Get detailed cost breakdown for Business Intelligence Platform.

    Returns breakdown of costs by component (input, output, tools).
    """
    if approx_tokens <= 0:
        return {"error": "No tokens to analyze"}

    # Get pricing
    in_s, out_s, in_y, out_y = _resolve_prices_from_env_or_models()

    # Get appropriate split
    sp = BI_DEFAULT_SPLIT if use_bi_pricing else DEFAULT_SPLIT
    total = float(approx_tokens)

    # Calculate token distribution
    input_tokens = total * sp["input"]
    output_specs = total * sp["output_specs"]
    output_synth = total * sp["output_synth"]
    tool_overhead = total * sp.get("tool_overhead", 0)

    # Calculate costs
    input_cost = (input_tokens / 1000.0) * in_s
    output_specs_cost = (output_specs / 1000.0) * out_s
    output_synth_cost = (output_synth / 1000.0) * out_y
    tool_cost = (tool_overhead / 1000.0) * out_s if tool_overhead > 0 else 0

    total_cost = input_cost + output_specs_cost + output_synth_cost + tool_cost

    return {
        "total_tokens": int(total),
        "total_cost_usd": total_cost,
        "breakdown": {
            "input": {
                "tokens": int(input_tokens),
                "cost": input_cost,
                "percentage": sp["input"] * 100,
            },
            "specialists_output": {
                "tokens": int(output_specs),
                "cost": output_specs_cost,
                "percentage": sp["output_specs"] * 100,
            },
            "synthesizer_output": {
                "tokens": int(output_synth),
                "cost": output_synth_cost,
                "percentage": sp["output_synth"] * 100,
            },
            "tool_overhead": (
                {
                    "tokens": int(tool_overhead),
                    "cost": tool_cost,
                    "percentage": sp.get("tool_overhead", 0) * 100,
                }
                if use_bi_pricing
                else None
            ),
        },
        "pricing_model": "BI_Enhanced" if use_bi_pricing else "Standard",
        "cost_increase_vs_standard": (
            (
                (total_cost / estimate_cost_usd(approx_tokens, use_bi_pricing=False) - 1) * 100
                if estimate_cost_usd(approx_tokens, use_bi_pricing=False)
                else 0
            )
            if use_bi_pricing
            else 0
        ),
    }
