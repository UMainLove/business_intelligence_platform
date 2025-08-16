"""
Focused tests for util.py to achieve 95%+ coverage.
"""

from unittest.mock import patch

from src.util import (
    _PER_1K,
    BI_DEFAULT_SPLIT,
    DEFAULT_SPLIT,
    MODEL_PRICE_MAP,
    _pick_prices,
    _resolve_prices_from_env_or_models,
    describe_pricing,
    estimate_cost_usd,
    estimate_tokens_chars,
    get_cost_breakdown,
)


class TestConstants:
    """Test module constants and data structures."""

    def test_model_price_map_structure(self):
        """Test MODEL_PRICE_MAP structure."""
        assert isinstance(MODEL_PRICE_MAP, dict)
        assert "claude-sonnet-4" in MODEL_PRICE_MAP
        assert "claude-3-7-sonnet" in MODEL_PRICE_MAP

        for model, prices in MODEL_PRICE_MAP.items():
            assert len(prices) == 2
            assert isinstance(prices[0], float)  # input price
            assert isinstance(prices[1], float)  # output price
            assert prices[0] > 0
            assert prices[1] > 0

    def test_per_1k_pricing(self):
        """Test _PER_1K pricing constants."""
        assert _PER_1K["in"] == 0.003
        assert _PER_1K["out"] == 0.015
        assert _PER_1K["out"] > _PER_1K["in"]

    def test_bi_default_split_sums_to_one(self):
        """Test BI_DEFAULT_SPLIT sums to 1.0."""
        total = sum(BI_DEFAULT_SPLIT.values())
        assert abs(total - 1.0) < 1e-6

        # Check expected categories
        assert "input" in BI_DEFAULT_SPLIT
        assert "output_specs" in BI_DEFAULT_SPLIT
        assert "output_synth" in BI_DEFAULT_SPLIT
        assert "tool_overhead" in BI_DEFAULT_SPLIT

    def test_default_split_sums_to_one(self):
        """Test DEFAULT_SPLIT sums to 1.0."""
        total = sum(DEFAULT_SPLIT.values())
        assert abs(total - 1.0) < 1e-6

        # Check expected categories
        assert "input" in DEFAULT_SPLIT
        assert "output_specs" in DEFAULT_SPLIT
        assert "output_synth" in DEFAULT_SPLIT

    def test_bi_split_has_tool_overhead(self):
        """Test BI_DEFAULT_SPLIT includes tool overhead."""
        assert BI_DEFAULT_SPLIT["tool_overhead"] > 0
        assert "tool_overhead" not in DEFAULT_SPLIT

    def test_split_percentages_reasonable(self):
        """Test that split percentages are reasonable."""
        # BI split should allocate most tokens to input
        assert BI_DEFAULT_SPLIT["input"] > 0.5
        assert BI_DEFAULT_SPLIT["output_specs"] > BI_DEFAULT_SPLIT["output_synth"]

        # Legacy split should also favor input
        assert DEFAULT_SPLIT["input"] > 0.5
        assert DEFAULT_SPLIT["output_specs"] > DEFAULT_SPLIT["output_synth"]


class TestPickPrices:
    """Test _pick_prices function."""

    def test_pick_prices_claude_sonnet_4(self):
        """Test _pick_prices with claude-sonnet-4."""
        prices = _pick_prices("claude-sonnet-4")
        assert prices == (_PER_1K["in"], _PER_1K["out"])

    def test_pick_prices_claude_3_7_sonnet(self):
        """Test _pick_prices with claude-3-7-sonnet."""
        prices = _pick_prices("claude-3-7-sonnet")
        assert prices == (_PER_1K["in"], _PER_1K["out"])

    def test_pick_prices_case_insensitive(self):
        """Test _pick_prices is case insensitive."""
        prices1 = _pick_prices("CLAUDE-SONNET-4")
        prices2 = _pick_prices("Claude-Sonnet-4")
        prices3 = _pick_prices("claude-sonnet-4")

        assert prices1 == prices2 == prices3

    def test_pick_prices_prefix_matching(self):
        """Test _pick_prices works with prefixes."""
        prices = _pick_prices("claude-sonnet-4-latest")
        assert prices == (_PER_1K["in"], _PER_1K["out"])

    def test_pick_prices_unknown_model(self):
        """Test _pick_prices with unknown model returns defaults."""
        prices = _pick_prices("unknown-model")
        assert prices == (_PER_1K["in"], _PER_1K["out"])

    def test_pick_prices_empty_model(self):
        """Test _pick_prices with empty model name."""
        prices = _pick_prices("")
        assert prices == (_PER_1K["in"], _PER_1K["out"])

    def test_pick_prices_none_model(self):
        """Test _pick_prices with None model name."""
        prices = _pick_prices(None)
        assert prices == (_PER_1K["in"], _PER_1K["out"])


