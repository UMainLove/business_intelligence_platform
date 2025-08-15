"""
Synthetic tests for memory.py without external dependencies.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.memory import (
    DEFAULT_MEMORY,
    memory_block,
    load_memory,
    save_memory,
    build_memory_from_messages,
    PROMPT_JSON
)


class TestMemoryBlock:
    """Test memory block rendering."""

    def test_memory_block_empty(self):
        """Test memory block with empty memory."""
        mem = DEFAULT_MEMORY.copy()
        result = memory_block(mem)
        assert result == ""  # Empty memory returns empty string

    def test_memory_block_with_idea(self):
        """Test memory block with just idea."""
        mem = {"idea": "AI-powered business analyzer"}
        result = memory_block(mem)
        assert "## Session Memory" in result
        assert "Idea: AI-powered business analyzer" in result

    def test_memory_block_full(self):
        """Test memory block with all fields."""
        mem = {
            "idea": "AI startup",
            "target_market": "B2B SaaS",
            "customer": "Enterprises",
            "region": "North America",
            "pricing_model": "Subscription",
            "key_constraints": ["Budget", "Timeline"],
            "risks": ["Competition", "Market saturation"],
            "assumptions": ["Growth rate", "Adoption speed"]
        }
        result = memory_block(mem)
        
        assert "## Session Memory" in result
        assert "Idea: AI startup" in result
        assert "Target market: B2B SaaS" in result
        assert "Customer: Enterprises" in result
        assert "Region: North America" in result
        assert "Pricing model: Subscription" in result
        assert "Key constraints: Budget; Timeline" in result
        assert "Risks: Competition; Market saturation" in result
        assert "Assumptions: Growth rate; Adoption speed" in result

    def test_memory_block_partial(self):
        """Test memory block with partial fields."""
        mem = {
            "idea": "Test idea",
            "risks": ["Risk 1", "Risk 2"],
            "unrelated_field": "Should be ignored"
        }
        result = memory_block(mem)
        
        assert "Idea: Test idea" in result
        assert "Risks: Risk 1; Risk 2" in result
        assert "unrelated_field" not in result

    def test_memory_block_empty_lists(self):
        """Test memory block with empty lists."""
        mem = {
            "idea": "Test",
            "key_constraints": [],
            "risks": [],
            "assumptions": []
        }
        result = memory_block(mem)
        
        assert "Idea: Test" in result
        assert "Key constraints" not in result  # Empty lists not shown
        assert "Risks" not in result
        assert "Assumptions" not in result

    def test_memory_block_none_values(self):
        """Test memory block with None values."""
        mem = {
            "idea": "Test",
            "target_market": None,
            "customer": "",
            "risks": None
        }
        result = memory_block(mem)
        
        assert "Idea: Test" in result
        assert "Target market" not in result  # None/empty not shown
        assert "Customer" not in result


class TestMemoryPersistence:
    """Test memory load/save functions."""

    def test_load_memory_default(self):
        """Test loading memory from non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = f"{tmpdir}/nonexistent.json"
            mem = load_memory(path)
            
            assert mem == DEFAULT_MEMORY
            assert mem["idea"] == ""
            assert mem["key_constraints"] == []

    def test_save_and_load_memory(self):
        """Test saving and loading memory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = f"{tmpdir}/memory.json"
            
            # Save memory
            mem_to_save = {
                "idea": "Test idea",
                "target_market": "B2C",
                "customer": "Consumers",
                "region": "Global",
                "pricing_model": "Freemium",
                "key_constraints": ["Resources"],
                "risks": ["Execution"],
                "assumptions": ["Market size"]
            }
            save_memory(path, mem_to_save)
            
            # Verify file was created
            assert Path(path).exists()
            
            # Load memory
            loaded_mem = load_memory(path)
            assert loaded_mem == mem_to_save

    def test_save_memory_creates_parent_dirs(self):
        """Test that save_memory creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = f"{tmpdir}/deep/nested/path/memory.json"
            
            mem = {"idea": "Test"}
            save_memory(path, mem)
            
            assert Path(path).exists()
            loaded = load_memory(path)
            assert loaded["idea"] == "Test"

    def test_load_memory_invalid_json(self):
        """Test loading memory from invalid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = f"{tmpdir}/invalid.json"
            
            # Write invalid JSON
            Path(path).write_text("not valid json {]", encoding="utf-8")
            
            # Should return default memory
            mem = load_memory(path)
            assert mem == DEFAULT_MEMORY

    def test_save_memory_with_unicode(self):
        """Test saving memory with unicode characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = f"{tmpdir}/unicode.json"
            
            mem = {
                "idea": "Test with émojis 🚀",
                "target_market": "中国市场",
                "customer": "Entreprises françaises",
                "region": "日本",
                "pricing_model": "",
                "key_constraints": [],
                "risks": [],
                "assumptions": []
            }
            save_memory(path, mem)
            
            loaded = load_memory(path)
            assert loaded["idea"] == "Test with émojis 🚀"
            assert loaded["target_market"] == "中国市场"
            assert loaded["region"] == "日本"


