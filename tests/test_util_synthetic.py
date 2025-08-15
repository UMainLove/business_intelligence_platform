"""
Synthetic tests for util.py without external dependencies.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.util import (
    estimate_tokens_chars,
    estimate_cost_usd,
    describe_pricing,
    _pick_prices,
    _resolve_prices_from_env_or_models,
    MODEL_PRICE_MAP,
    DEFAULT_SPLIT,
    BI_DEFAULT_SPLIT
)


class TestTokenEstimation:
    """Test token estimation functions."""

    def test_estimate_tokens_chars_empty(self):
        """Test token estimation with empty messages."""
        assert estimate_tokens_chars([]) == 0
        assert estimate_tokens_chars(None) == 0

    def test_estimate_tokens_chars_single_message(self):
        """Test token estimation with single message."""
        messages = [{"content": "Hello world"}]
        # "Hello world" = 11 chars, 11/4 = 2.75, rounded down to 2
        assert estimate_tokens_chars(messages) == 2

    def test_estimate_tokens_chars_multiple_messages(self):
        """Test token estimation with multiple messages."""
        messages = [
            {"content": "This is a test"},  # 14 chars
            {"content": "Another message"},  # 15 chars
            {"content": "Final one"}  # 9 chars
        ]
        # Total: 38 chars, 38/4 = 9.5, rounded down to 9
        assert estimate_tokens_chars(messages) == 9

    def test_estimate_tokens_chars_minimum_one(self):
        """Test that minimum token count is 1."""
        messages = [{"content": "Hi"}]  # 2 chars, 2/4 = 0.5
        assert estimate_tokens_chars(messages) == 1

    def test_estimate_tokens_chars_missing_content(self):
        """Test with messages missing content field."""
        messages = [
            {"role": "user"},  # No content
            {"content": "Test"},  # 4 chars
            {"other": "field"}  # No content
        ]
        assert estimate_tokens_chars(messages) == 1  # 4/4 = 1


class TestPricePicking:
    """Test price selection functions."""

    def test_pick_prices_known_model(self):
        """Test price picking for known models."""
        # Test Claude Sonnet 4
        price_in, price_out = _pick_prices("claude-sonnet-4-something")
        assert price_in == 0.003
        assert price_out == 0.015

        # Test Claude 3.7 Sonnet
        price_in, price_out = _pick_prices("claude-3-7-sonnet-xyz")
        assert price_in == 0.003
        assert price_out == 0.015

    def test_pick_prices_unknown_model(self):
        """Test price picking for unknown models."""
        # Should fall back to default Sonnet prices
        price_in, price_out = _pick_prices("gpt-4")
        assert price_in == 0.003
        assert price_out == 0.015

    def test_pick_prices_empty_model(self):
        """Test price picking with empty model name."""
        price_in, price_out = _pick_prices("")
        assert price_in == 0.003
        assert price_out == 0.015

        price_in, price_out = _pick_prices(None)
        assert price_in == 0.003
        assert price_out == 0.015

    def test_pick_prices_case_insensitive(self):
        """Test that model name matching is case insensitive."""
        price_in, price_out = _pick_prices("CLAUDE-SONNET-4")
        assert price_in == 0.003
        assert price_out == 0.015


class TestResolveEnvPrices:
    """Test environment-based price resolution."""

    @patch('src.util.settings')
    def test_resolve_prices_from_models(self, mock_settings):
        """Test price resolution from model names."""
        mock_settings.price_in_specialists = 0
        mock_settings.price_out_specialists = 0
        mock_settings.price_in_synth = 0
        mock_settings.price_out_synth = 0
        mock_settings.model_specialists = "claude-sonnet-4"
        mock_settings.model_synth = "claude-3-7-sonnet"

        prices = _resolve_prices_from_env_or_models()
        assert prices == (0.003, 0.015, 0.003, 0.015)

    @patch('src.util.settings')
    def test_resolve_prices_from_env_override(self, mock_settings):
        """Test price resolution with environment overrides."""
        mock_settings.price_in_specialists = 0.005
        mock_settings.price_out_specialists = 0.020
        mock_settings.price_in_synth = 0.004
        mock_settings.price_out_synth = 0.018
        mock_settings.model_specialists = "claude-sonnet-4"
        mock_settings.model_synth = "claude-3-7-sonnet"

        prices = _resolve_prices_from_env_or_models()
        assert prices == (0.005, 0.020, 0.004, 0.018)

    @patch('src.util.settings')
    def test_resolve_prices_partial_env_override(self, mock_settings):
        """Test price resolution with partial environment overrides."""
        mock_settings.price_in_specialists = 0.010  # Override
        mock_settings.price_out_specialists = 0  # Use model default
        mock_settings.price_in_synth = 0  # Use model default
        mock_settings.price_out_synth = 0.025  # Override
        mock_settings.model_specialists = "claude-sonnet-4"
        mock_settings.model_synth = "claude-3-7-sonnet"

        prices = _resolve_prices_from_env_or_models()
        assert prices == (0.010, 0.015, 0.003, 0.025)


class TestCostEstimation:
    """Test cost estimation functions."""

    def test_estimate_cost_zero_tokens(self):
        """Test cost estimation with zero tokens."""
        assert estimate_cost_usd(0) is None
        assert estimate_cost_usd(-10) is None

    def test_estimate_cost_default_bi_pricing(self):
        """Test cost estimation with default BI pricing."""
        # 1000 tokens with BI default split
        cost = estimate_cost_usd(1000, use_bi_pricing=True)
        assert cost is not None
        assert cost > 0
        
        # Verify the calculation
        # Input: 700 tokens (70%), Output specs: 200 (20%), Output synth: 50 (5%), Tool: 50 (5%)
        # Input split: 70% specialists (490), 30% synthesizer (210)
        # Cost = 490/1000 * 0.003 + 210/1000 * 0.003 + 200/1000 * 0.015 + 50/1000 * 0.015 + 50/1000 * 0.015
        expected = 0.49 * 0.003 + 0.21 * 0.003 + 0.2 * 0.015 + 0.05 * 0.015 + 0.05 * 0.015
        assert abs(cost - expected) < 0.0001

    def test_estimate_cost_legacy_pricing(self):
        """Test cost estimation with legacy pricing."""
        cost = estimate_cost_usd(1000, use_bi_pricing=False)
        assert cost is not None
        assert cost > 0
        
        # With legacy split: input 81%, output_specs 15%, output_synth 4%
        # Input split: 70% specialists (567), 30% synthesizer (243)
        # Cost = 567/1000 * 0.003 + 243/1000 * 0.003 + 150/1000 * 0.015 + 40/1000 * 0.015
        expected = 0.567 * 0.003 + 0.243 * 0.003 + 0.15 * 0.015 + 0.04 * 0.015
        assert abs(cost - expected) < 0.0001

    def test_estimate_cost_custom_prices(self):
        """Test cost estimation with custom prices."""
        cost = estimate_cost_usd(
            1000,
            price_in_specialists=0.010,
            price_out_specialists=0.050,
            price_in_synth=0.008,
            price_out_synth=0.040,
            use_bi_pricing=True
        )
        assert cost is not None
        # Higher prices should result in higher cost
        assert cost > estimate_cost_usd(1000, use_bi_pricing=True)

    def test_estimate_cost_custom_split(self):
        """Test cost estimation with custom token split."""
        custom_split = {
            "input": 0.5,
            "output_specs": 0.3,
            "output_synth": 0.2,
            "tool_overhead": 0.0
        }
        cost = estimate_cost_usd(1000, split=custom_split)
        assert cost is not None
        assert cost > 0

    def test_estimate_cost_large_tokens(self):
        """Test cost estimation with large token count."""
        # 1 million tokens
        cost = estimate_cost_usd(1_000_000, use_bi_pricing=True)
        assert cost is not None
        assert cost > 1.0  # Should be several dollars


class TestDescribePricing:
    """Test pricing description function."""

    @patch('src.util._resolve_prices_from_env_or_models')
    def test_describe_pricing_basic(self, mock_resolve):
        """Test basic pricing description."""
        mock_resolve.return_value = (0.003, 0.015, 0.003, 0.015)
        
        pricing = describe_pricing()
        
        assert isinstance(pricing, dict)
        assert "specialists_in_per_1k" in pricing
        assert "specialists_out_per_1k" in pricing
        assert "synth_in_per_1k" in pricing
        assert "synth_out_per_1k" in pricing
        assert pricing["specialists_in_per_1k"] == 0.003
        assert pricing["specialists_out_per_1k"] == 0.015

    @patch('src.util._resolve_prices_from_env_or_models')
    def test_describe_pricing_custom(self, mock_resolve):
        """Test pricing description with custom prices."""
        mock_resolve.return_value = (0.005, 0.025, 0.004, 0.020)
        
        pricing = describe_pricing()
        
        assert pricing["specialists_in_per_1k"] == 0.005
        assert pricing["specialists_out_per_1k"] == 0.025
        assert pricing["synth_in_per_1k"] == 0.004
        assert pricing["synth_out_per_1k"] == 0.020


class TestConstants:
    """Test module constants."""

    def test_default_split_sums_to_one(self):
        """Test that DEFAULT_SPLIT sums to 1.0."""
        assert abs(sum(DEFAULT_SPLIT.values()) - 1.0) < 1e-6

    def test_bi_default_split_sums_to_one(self):
        """Test that BI_DEFAULT_SPLIT sums to 1.0."""
        assert abs(sum(BI_DEFAULT_SPLIT.values()) - 1.0) < 1e-6

    def test_model_price_map_structure(self):
        """Test MODEL_PRICE_MAP structure."""
        assert isinstance(MODEL_PRICE_MAP, dict)
        for key, value in MODEL_PRICE_MAP.items():
            assert isinstance(key, str)
            assert isinstance(value, tuple)
            assert len(value) == 2
            assert all(isinstance(v, (int, float)) for v in value)
            assert all(v >= 0 for v in value)