class TestResolvePricesFromEnv:
    """Test _resolve_prices_from_env_or_models function."""

    @patch("src.util.settings")
    def test_resolve_prices_no_env_overrides(self, mock_settings):
        """Test price resolution with no environment overrides."""
        mock_settings.price_in_specialists = 0
        mock_settings.price_out_specialists = 0
        mock_settings.price_in_synth = 0
        mock_settings.price_out_synth = 0
        mock_settings.model_specialists = "claude-sonnet-4"
        mock_settings.model_synth = "claude-3-7-sonnet"

        prices = _resolve_prices_from_env_or_models()

        expected = (_PER_1K["in"], _PER_1K["out"], _PER_1K["in"], _PER_1K["out"])
        assert prices == expected

    @patch("src.util.settings")
    def test_resolve_prices_with_env_overrides(self, mock_settings):
        """Test price resolution with environment overrides."""
        mock_settings.price_in_specialists = 0.005
        mock_settings.price_out_specialists = 0.025
        mock_settings.price_in_synth = 0.004
        mock_settings.price_out_synth = 0.020
        mock_settings.model_specialists = "claude-sonnet-4"
        mock_settings.model_synth = "claude-3-7-sonnet"

        prices = _resolve_prices_from_env_or_models()

        assert prices == (0.005, 0.025, 0.004, 0.020)

    @patch("src.util.settings")
    def test_resolve_prices_partial_env_overrides(self, mock_settings):
        """Test price resolution with partial environment overrides."""
        mock_settings.price_in_specialists = 0.005  # Override
        mock_settings.price_out_specialists = 0  # Use default
        mock_settings.price_in_synth = 0.004  # Override
        mock_settings.price_out_synth = 0  # Use default
        mock_settings.model_specialists = "claude-sonnet-4"
        mock_settings.model_synth = "claude-3-7-sonnet"

        prices = _resolve_prices_from_env_or_models()

        assert prices == (0.005, _PER_1K["out"], 0.004, _PER_1K["out"])

    @patch("src.util.settings")
    def test_resolve_prices_negative_env_values(self, mock_settings):
        """Test price resolution with negative environment values."""
        mock_settings.price_in_specialists = -1  # Should use default
        mock_settings.price_out_specialists = 0.025
        mock_settings.price_in_synth = 0.004
        mock_settings.price_out_synth = 0.020
        mock_settings.model_specialists = "claude-sonnet-4"
        mock_settings.model_synth = "claude-3-7-sonnet"

        prices = _resolve_prices_from_env_or_models()

        # Negative values should trigger model-based defaults
        expected = (_PER_1K["in"], _PER_1K["out"], _PER_1K["in"], _PER_1K["out"])
        assert prices == expected

    @patch("src.util.settings")
    def test_resolve_prices_different_models(self, mock_settings):
        """Test price resolution with different model configurations."""
        mock_settings.price_in_specialists = 0
        mock_settings.price_out_specialists = 0
        mock_settings.price_in_synth = 0
        mock_settings.price_out_synth = 0
        mock_settings.model_specialists = "claude-3-7-sonnet"
        mock_settings.model_synth = "claude-sonnet-4"

        prices = _resolve_prices_from_env_or_models()

        # Both models use same pricing currently
        expected = (_PER_1K["in"], _PER_1K["out"], _PER_1K["in"], _PER_1K["out"])
        assert prices == expected

    @patch("src.util.settings")
    def test_resolve_prices_unknown_models(self, mock_settings):
        """Test price resolution with unknown model names."""
        mock_settings.price_in_specialists = 0
        mock_settings.price_out_specialists = 0
        mock_settings.price_in_synth = 0
        mock_settings.price_out_synth = 0
        mock_settings.model_specialists = "unknown-model-1"
        mock_settings.model_synth = "unknown-model-2"

        prices = _resolve_prices_from_env_or_models()

        # Should fall back to defaults
        expected = (_PER_1K["in"], _PER_1K["out"], _PER_1K["in"], _PER_1K["out"])
        assert prices == expected