class TestBuildMemoryFromMessages:
    """Test LLM-powered memory extraction."""

    @patch('src.memory.Anthropic')
    @patch('src.memory.settings')
    def test_build_memory_success(self, mock_settings, mock_anthropic_class):
        """Test successful memory extraction from messages."""
        # Configure settings
        mock_settings.anthropic_key = "test-key"
        mock_settings.model_memory = "claude-3-haiku"
        mock_settings.max_tokens_memory = 500
        mock_settings.temperature_memory = 0.3
        mock_settings.top_p = 0.95
        
        # Mock Anthropic client
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        
        # Mock response
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps({
            "idea": "AI chatbot",
            "target_market": "SMBs",
            "customer": "Small businesses",
            "region": "USA",
            "pricing_model": "Monthly subscription",
            "key_constraints": ["Technical expertise", "Budget"],
            "risks": ["Competition"],
            "assumptions": ["Market demand"]
        }))]
        mock_client.messages.create.return_value = mock_response
        
        # Test messages
        messages = [
            {"name": "human", "content": "I want to build an AI chatbot"},
            {"name": "assistant", "content": "Great idea! Let's target SMBs"}
        ]
        
        mem = build_memory_from_messages(messages)
        
        assert mem["idea"] == "AI chatbot"
        assert mem["target_market"] == "SMBs"
        assert mem["customer"] == "Small businesses"
        assert mem["region"] == "USA"
        assert mem["pricing_model"] == "Monthly subscription"
        assert mem["key_constraints"] == ["Technical expertise", "Budget"]
        assert mem["risks"] == ["Competition"]
        assert mem["assumptions"] == ["Market demand"]

    @patch('src.memory.Anthropic')
    @patch('src.memory.settings')
    def test_build_memory_json_parse_error(self, mock_settings, mock_anthropic_class):
        """Test memory extraction with JSON parse error."""
        mock_settings.anthropic_key = "test-key"
        mock_settings.model_memory = "claude-3-haiku"
        mock_settings.max_tokens_memory = 500
        mock_settings.temperature_memory = 0.3
        mock_settings.top_p = 0.95
        
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        
        # Return invalid JSON
        mock_response = Mock()
        mock_response.content = [Mock(text="This is not valid JSON")]
        mock_client.messages.create.return_value = mock_response
        
        messages = [{"name": "human", "content": "Test"}]
        
        mem = build_memory_from_messages(messages)
        
        # Should use the text as idea (truncated to 400 chars)
        assert mem["idea"] == "This is not valid JSON"
        assert mem["target_market"] == ""
        assert mem["key_constraints"] == []

    @patch('src.memory.Anthropic')
    @patch('src.memory.settings')
    def test_build_memory_with_long_fields(self, mock_settings, mock_anthropic_class):
        """Test memory extraction with fields that need truncation."""
        mock_settings.anthropic_key = "test-key"
        mock_settings.model_memory = "claude-3-haiku"
        mock_settings.max_tokens_memory = 500
        mock_settings.temperature_memory = 0.3
        mock_settings.top_p = 0.95
        
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        
        # Return response with very long fields
        long_text = "x" * 500
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps({
            "idea": long_text,
            "target_market": long_text,
            "customer": long_text,
            "region": long_text,
            "pricing_model": long_text,
            "key_constraints": ["a", "b", "c", "d", "e", "f", "g", "h"],
            "risks": ["1", "2", "3", "4", "5", "6", "7"],
            "assumptions": ["A", "B", "C", "D", "E", "F"]
        }))]
        mock_client.messages.create.return_value = mock_response
        
        messages = [{"name": "human", "content": "Test"}]
        
        mem = build_memory_from_messages(messages)
        
        # Text fields should be truncated to 300 chars
        assert len(mem["idea"]) == 300
        assert len(mem["target_market"]) == 300
        assert len(mem["customer"]) == 300
        assert len(mem["region"]) == 300
        assert len(mem["pricing_model"]) == 300
        
        # Lists should be truncated to 5 items
        assert len(mem["key_constraints"]) == 5
        assert len(mem["risks"]) == 5
        assert len(mem["assumptions"]) == 5

    @patch('src.memory.Anthropic')
    @patch('src.memory.settings')
    def test_build_memory_custom_model(self, mock_settings, mock_anthropic_class):
        """Test memory extraction with custom model."""
        mock_settings.anthropic_key = "test-key"
        mock_settings.model_memory = "claude-3-haiku"
        mock_settings.max_tokens_memory = 500
        mock_settings.temperature_memory = 0.3
        mock_settings.top_p = 0.95
        
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps({"idea": "Test"}))]
        mock_client.messages.create.return_value = mock_response
        
        messages = [{"name": "human", "content": "Test"}]
        
        # Use custom model
        mem = build_memory_from_messages(messages, model="claude-3-opus")
        
        # Verify custom model was used
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["model"] == "claude-3-opus"

    @patch('src.memory.Anthropic')
    @patch('src.memory.settings')
    def test_build_memory_message_formatting(self, mock_settings, mock_anthropic_class):
        """Test that messages are properly formatted for Anthropic."""
        mock_settings.anthropic_key = "test-key"
        mock_settings.model_memory = "claude-3-haiku"
        mock_settings.max_tokens_memory = 500
        mock_settings.temperature_memory = 0.3
        mock_settings.top_p = 0.95
        
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps({"idea": "Test"}))]
        mock_client.messages.create.return_value = mock_response
        
        messages = [
            {"name": "human", "content": "User message"},
            {"name": "assistant", "content": "Assistant reply"},
            {"name": "human", "content": "Another user message"}
        ]
        
        mem = build_memory_from_messages(messages)
        
        # Check that messages were properly formatted
        call_args = mock_client.messages.create.call_args
        formatted_msgs = call_args.kwargs["messages"]
        
        assert formatted_msgs[0] == {"role": "user", "content": "User message"}
        assert formatted_msgs[1] == {"role": "assistant", "content": "Assistant reply"}
        assert formatted_msgs[2] == {"role": "user", "content": "Another user message"}
        assert formatted_msgs[3] == {"role": "user", "content": PROMPT_JSON}


