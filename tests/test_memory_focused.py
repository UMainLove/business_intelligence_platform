"""
Focused tests for memory.py to achieve 95%+ coverage.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.memory import (
    DEFAULT_MEMORY,
    PROMPT_JSON,
    build_memory_from_messages,
    load_memory,
    memory_block,
    save_memory,
)


class TestDefaultMemory:
    """Test DEFAULT_MEMORY constant."""

    def test_default_memory_structure(self):
        """Test DEFAULT_MEMORY has expected structure."""
        assert isinstance(DEFAULT_MEMORY, dict)

        expected_keys = [
            "idea",
            "target_market",
            "customer",
            "region",
            "pricing_model",
            "key_constraints",
            "risks",
            "assumptions",
        ]

        for key in expected_keys:
            assert key in DEFAULT_MEMORY

        # Check types
        assert isinstance(DEFAULT_MEMORY["idea"], str)
        assert isinstance(DEFAULT_MEMORY["target_market"], str)
        assert isinstance(DEFAULT_MEMORY["customer"], str)
        assert isinstance(DEFAULT_MEMORY["region"], str)
        assert isinstance(DEFAULT_MEMORY["pricing_model"], str)
        assert isinstance(DEFAULT_MEMORY["key_constraints"], list)
        assert isinstance(DEFAULT_MEMORY["risks"], list)
        assert isinstance(DEFAULT_MEMORY["assumptions"], list)

    def test_default_memory_values(self):
        """Test DEFAULT_MEMORY has expected default values."""
        assert DEFAULT_MEMORY["idea"] == ""
        assert DEFAULT_MEMORY["target_market"] == ""
        assert DEFAULT_MEMORY["customer"] == ""
        assert DEFAULT_MEMORY["region"] == ""
        assert DEFAULT_MEMORY["pricing_model"] == ""
        assert DEFAULT_MEMORY["key_constraints"] == []
        assert DEFAULT_MEMORY["risks"] == []
        assert DEFAULT_MEMORY["assumptions"] == []


class TestMemoryBlock:
    """Test memory_block function."""

    def test_memory_block_empty_memory(self):
        """Test memory_block with empty memory."""
        empty_mem = {}
        result = memory_block(empty_mem)
        assert result == ""

    def test_memory_block_default_memory(self):
        """Test memory_block with DEFAULT_MEMORY."""
        result = memory_block(DEFAULT_MEMORY)
        assert result == ""  # All empty values should result in empty block

    def test_memory_block_partial_data(self):
        """Test memory_block with partial data."""
        mem = {
            "idea": "AI SaaS Platform",
            "target_market": "Enterprise B2B",
            "customer": "",  # Empty, should be skipped
            "region": "North America",
        }

        result = memory_block(mem)

        assert "## Session Memory (facts & assumptions)" in result
        assert "- Idea: AI SaaS Platform" in result
        assert "- Target market: Enterprise B2B" in result
        assert "- Region: North America" in result
        assert "Customer" not in result  # Empty value should be skipped

    def test_memory_block_full_data(self):
        """Test memory_block with complete data."""
        mem = {
            "idea": "FinTech Startup",
            "target_market": "SMB",
            "customer": "Small businesses",
            "region": "Europe",
            "pricing_model": "Subscription",
            "key_constraints": ["Regulatory compliance", "Security requirements"],
            "risks": ["Market competition", "Technical challenges"],
            "assumptions": ["Strong demand", "Skilled team available"],
        }

        result = memory_block(mem)

        assert "## Session Memory (facts & assumptions)" in result
        assert "- Idea: FinTech Startup" in result
        assert "- Target market: SMB" in result
        assert "- Customer: Small businesses" in result
        assert "- Region: Europe" in result
        assert "- Pricing model: Subscription" in result
        assert "- Key constraints: Regulatory compliance; Security requirements" in result
        assert "- Risks: Market competition; Technical challenges" in result
        assert "- Assumptions: Strong demand; Skilled team available" in result

    def test_memory_block_list_formatting(self):
        """Test memory_block formats lists correctly."""
        mem = {
            "risks": ["Risk 1", "Risk 2", "Risk 3"],
            "assumptions": ["Assumption A"],
            "key_constraints": [],  # Empty list should be skipped
        }

        result = memory_block(mem)

        assert "- Risks: Risk 1; Risk 2; Risk 3" in result
        assert "- Assumptions: Assumption A" in result
        assert "Key constraints" not in result

    def test_memory_block_mixed_types_in_lists(self):
        """Test memory_block handles mixed types in lists."""
        mem = {"risks": ["String risk", 123, None, True], "assumptions": [1, 2, 3]}

        result = memory_block(mem)

        assert "- Risks: String risk; 123; None; True" in result
        assert "- Assumptions: 1; 2; 3" in result

    def test_memory_block_none_values(self):
        """Test memory_block handles None values."""
        mem = {"idea": None, "target_market": "Test Market", "risks": None}

        result = memory_block(mem)

        assert "- Target market: Test Market" in result
        assert "Idea" not in result
        assert "Risks" not in result

    def test_memory_block_get_with_defaults(self):
        """Test memory_block uses get() with defaults."""
        mem = {
            "idea": "Test Idea"
            # Missing other keys
        }

        result = memory_block(mem)

        assert "- Idea: Test Idea" in result
        # Should not crash on missing keys


class TestLoadMemory:
    """Test load_memory function."""

    def test_load_memory_nonexistent_file(self):
        """Test load_memory with nonexistent file."""
        result = load_memory("/nonexistent/path/memory.json")
        assert result == DEFAULT_MEMORY

    def test_load_memory_valid_file(self):
        """Test load_memory with valid JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            test_memory = {
                "idea": "Test Startup",
                "target_market": "B2B",
                "risks": ["Risk 1", "Risk 2"],
            }
            json.dump(test_memory, f)
            temp_path = f.name

        try:
            result = load_memory(temp_path)
            assert result["idea"] == "Test Startup"
            assert result["target_market"] == "B2B"
            assert result["risks"] == ["Risk 1", "Risk 2"]
        finally:
            Path(temp_path).unlink()

    def test_load_memory_invalid_json(self):
        """Test load_memory with invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content {")
            temp_path = f.name

        try:
            result = load_memory(temp_path)
            assert result == DEFAULT_MEMORY
        finally:
            Path(temp_path).unlink()

    def test_load_memory_empty_file(self):
        """Test load_memory with empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            result = load_memory(temp_path)
            assert result == DEFAULT_MEMORY
        finally:
            Path(temp_path).unlink()

    def test_load_memory_non_json_file(self):
        """Test load_memory with non-JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is not JSON")
            temp_path = f.name

        try:
            result = load_memory(temp_path)
            assert result == DEFAULT_MEMORY
        finally:
            Path(temp_path).unlink()

    def test_load_memory_permission_error(self):
        """Test load_memory handles permission errors gracefully."""
        # Use a path that might cause permission issues
        result = load_memory("/root/inaccessible/memory.json")
        assert result == DEFAULT_MEMORY


class TestSaveMemory:
    """Test save_memory function."""

    def test_save_memory_basic(self):
        """Test basic save_memory functionality."""
        test_memory = {
            "idea": "Test Idea",
            "target_market": "Test Market",
            "risks": ["Risk 1", "Risk 2"],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "memory.json"

            save_memory(str(temp_path), test_memory)

            assert temp_path.exists()
            loaded_data = json.loads(temp_path.read_text())
            assert loaded_data == test_memory

    def test_save_memory_creates_directories(self):
        """Test save_memory creates parent directories."""
        test_memory = {"idea": "Test"}

        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = Path(temp_dir) / "nested" / "dir" / "memory.json"

            save_memory(str(nested_path), test_memory)

            assert nested_path.exists()
            assert nested_path.parent.exists()
            loaded_data = json.loads(nested_path.read_text())
            assert loaded_data == test_memory

    def test_save_memory_overwrites_existing(self):
        """Test save_memory overwrites existing file."""
        old_memory = {"idea": "Old Idea"}
        new_memory = {"idea": "New Idea"}

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "memory.json"

            # Save old memory
            save_memory(str(temp_path), old_memory)
            assert json.loads(temp_path.read_text())["idea"] == "Old Idea"

            # Save new memory
            save_memory(str(temp_path), new_memory)
            assert json.loads(temp_path.read_text())["idea"] == "New Idea"

    def test_save_memory_complex_data(self):
        """Test save_memory with complex data structures."""
        complex_memory = {
            "idea": "Complex Startup",
            "target_market": "Enterprise",
            "key_constraints": ["Constraint 1", "Constraint 2"],
            "risks": ["Financial risk", "Market risk"],
            "assumptions": ["Growth assumption"],
            "nested": {"level1": {"level2": "value"}},  # Not in DEFAULT_MEMORY
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "complex_memory.json"

            save_memory(str(temp_path), complex_memory)

            loaded_data = json.loads(temp_path.read_text())
            assert loaded_data == complex_memory

    def test_save_memory_encoding(self):
        """Test save_memory handles UTF-8 encoding correctly."""
        unicode_memory = {
            "idea": "Café Management System",
            "customer": "Customers with émojis 🚀",
            "region": "München, Deutschland",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "unicode_memory.json"

            save_memory(str(temp_path), unicode_memory)

            loaded_data = json.loads(temp_path.read_text(encoding="utf-8"))
            assert loaded_data == unicode_memory


class TestBuildMemoryFromMessages:
    """Test build_memory_from_messages function."""

    @patch("src.memory.Anthropic")
    @patch("src.memory.settings")
    def test_build_memory_success(self, mock_settings, mock_anthropic_class):
        """Test successful memory building from messages."""
        # Setup mocks
        mock_settings.anthropic_key = "test-key"
        mock_settings.model_memory = "claude-3-haiku"
        mock_settings.max_tokens_memory = 1024
        mock_settings.temperature_memory = 0.3
        mock_settings.top_p = 0.9

        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [
            Mock(text='{"idea": "AI Platform", "target_market": "B2B", "risks": ["Competition"]}')
        ]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        messages = [
            {"name": "human", "content": "I want to build an AI platform"},
            {"name": "assistant", "content": "That's a great idea for the B2B market"},
        ]

        result = build_memory_from_messages(messages)

        assert result["idea"] == "AI Platform"
        assert result["target_market"] == "B2B"
        assert result["risks"] == ["Competition"]

        # Verify API call
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-3-haiku"
        assert call_kwargs["max_tokens"] == 1024
        assert call_kwargs["temperature"] == 0.3
        assert call_kwargs["top_p"] == 0.9

    @patch("src.memory.Anthropic")
    @patch("src.memory.settings")
    def test_build_memory_message_formatting(self, mock_settings, mock_anthropic_class):
        """Test message formatting for Anthropic API."""
        mock_settings.anthropic_key = "test-key"
        mock_settings.model_memory = "claude-3-haiku"
        mock_settings.max_tokens_memory = 1024
        mock_settings.temperature_memory = 0.3
        mock_settings.top_p = 0.9

        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="{}")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        messages = [
            {"name": "human", "content": "Human message"},
            {"name": "assistant", "content": "Assistant response"},
            {"name": "other", "content": "Other message"},  # Should be treated as assistant
        ]

        build_memory_from_messages(messages)

        # Check formatted messages
        call_kwargs = mock_client.messages.create.call_args[1]
        formatted_messages = call_kwargs["messages"]

        assert len(formatted_messages) == 4  # 3 original + 1 prompt
        assert formatted_messages[0]["role"] == "user"
        assert formatted_messages[0]["content"] == "Human message"
        assert formatted_messages[1]["role"] == "assistant"
        assert formatted_messages[1]["content"] == "Assistant response"
        assert formatted_messages[2]["role"] == "assistant"  # "other" -> assistant
        assert formatted_messages[2]["content"] == "Other message"
        assert formatted_messages[3]["role"] == "user"
        assert PROMPT_JSON in formatted_messages[3]["content"]

    @patch("src.memory.Anthropic")
    @patch("src.memory.settings")
    def test_build_memory_invalid_json_response(self, mock_settings, mock_anthropic_class):
        """Test handling invalid JSON response."""
        mock_settings.anthropic_key = "test-key"
        mock_settings.model_memory = "claude-3-haiku"
        mock_settings.max_tokens_memory = 1024
        mock_settings.temperature_memory = 0.3
        mock_settings.top_p = 0.9

        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="invalid json response")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        messages = [{"name": "human", "content": "Test message"}]

        result = build_memory_from_messages(messages)

        # Should return DEFAULT_MEMORY with idea set to response text
        assert result["idea"] == "invalid json response"
        assert result["target_market"] == ""
        assert result["risks"] == []

    @patch("src.memory.Anthropic")
    @patch("src.memory.settings")
    def test_build_memory_long_response_truncation(self, mock_settings, mock_anthropic_class):
        """Test truncation of long response when JSON parsing fails."""
        mock_settings.anthropic_key = "test-key"
        mock_settings.model_memory = "claude-3-haiku"
        mock_settings.max_tokens_memory = 1024
        mock_settings.temperature_memory = 0.3
        mock_settings.top_p = 0.9

        mock_client = Mock()
        mock_response = Mock()
        long_response = (
            "x" * 500
        )  # Long response - first 400 chars go to idea, then truncated to 300
        mock_response.content = [Mock(text=long_response)]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        messages = [{"name": "human", "content": "Test message"}]

        result = build_memory_from_messages(messages)

        # The response gets truncated to 400 chars first, then field normalization trims to 300
        assert len(result["idea"]) == 300
        assert result["idea"] == "x" * 300

    @patch("src.memory.Anthropic")
    @patch("src.memory.settings")
    def test_build_memory_field_normalization(self, mock_settings, mock_anthropic_class):
        """Test field normalization and filtering."""
        mock_settings.anthropic_key = "test-key"
        mock_settings.model_memory = "claude-3-haiku"
        mock_settings.max_tokens_memory = 1024
        mock_settings.temperature_memory = 0.3
        mock_settings.top_p = 0.9

        mock_client = Mock()
        mock_response = Mock()
        response_data = {
            "idea": "x" * 400,  # Long field that should be truncated
            "target_market": "Valid market",
            "unknown_field": "Should be ignored",
            "risks": ["Risk 1", "Risk 2", "Risk 3", "Risk 4", "Risk 5", "Risk 6"],  # > 5 items
            "assumptions": ["A1", "A2"],
        }
        mock_response.content = [Mock(text=json.dumps(response_data))]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        messages = [{"name": "human", "content": "Test message"}]

        result = build_memory_from_messages(messages)

        # String fields should be truncated to 300 chars
        assert len(result["idea"]) == 300
        assert result["target_market"] == "Valid market"

        # Unknown fields should be ignored
        assert "unknown_field" not in result

        # List fields should be truncated to 5 items
        assert len(result["risks"]) == 5
        assert result["risks"] == ["Risk 1", "Risk 2", "Risk 3", "Risk 4", "Risk 5"]
        assert result["assumptions"] == ["A1", "A2"]

    @patch("src.memory.Anthropic")
    @patch("src.memory.settings")
    def test_build_memory_custom_model(self, mock_settings, mock_anthropic_class):
        """Test build_memory with custom model parameter."""
        mock_settings.anthropic_key = "test-key"
        mock_settings.model_memory = "claude-3-haiku"  # Default
        mock_settings.max_tokens_memory = 1024
        mock_settings.temperature_memory = 0.3
        mock_settings.top_p = 0.9

        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text='{"idea": "Test"}')]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        messages = [{"name": "human", "content": "Test"}]

        # Use custom model
        build_memory_from_messages(messages, model="claude-3-sonnet")

        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-3-sonnet"

    @patch("src.memory.Anthropic")
    @patch("src.memory.settings")
    def test_build_memory_empty_messages(self, mock_settings, mock_anthropic_class):
        """Test build_memory with empty messages list."""
        mock_settings.anthropic_key = "test-key"
        mock_settings.model_memory = "claude-3-haiku"
        mock_settings.max_tokens_memory = 1024
        mock_settings.temperature_memory = 0.3
        mock_settings.top_p = 0.9

        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="{}")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        build_memory_from_messages([])

        # Should still work with just the prompt
        call_kwargs = mock_client.messages.create.call_args[1]
        formatted_messages = call_kwargs["messages"]
        assert len(formatted_messages) == 1
        assert formatted_messages[0]["role"] == "user"
        assert PROMPT_JSON in formatted_messages[0]["content"]

    @patch("src.memory.Anthropic")
    @patch("src.memory.settings")
    def test_build_memory_messages_without_content(self, mock_settings, mock_anthropic_class):
        """Test build_memory with messages missing content field."""
        mock_settings.anthropic_key = "test-key"
        mock_settings.model_memory = "claude-3-haiku"
        mock_settings.max_tokens_memory = 1024
        mock_settings.temperature_memory = 0.3
        mock_settings.top_p = 0.9

        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="{}")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        messages = [
            {"name": "human"},  # Missing content
            {"name": "assistant", "content": "Valid content"},
        ]

        build_memory_from_messages(messages)

        call_kwargs = mock_client.messages.create.call_args[1]
        formatted_messages = call_kwargs["messages"]

        assert formatted_messages[0]["content"] == ""  # Empty content for missing field
        assert formatted_messages[1]["content"] == "Valid content"


class TestPromptJSON:
    """Test PROMPT_JSON constant."""

    def test_prompt_json_content(self):
        """Test PROMPT_JSON contains expected content."""
        assert "JSON object" in PROMPT_JSON
        assert "idea" in PROMPT_JSON
        assert "target_market" in PROMPT_JSON
        assert "customer" in PROMPT_JSON
        assert "region" in PROMPT_JSON
        assert "pricing_model" in PROMPT_JSON
        assert "key_constraints" in PROMPT_JSON
        assert "risks" in PROMPT_JSON
        assert "assumptions" in PROMPT_JSON
        assert "No extra text" in PROMPT_JSON


class TestIntegration:
    """Test integration scenarios."""

    def test_full_memory_workflow(self):
        """Test complete memory workflow: load -> update -> save."""
        test_data = {
            "idea": "E-commerce Platform",
            "target_market": "SMB",
            "risks": ["Competition", "Technical challenges"],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "test_memory.json"

            # Save initial memory
            save_memory(str(memory_path), test_data)

            # Load memory
            loaded = load_memory(str(memory_path))
            assert loaded["idea"] == "E-commerce Platform"

            # Generate memory block
            block = memory_block(loaded)
            assert "E-commerce Platform" in block
            assert "Competition; Technical challenges" in block

            # Update and save again
            loaded["region"] = "Global"
            save_memory(str(memory_path), loaded)

            # Verify update
            reloaded = load_memory(str(memory_path))
            assert reloaded["region"] == "Global"

    def test_memory_block_formatting_consistency(self):
        """Test memory block formatting is consistent."""
        test_memories = [
            {"idea": "Simple idea"},
            {
                "idea": "Complex idea",
                "risks": ["Risk 1", "Risk 2"],
                "assumptions": ["Assumption 1"],
            },
            {},  # Empty
        ]

        for mem in test_memories:
            block = memory_block(mem)
            if block:  # Non-empty
                assert block.startswith("## Session Memory (facts & assumptions)")
                lines = block.split("\n")
                # All content lines should start with "- "
                for line in lines[1:]:  # Skip header
                    if line.strip():
                        assert line.startswith("- ")

    def test_data_persistence_integrity(self):
        """Test data integrity through save/load cycle."""
        original_data = {
            "idea": "Test Startup with special chars: éñ中文🚀",
            "target_market": "Global market",
            "key_constraints": ["Budget limit", "Time constraint"],
            "risks": ["Market risk", "Technical risk", "Financial risk"],
            "assumptions": ["Strong demand", "Team availability"],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "integrity_test.json"

            # Save and load
            save_memory(str(memory_path), original_data)
            loaded_data = load_memory(str(memory_path))

            # Should be identical
            assert loaded_data == original_data

            # Memory block should include all data
            block = memory_block(loaded_data)
            assert "Test Startup with special chars: éñ中文🚀" in block
            assert "Budget limit; Time constraint" in block
            assert "Market risk; Technical risk; Financial risk" in block

    @patch("src.memory.Anthropic")
    @patch("src.memory.settings")
    def test_api_error_handling(self, mock_settings, mock_anthropic_class):
        """Test API error handling in build_memory_from_messages."""
        mock_settings.anthropic_key = "test-key"
        mock_settings.model_memory = "claude-3-haiku"
        mock_settings.max_tokens_memory = 1024
        mock_settings.temperature_memory = 0.3
        mock_settings.top_p = 0.9

        # Mock API failure
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic_class.return_value = mock_client

        messages = [{"name": "human", "content": "Test message"}]

        # Should handle exception gracefully
        with pytest.raises(Exception):
            build_memory_from_messages(messages)