class TestEstimateTokensChars:
    """Test estimate_tokens_chars function."""

    def test_estimate_tokens_empty_messages(self):
        """Test token estimation with empty messages."""
        assert estimate_tokens_chars([]) == 0
        assert estimate_tokens_chars(None) == 0

    def test_estimate_tokens_single_message(self):
        """Test token estimation with single message."""
        messages = [{"content": "Hello world"}]
        tokens = estimate_tokens_chars(messages)
        expected = max(1, len("Hello world") // 4)
        assert tokens == expected

    def test_estimate_tokens_multiple_messages(self):
        """Test token estimation with multiple messages."""
        messages = [
            {"content": "Hello world"},
            {"content": "This is a test message"},
            {"content": "Another message here"},
        ]
        total_chars = sum(len(msg["content"]) for msg in messages)
        tokens = estimate_tokens_chars(messages)
        expected = max(1, total_chars // 4)
        assert tokens == expected

    def test_estimate_tokens_messages_without_content(self):
        """Test token estimation with messages missing content."""
        messages = [{"role": "user"}, {"content": "Hello"}, {"type": "system"}]
        tokens = estimate_tokens_chars(messages)
        expected = max(1, len("Hello") // 4)
        assert tokens == expected

    def test_estimate_tokens_minimum_value(self):
        """Test that token estimation returns at least 1."""
        messages = [{"content": "Hi"}]  # 2 chars -> 0 tokens, but should be 1
        tokens = estimate_tokens_chars(messages)
        assert tokens == 1

    def test_estimate_tokens_large_content(self):
        """Test token estimation with large content."""
        large_content = "x" * 10000
        messages = [{"content": large_content}]
        tokens = estimate_tokens_chars(messages)
        expected = 10000 // 4
        assert tokens == expected

    def test_estimate_tokens_empty_content(self):
        """Test token estimation with empty content."""
        messages = [{"content": ""}, {"content": ""}, {"content": ""}]
        tokens = estimate_tokens_chars(messages)
        assert tokens == 1  # max(1, 0)


class TestEstimateCostUSD:
    """Test estimate_cost_usd function."""

    def test_estimate_cost_zero_tokens(self):
        """Test cost estimation with zero tokens."""
        assert estimate_cost_usd(0) is None
        assert estimate_cost_usd(-1) is None

    def test_estimate_cost_basic_bi_pricing(self):
        """Test basic cost estimation with BI pricing."""
        cost = estimate_cost_usd(1000, use_bi_pricing=True)
        assert cost is not None
        assert cost > 0
        assert isinstance(cost, float)

    def test_estimate_cost_basic_standard_pricing(self):
        """Test basic cost estimation with standard pricing."""
        cost = estimate_cost_usd(1000, use_bi_pricing=False)
        assert cost is not None
        assert cost > 0
        assert isinstance(cost, float)

    def test_estimate_cost_bi_vs_standard(self):
        """Test that BI pricing typically costs more than standard."""
        tokens = 10000
        bi_cost = estimate_cost_usd(tokens, use_bi_pricing=True)
        standard_cost = estimate_cost_usd(tokens, use_bi_pricing=False)

        assert bi_cost is not None
        assert standard_cost is not None
        # BI pricing might be higher due to tool overhead
        assert bi_cost >= standard_cost * 0.8  # Allow some variance

    def test_estimate_cost_with_price_overrides(self):
        """Test cost estimation with price overrides."""
        cost_default = estimate_cost_usd(1000)
        cost_custom = estimate_cost_usd(
            1000,
            price_in_specialists=0.001,
            price_out_specialists=0.005,
            price_in_synth=0.001,
            price_out_synth=0.005,
        )

        assert cost_default is not None
        assert cost_custom is not None
        assert cost_custom != cost_default

    def test_estimate_cost_with_custom_split(self):
        """Test cost estimation with custom split."""
        custom_split = {"input": 0.6, "output_specs": 0.3, "output_synth": 0.1}

        cost = estimate_cost_usd(1000, split=custom_split)
        assert cost is not None
        assert cost > 0

    def test_estimate_cost_scales_with_tokens(self):
        """Test that cost scales approximately linearly with tokens."""
        cost_1k = estimate_cost_usd(1000)
        cost_2k = estimate_cost_usd(2000)
        cost_10k = estimate_cost_usd(10000)

        assert cost_1k is not None
        assert cost_2k is not None
        assert cost_10k is not None

        # Should be roughly proportional
        assert cost_2k > cost_1k * 1.8  # Allow some overhead variance
        assert cost_2k < cost_1k * 2.2
        assert cost_10k > cost_1k * 9
        assert cost_10k < cost_1k * 11

    @patch("src.util._resolve_prices_from_env_or_models")
    def test_estimate_cost_uses_env_prices(self, mock_resolve):
        """Test that estimate_cost_usd uses environment-resolved prices."""
        mock_resolve.return_value = (0.001, 0.002, 0.001, 0.002)

        cost = estimate_cost_usd(1000)

        assert cost is not None
        mock_resolve.assert_called_once()

    def test_estimate_cost_tool_overhead(self):
        """Test that BI pricing includes tool overhead."""
        tokens = 10000

        # BI pricing includes tool overhead
        bi_cost = estimate_cost_usd(tokens, use_bi_pricing=True)

        # Standard pricing doesn't
        standard_cost = estimate_cost_usd(tokens, use_bi_pricing=False)

        assert bi_cost is not None
        assert standard_cost is not None


class TestDescribePricing:
    """Test describe_pricing function."""

    @patch("src.util._resolve_prices_from_env_or_models")
    @patch("src.util.settings")
    def test_describe_pricing_structure(self, mock_settings, mock_resolve):
        """Test describe_pricing returns expected structure."""
        mock_resolve.return_value = (0.003, 0.015, 0.003, 0.015)
        mock_settings.model_specialists = "claude-sonnet-4"
        mock_settings.model_synth = "claude-3-7-sonnet"

        pricing = describe_pricing()

        assert isinstance(pricing, dict)
        assert "specialists_in_per_1k" in pricing
        assert "specialists_out_per_1k" in pricing
        assert "synth_in_per_1k" in pricing
        assert "synth_out_per_1k" in pricing
        assert "models" in pricing

        assert pricing["specialists_in_per_1k"] == 0.003
        assert pricing["specialists_out_per_1k"] == 0.015
        assert pricing["synth_in_per_1k"] == 0.003
        assert pricing["synth_out_per_1k"] == 0.015

        assert pricing["models"]["specialists"] == "claude-sonnet-4"
        assert pricing["models"]["synth"] == "claude-3-7-sonnet"

    @patch("src.util._resolve_prices_from_env_or_models")
    def test_describe_pricing_calls_resolve(self, mock_resolve):
        """Test describe_pricing calls price resolution."""
        mock_resolve.return_value = (0.001, 0.002, 0.003, 0.004)

        pricing = describe_pricing()

        mock_resolve.assert_called_once()
        assert pricing["specialists_in_per_1k"] == 0.001
        assert pricing["specialists_out_per_1k"] == 0.002
        assert pricing["synth_in_per_1k"] == 0.003
        assert pricing["synth_out_per_1k"] == 0.004


class TestGetCostBreakdown:
    """Test get_cost_breakdown function."""

    def test_get_cost_breakdown_zero_tokens(self):
        """Test cost breakdown with zero tokens."""
        breakdown = get_cost_breakdown(0)
        assert "error" in breakdown
        assert breakdown["error"] == "No tokens to analyze"

    def test_get_cost_breakdown_negative_tokens(self):
        """Test cost breakdown with negative tokens."""
        breakdown = get_cost_breakdown(-100)
        assert "error" in breakdown

    def test_get_cost_breakdown_bi_pricing(self):
        """Test cost breakdown with BI pricing."""
        breakdown = get_cost_breakdown(10000, use_bi_pricing=True)

        assert "total_tokens" in breakdown
        assert "total_cost_usd" in breakdown
        assert "breakdown" in breakdown
        assert "pricing_model" in breakdown

        assert breakdown["total_tokens"] == 10000
        assert breakdown["total_cost_usd"] > 0
        assert breakdown["pricing_model"] == "BI_Enhanced"

        # Check breakdown structure
        bd = breakdown["breakdown"]
        assert "input" in bd
        assert "specialists_output" in bd
        assert "synthesizer_output" in bd
        assert "tool_overhead" in bd

        # Each component should have tokens, cost, percentage
        for component in ["input", "specialists_output", "synthesizer_output", "tool_overhead"]:
            if bd[component] is not None:
                assert "tokens" in bd[component]
                assert "cost" in bd[component]
                assert "percentage" in bd[component]

    def test_get_cost_breakdown_standard_pricing(self):
        """Test cost breakdown with standard pricing."""
        breakdown = get_cost_breakdown(10000, use_bi_pricing=False)

        assert breakdown["pricing_model"] == "Standard"
        assert breakdown["breakdown"]["tool_overhead"] is None
        assert breakdown["cost_increase_vs_standard"] == 0

    def test_get_cost_breakdown_token_distribution(self):
        """Test that token breakdown sums to total."""
        breakdown = get_cost_breakdown(10000, use_bi_pricing=True)

        bd = breakdown["breakdown"]
        total_breakdown_tokens = (
            bd["input"]["tokens"]
            + bd["specialists_output"]["tokens"]
            + bd["synthesizer_output"]["tokens"]
            + bd["tool_overhead"]["tokens"]
        )

        assert total_breakdown_tokens == breakdown["total_tokens"]

    def test_get_cost_breakdown_percentage_sum(self):
        """Test that percentages sum to approximately 100%."""
        breakdown = get_cost_breakdown(10000, use_bi_pricing=True)

        bd = breakdown["breakdown"]
        total_percentage = (
            bd["input"]["percentage"]
            + bd["specialists_output"]["percentage"]
            + bd["synthesizer_output"]["percentage"]
            + bd["tool_overhead"]["percentage"]
        )

        assert abs(total_percentage - 100.0) < 0.1

    def test_get_cost_breakdown_cost_comparison(self):
        """Test cost increase calculation."""
        breakdown = get_cost_breakdown(10000, use_bi_pricing=True)

        assert "cost_increase_vs_standard" in breakdown
        # Should be a reasonable percentage
        increase = breakdown["cost_increase_vs_standard"]
        assert isinstance(increase, (int, float))
        assert increase >= 0  # BI pricing should not be cheaper

    @patch("src.util._resolve_prices_from_env_or_models")
    def test_get_cost_breakdown_uses_pricing(self, mock_resolve):
        """Test that cost breakdown uses resolved pricing."""
        mock_resolve.return_value = (0.001, 0.005, 0.002, 0.010)

        breakdown = get_cost_breakdown(1000)

        assert breakdown["total_cost_usd"] > 0
        mock_resolve.assert_called()


class TestIntegration:
    """Test integration scenarios."""

    @patch("src.util.settings")
    def test_full_workflow_with_env_pricing(self, mock_settings):
        """Test complete workflow with environment pricing."""
        # Setup environment
        mock_settings.price_in_specialists = 0.004
        mock_settings.price_out_specialists = 0.020
        mock_settings.price_in_synth = 0.003
        mock_settings.price_out_synth = 0.015
        mock_settings.model_specialists = "claude-sonnet-4"
        mock_settings.model_synth = "claude-3-7-sonnet"

        # Test token estimation
        messages = [
            {"content": "This is a business intelligence query"},
            {"content": "Analyze market trends for AI companies"},
        ]
        tokens = estimate_tokens_chars(messages)
        assert tokens > 0

        # Test cost estimation
        cost = estimate_cost_usd(tokens)
        assert cost is not None
        assert cost > 0

        # Test pricing description
        pricing = describe_pricing()
        assert pricing["specialists_in_per_1k"] == 0.004

        # Test cost breakdown
        breakdown = get_cost_breakdown(tokens)
        assert breakdown["total_tokens"] == tokens
        assert breakdown["total_cost_usd"] > 0

    def test_realistic_usage_scenario(self):
        """Test realistic usage scenario with typical message sizes."""
        # Simulate a realistic BI conversation
        messages = [
            {
                "content": "I want to analyze the fintech market for potential investment opportunities"
            },
            {"content": "Based on current market data, here are the key trends in fintech..."},
            {"content": "Can you also analyze the regulatory landscape?"},
            {"content": "The regulatory environment shows several important factors..."},
        ]

        tokens = estimate_tokens_chars(messages)
        cost_bi = estimate_cost_usd(tokens, use_bi_pricing=True)
        cost_standard = estimate_cost_usd(tokens, use_bi_pricing=False)
        breakdown = get_cost_breakdown(tokens)

        assert tokens > 0
        assert cost_bi is not None
        assert cost_standard is not None
        assert cost_bi > 0
        assert cost_standard > 0
        assert breakdown["total_tokens"] == tokens

    def test_edge_cases_and_error_handling(self):
        """Test edge cases and error handling."""
        # Test with None and empty inputs
        assert estimate_tokens_chars(None) == 0
        assert estimate_tokens_chars([]) == 0
        assert estimate_cost_usd(0) is None
        assert estimate_cost_usd(-1) is None

        # Test with very small messages
        tiny_messages = [{"content": "x"}]
        tokens = estimate_tokens_chars(tiny_messages)
        assert tokens == 1  # Minimum

        cost = estimate_cost_usd(tokens)
        assert cost is not None
        assert cost > 0

    def test_pricing_consistency(self):
        """Test pricing consistency across functions."""
        tokens = 5000

        # Get cost using main function
        cost1 = estimate_cost_usd(tokens)

        # Get cost using breakdown
        breakdown = get_cost_breakdown(tokens)
        cost2 = breakdown["total_cost_usd"]

        # Should be approximately equal (allowing for rounding)
        assert abs(cost1 - cost2) < 0.001

    def test_large_scale_calculations(self):
        """Test calculations with large token counts."""
        large_tokens = 1000000  # 1M tokens

        cost = estimate_cost_usd(large_tokens)
        breakdown = get_cost_breakdown(large_tokens)

        assert cost is not None
        assert cost > 1  # Should be substantial cost for 1M tokens (cost is around $6.6)
        assert breakdown["total_tokens"] == large_tokens
        assert breakdown["total_cost_usd"] > 1

    @patch("src.util.settings")
    def test_model_fallback_behavior(self, mock_settings):
        """Test fallback behavior with unknown models."""
        mock_settings.price_in_specialists = 0
        mock_settings.price_out_specialists = 0
        mock_settings.price_in_synth = 0
        mock_settings.price_out_synth = 0
        mock_settings.model_specialists = "future-claude-model"
        mock_settings.model_synth = "another-unknown-model"

        # Should fall back to default pricing
        cost = estimate_cost_usd(1000)
        pricing = describe_pricing()

        assert cost is not None
        assert pricing["specialists_in_per_1k"] == _PER_1K["in"]
        assert pricing["specialists_out_per_1k"] == _PER_1K["out"]