class TestDefaultMemory:
    """Test DEFAULT_MEMORY constant."""

    def test_default_memory_structure(self):
        """Test that DEFAULT_MEMORY has expected structure."""
        assert isinstance(DEFAULT_MEMORY, dict)
        assert DEFAULT_MEMORY["idea"] == ""
        assert DEFAULT_MEMORY["target_market"] == ""
        assert DEFAULT_MEMORY["customer"] == ""
        assert DEFAULT_MEMORY["region"] == ""
        assert DEFAULT_MEMORY["pricing_model"] == ""
        assert DEFAULT_MEMORY["key_constraints"] == []
        assert DEFAULT_MEMORY["risks"] == []
        assert DEFAULT_MEMORY["assumptions"] == []

    def test_default_memory_copy(self):
        """Test that DEFAULT_MEMORY.copy() creates independent copy."""
        mem1 = DEFAULT_MEMORY.copy()
        mem2 = DEFAULT_MEMORY.copy()
        
        # Note: .copy() only does shallow copy, so lists are shared
        # This is expected Python behavior
        mem1["idea"] = "Modified"
        mem1["risks"] = ["New risk"]  # Replace list instead of append
        
        assert mem2["idea"] == ""
        assert mem2["risks"] == []  # Original list unchanged
        assert DEFAULT_MEMORY["idea"] == ""