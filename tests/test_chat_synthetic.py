"""
Synthetic tests for chat.py without external dependencies.
"""

import pytest
from unittest.mock import Mock, patch
import json

from src.chat import (
    build_group,
    run_synthesizer,
    run_synthesizer_json,
    get_memory,
    set_memory,
    clear_memory,
    reset_messages,
    get_messages,
    update_memory_from_chat
)


class TestMemoryFunctions:
    """Test memory management functions."""

    def test_get_memory_initial(self):
        """Test getting initial memory."""
        memory = get_memory()
        assert isinstance(memory, dict)

    def test_set_memory(self):
        """Test setting memory."""
        test_memory = {"idea": "test idea", "market": "B2B"}
        set_memory(test_memory)
        
        retrieved_memory = get_memory()
        assert retrieved_memory["idea"] == "test idea"
        assert retrieved_memory["market"] == "B2B"

    def test_clear_memory(self):
        """Test clearing memory."""
        # Set some memory first
        set_memory({"idea": "test", "market": "test"})
        
        # Clear it
        clear_memory()
        
        # Should be empty or default
        memory = get_memory()
        assert memory.get("idea", "") == ""

    def test_update_memory_from_chat(self):
        """Test updating memory from chat messages."""
        with patch('src.chat.build_memory_from_messages') as mock_build:
            mock_build.return_value = {"idea": "AI company", "market": "enterprises"}
            
            result = update_memory_from_chat()
            
            # Should return a dict
            assert isinstance(result, dict)


class TestMessageFunctions:
    """Test message management functions."""

    def test_get_messages_initial(self):
        """Test getting initial messages."""
        messages = get_messages()
        assert isinstance(messages, list)

    def test_reset_messages(self):
        """Test resetting messages."""
        reset_messages()
        messages = get_messages()
        assert len(messages) == 0


class TestSynthesizerFunctions:
    """Test synthesizer functions."""

    @patch('src.chat.build_group')
    def test_run_synthesizer(self, mock_build_group):
        """Test running synthesizer."""
        # Mock the build_group function
        mock_manager = Mock()
        mock_groupchat = Mock()
        mock_groupchat.messages = [{"content": "test message"}]
        mock_manager.groupchat = mock_groupchat
        
        mock_synthesizer = Mock()
        mock_synthesizer.generate_reply.return_value = "Synthesis result"
        
        mock_build_group.return_value = (mock_manager, [], mock_synthesizer)
        
        result = run_synthesizer()
        
        assert result == "Synthesis result"
        mock_synthesizer.generate_reply.assert_called_once()

    @patch('src.chat.build_group')
    def test_run_synthesizer_json(self, mock_build_group):
        """Test running synthesizer with JSON output."""
        # Mock the build_group function
        mock_manager = Mock()
        mock_groupchat = Mock()
        mock_groupchat.messages = [{"content": "test message"}]
        mock_manager.groupchat = mock_groupchat
        
        mock_synthesizer = Mock()
        mock_synthesizer.generate_reply.return_value = json.dumps({
            "executive_summary": "Test summary",
            "economic_viability": "Good"
        })
        
        mock_build_group.return_value = (mock_manager, [], mock_synthesizer)
        
        result = run_synthesizer_json()
        
        assert isinstance(result, dict)
        assert result["executive_summary"] == "Test summary"
        assert result["economic_viability"] == "Good"


class TestBuildGroup:
    """Test group building function."""

    @patch('src.chat._anthropic_cfg')
    @patch('src.chat.ConversableAgent')
    @patch('src.chat.GroupChat')
    @patch('src.chat.GroupChatManager')
    def test_build_group(self, mock_manager_class, mock_chat_class, mock_agent_class, mock_cfg):
        """Test building chat group."""
        # Mock configuration - needs to support context manager protocol
        mock_llm_config = Mock()
        mock_llm_config.__enter__ = Mock(return_value=mock_llm_config)
        mock_llm_config.__exit__ = Mock(return_value=None)
        mock_cfg.return_value = mock_llm_config
        
        # Mock agents
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        
        # Mock group chat
        mock_chat = Mock()
        mock_chat_class.return_value = mock_chat
        
        # Mock manager
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        
        result = build_group()
        
        assert result is not None
        # Should return a tuple with manager, agents, and synthesizer
        assert len(result) == 3


class TestModuleFunctions:
    """Test overall module functionality."""

    def test_all_functions_callable(self):
        """Test that all imported functions are callable."""
        assert callable(build_group)
        assert callable(run_synthesizer)
        assert callable(run_synthesizer_json)
        assert callable(get_memory)
        assert callable(set_memory)
        assert callable(clear_memory)
        assert callable(reset_messages)
        assert callable(get_messages)
        assert callable(update_memory_from_chat)

    def test_memory_persistence(self):
        """Test memory persistence across operations."""
        # Start fresh
        clear_memory()
        
        # Set some data
        test_data = {"idea": "persistent test", "market": "test market"}
        set_memory(test_data)
        
        # Verify it persists
        retrieved = get_memory()
        assert retrieved["idea"] == "persistent test"
        assert retrieved["market"] == "test market"
        
        # Clean up
        clear_memory()

    def test_messages_state_management(self):
        """Test message state management."""
        # Reset to clean state
        reset_messages()
        
        # Should start empty
        messages = get_messages()
        assert len(messages) == 0
        
        # Messages should be manageable
        assert isinstance(messages, list)