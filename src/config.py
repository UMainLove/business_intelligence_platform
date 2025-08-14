import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

def _bool(env_value: str, default=False) -> bool:
    if env_value is None:
        return default
    return env_value.strip().lower() in {"1", "true", "yes", "on"}

def _int(env_value: str, default: int) -> int:
    if env_value is None or env_value == "":
        return default
    return int(env_value)

def _float(env_value: str, default: float) -> float:
    if env_value is None or env_value == "":
        return default
    return float(env_value)

@dataclass(frozen=True)
class Settings:
    anthropic_key: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Models
    model_specialists: str = os.getenv("ANTHROPIC_MODEL_SPECIALISTS", "claude-sonnet-4-20250514")
    model_synth: str = os.getenv("ANTHROPIC_MODEL_SYNTH", "claude-3-7-sonnet-20250219")
    model_memory: str = os.getenv("ANTHROPIC_MODEL_MEMORY", "claude-3-5-haiku-20241022")

    # Token limits
    max_tokens_specialists: int = _int(os.getenv("MAX_TOKENS_SPECIALISTS"), 1500)
    max_tokens_synth: int = _int(os.getenv("MAX_TOKENS_SYNTH"), 2500)
    max_tokens_memory: int = _int(os.getenv("MAX_TOKENS_MEMORY"), 800)

    # Temperature settings (role-specific)
    temperature_economist: float = _float(os.getenv("TEMPERATURE_ECONOMIST"), 0.2)
    temperature_lawyer: float = _float(os.getenv("TEMPERATURE_LAWYER"), 0.1)
    temperature_sociologist: float = _float(os.getenv("TEMPERATURE_SOCIOLOGIST"), 0.4)
    temperature_synth: float = _float(os.getenv("TEMPERATURE_SYNTH"), 0.15)
    temperature_memory: float = _float(os.getenv("TEMPERATURE_MEMORY"), 0.1)

    # Advanced sampling parameters
    top_p: float = _float(os.getenv("TOP_P"), 0.95)
    top_k: int = _int(os.getenv("TOP_K"), 40)

    # Thinking mode
    thinking_enabled: bool = _bool(os.getenv("THINKING_ENABLED", "false"))
    thinking_budget_tokens: int = _int(os.getenv("THINKING_BUDGET_TOKENS"), 2048)

    # Optional pricing (USD per 1K tokens) for rough cost estimate
    price_in_specialists: float = _float(os.getenv("PRICE_IN_SPECIALISTS"), 0.003)
    price_out_specialists: float = _float(os.getenv("PRICE_OUT_SPECIALISTS"), 0.015)
    price_in_synth: float = _float(os.getenv("PRICE_IN_SYNTH"), 0.003)
    price_out_synth: float = _float(os.getenv("PRICE_OUT_SYNTH"), 0.015)

settings = Settings()