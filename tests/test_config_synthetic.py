"""
Synthetic tests for config.py without external dependencies.
"""

import os
from unittest.mock import patch

import pytest

from src.config import Settings, _bool, _float, _int, settings


class TestBoolConverter:
    """Test _bool conversion function."""

    def test_bool_true_values(self):
        """Test that various true values are correctly converted."""
        assert _bool("1") is True
        assert _bool("true") is True
        assert _bool("True") is True
        assert _bool("TRUE") is True
        assert _bool("yes") is True
        assert _bool("YES") is True
        assert _bool("on") is True
        assert _bool("ON") is True
        assert _bool("  true  ") is True  # With whitespace

    def test_bool_false_values(self):
        """Test that various false values are correctly converted."""
        assert _bool("0") is False
        assert _bool("false") is False
        assert _bool("False") is False
        assert _bool("no") is False
        assert _bool("off") is False
        assert _bool("") is False
        assert _bool("random") is False

    def test_bool_none_default(self):
        """Test that None returns default value."""
        assert _bool(None) is False  # Default false
        assert _bool(None, True) is True  # Custom default
        assert _bool(None, False) is False  # Custom default


class TestIntConverter:
    """Test _int conversion function."""

    def test_int_valid_values(self):
        """Test that valid integers are converted."""
        assert _int("42", 0) == 42
        assert _int("0", 100) == 0
        assert _int("-10", 50) == -10
        assert _int("1000000", 1) == 1000000

    def test_int_none_empty_default(self):
        """Test that None and empty string return default."""
        assert _int(None, 100) == 100
        assert _int("", 200) == 200
        assert _int(None, 0) == 0


class TestFloatConverter:
    """Test _float conversion function."""

    def test_float_valid_values(self):
        """Test that valid floats are converted."""
        assert _float("3.14", 0.0) == 3.14
        assert _float("0.0", 1.0) == 0.0
        assert _float("-2.5", 5.0) == -2.5
        assert _float("1e-3", 0.5) == 0.001

    def test_float_none_empty_default(self):
        """Test that None and empty string return default."""
        assert _float(None, 1.5) == 1.5
        assert _float("", 2.5) == 2.5
        assert _float(None, 0.0) == 0.0


class TestSettings:
    """Test Settings dataclass."""

    def test_settings_instance_exists(self):
        """Test that settings instance is created."""
        assert settings is not None
        assert isinstance(settings, Settings)

    def test_settings_frozen(self):
        """Test that Settings is frozen (immutable)."""
        with pytest.raises(AttributeError):
            settings.anthropic_key = "new_key"

    @patch.dict(
        os.environ,
        {
            "ANTHROPIC_API_KEY": "test-key-123",
            "ANTHROPIC_MODEL_SPECIALISTS": "custom-model-1",
            "MAX_TOKENS_SPECIALISTS": "2000",
            "TEMPERATURE_ECONOMIST": "0.5",
            "THINKING_ENABLED": "true",
            "PRICE_IN_SPECIALISTS": "0.005",
        },
    )
    def test_settings_from_env(self):
        """Test that Settings reads from environment variables."""
        # Need to reimport to get new settings with patched env
        from importlib import reload

        import src.config as config_module

        reload(config_module)

        test_settings = config_module.Settings()

        assert test_settings.anthropic_key == "test-key-123"
        assert test_settings.model_specialists == "custom-model-1"
        assert test_settings.max_tokens_specialists == 2000
        assert test_settings.temperature_economist == 0.5
        assert test_settings.thinking_enabled is True
        assert test_settings.price_in_specialists == 0.005

    def test_settings_defaults(self):
        """Test that Settings has sensible defaults."""
        test_settings = Settings()

        # Check model defaults
        assert "claude" in test_settings.model_specialists.lower()
        assert "claude" in test_settings.model_synth.lower()
        assert "claude" in test_settings.model_memory.lower()

        # Check token limits are reasonable
        assert 500 <= test_settings.max_tokens_specialists <= 5000
        assert 500 <= test_settings.max_tokens_synth <= 5000
        assert 500 <= test_settings.max_tokens_memory <= 2000

        # Check temperatures are in valid range
        assert 0.0 <= test_settings.temperature_economist <= 1.0
        assert 0.0 <= test_settings.temperature_lawyer <= 1.0
        assert 0.0 <= test_settings.temperature_sociologist <= 1.0
        assert 0.0 <= test_settings.temperature_synth <= 1.0
        assert 0.0 <= test_settings.temperature_memory <= 1.0

        # Check sampling parameters
        assert 0.0 < test_settings.top_p <= 1.0
        assert test_settings.top_k > 0

        # Check pricing is positive
        assert test_settings.price_in_specialists > 0
        assert test_settings.price_out_specialists > 0
        assert test_settings.price_in_synth > 0
        assert test_settings.price_out_synth > 0

    def test_settings_all_attributes(self):
        """Test that Settings has all expected attributes."""
        expected_attrs = [
            "anthropic_key",
            "model_specialists",
            "model_synth",
            "model_memory",
            "max_tokens_specialists",
            "max_tokens_synth",
            "max_tokens_memory",
            "temperature_economist",
            "temperature_lawyer",
            "temperature_sociologist",
            "temperature_synth",
            "temperature_memory",
            "top_p",
            "top_k",
            "thinking_enabled",
            "thinking_budget_tokens",
            "price_in_specialists",
            "price_out_specialists",
            "price_in_synth",
            "price_out_synth",
        ]

        for attr in expected_attrs:
            assert hasattr(settings, attr), f"Settings missing attribute: {attr}"
