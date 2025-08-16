"""
Comprehensive tests for chat.py to achieve 95%+ coverage.
"""

import json
from unittest.mock import Mock, patch

import pytest

from src.chat import (
    _anthropic_cfg,
    _compose_system,
    _construct_group_from_memory,
    _rebuild_group,
    build_group,
    clear_memory,
    get_memory,
    get_messages,
    reset_messages,
    run_synthesizer,
    run_synthesizer_json,
    set_memory,
    update_memory_from_chat,
)


class TestAnthropicCfg:
    """Test _anthropic_cfg function."""

    @patch("src.chat.settings")
    def test_anthropic_cfg_basic(self, mock_settings):
        """Test basic LLMConfig creation."""
        mock_settings.anthropic_key = "test-key"
        mock_settings.top_k = 0
        mock_settings.thinking_enabled = False

        with patch("src.chat.LLMConfig") as mock_llm_config:
            result = _anthropic_cfg("claude-3-sonnet", 0.7, 2048)

            mock_llm_config.assert_called_once()
            call_kwargs = mock_llm_config.call_args[1]

            assert call_kwargs["api_type"] == "anthropic"
            assert call_kwargs["model"] == "claude-3-sonnet"
            assert call_kwargs["api_key"] == "test-key"
            assert call_kwargs["temperature"] == 0.7
            assert call_kwargs["max_tokens"] == 2048

    @patch("src.chat.settings")
    def test_anthropic_cfg_with_top_p(self, mock_settings):
        """Test LLMConfig creation with top_p parameter."""
        mock_settings.anthropic_key = "test-key"
        mock_settings.top_k = 0
        mock_settings.thinking_enabled = False

        with patch("src.chat.LLMConfig") as mock_llm_config:
            result = _anthropic_cfg("claude-3-sonnet", 0.7, 2048, top_p=0.9)

            call_kwargs = mock_llm_config.call_args[1]
            assert call_kwargs["top_p"] == 0.9

    @patch("src.chat.settings")
    def test_anthropic_cfg_with_top_k(self, mock_settings):
        """Test LLMConfig creation with top_k parameter."""
        mock_settings.anthropic_key = "test-key"
        mock_settings.top_k = 40
        mock_settings.thinking_enabled = False

        with patch("src.chat.LLMConfig") as mock_llm_config:
            result = _anthropic_cfg("claude-3-sonnet", 0.7, 2048)

            call_kwargs = mock_llm_config.call_args[1]
            assert call_kwargs["top_k"] == 40

    @patch("src.chat.settings")
    def test_anthropic_cfg_opus_with_thinking(self, mock_settings):
        """Test LLMConfig creation for Opus with thinking mode."""
        mock_settings.anthropic_key = "test-key"
        mock_settings.top_k = 0
        mock_settings.thinking_enabled = True
        mock_settings.thinking_budget_tokens = 50000

        with patch("src.chat.LLMConfig") as mock_llm_config:
            result = _anthropic_cfg("claude-3-opus", 0.7, 2048)

            call_kwargs = mock_llm_config.call_args[1]
            assert call_kwargs["thinking_budget_tokens"] == 50000

    @patch("src.chat.settings")
    def test_anthropic_cfg_non_opus_no_thinking(self, mock_settings):
        """Test LLMConfig creation for non-Opus models (no thinking)."""
        mock_settings.anthropic_key = "test-key"
        mock_settings.top_k = 0
        mock_settings.thinking_enabled = True
        mock_settings.thinking_budget_tokens = 50000

        with patch("src.chat.LLMConfig") as mock_llm_config:
            result = _anthropic_cfg("claude-3-sonnet", 0.7, 2048)

            call_kwargs = mock_llm_config.call_args[1]
            assert "thinking_budget_tokens" not in call_kwargs

    @patch("src.chat.settings")
    def test_anthropic_cfg_thinking_disabled(self, mock_settings):
        """Test LLMConfig creation with thinking disabled."""
        mock_settings.anthropic_key = "test-key"
        mock_settings.top_k = 0
        mock_settings.thinking_enabled = False
        mock_settings.thinking_budget_tokens = 50000

        with patch("src.chat.LLMConfig") as mock_llm_config:
            result = _anthropic_cfg("claude-3-opus", 0.7, 2048)

            call_kwargs = mock_llm_config.call_args[1]
            assert "thinking_budget_tokens" not in call_kwargs

    @patch("src.chat.settings")
    def test_anthropic_cfg_default_max_tokens(self, mock_settings):
        """Test LLMConfig creation with default max_tokens."""
        mock_settings.anthropic_key = "test-key"
        mock_settings.top_k = 0
        mock_settings.thinking_enabled = False

        with patch("src.chat.LLMConfig") as mock_llm_config:
            result = _anthropic_cfg("claude-3-sonnet", 0.7)

            call_kwargs = mock_llm_config.call_args[1]
            assert call_kwargs["max_tokens"] == 2048


class TestComposeSystem:
    """Test _compose_system function."""

    @patch("src.chat.memory_block")
    def test_compose_system_no_memory(self, mock_memory_block):
        """Test system prompt composition without memory."""
        mock_memory_block.return_value = ""

        with patch("src.chat._memory_dict", None):
            result = _compose_system("Base prompt")

            assert result == "Base prompt"
            mock_memory_block.assert_called_once_with({})

    @patch("src.chat.memory_block")
    def test_compose_system_with_memory(self, mock_memory_block):
        """Test system prompt composition with memory."""
        mock_memory_block.return_value = "## Session Memory\n- Idea: Test startup"

        with patch("src.chat._memory_dict", {"idea": "Test startup"}):
            result = _compose_system("Base prompt")

            expected = "Base prompt\n\n## Session Memory\n- Idea: Test startup"
            assert result == expected
            mock_memory_block.assert_called_once_with({"idea": "Test startup"})

    @patch("src.chat.memory_block")
    def test_compose_system_empty_memory_dict(self, mock_memory_block):
        """Test system prompt composition with empty memory dict."""
        mock_memory_block.return_value = ""

        with patch("src.chat._memory_dict", {}):
            result = _compose_system("Base prompt")

            assert result == "Base prompt"
            mock_memory_block.assert_called_once_with({})


class TestConstructGroupFromMemory:
    """Test _construct_group_from_memory function."""

    @patch("src.chat._anthropic_cfg")
    @patch("src.chat._compose_system")
    @patch("src.chat.settings")
    @patch("src.chat.ConversableAgent")
    @patch("src.chat.GroupChat")
    @patch("src.chat.GroupChatManager")
    def test_construct_group_from_memory_success(
        self, mock_manager, mock_chat, mock_agent, mock_settings, mock_compose, mock_anthropic
    ):
        """Test successful group construction from memory."""
        # Mock settings
        mock_settings.model_specialists = "claude-3-sonnet"
        mock_settings.model_synth = "claude-3-haiku"
        mock_settings.temperature_economist = 0.7
        mock_settings.temperature_lawyer = 0.5
        mock_settings.temperature_sociologist = 0.6
        mock_settings.temperature_synth = 0.4
        mock_settings.max_tokens_specialists = 4000
        mock_settings.max_tokens_synth = 2000
        mock_settings.top_p = 0.9

        # Mock LLM config as context manager
        mock_llm_config = Mock()
        mock_llm_config.__enter__ = Mock(return_value=mock_llm_config)
        mock_llm_config.__exit__ = Mock(return_value=None)
        mock_anthropic.return_value = mock_llm_config
        mock_compose.return_value = "System message"

        # Mock prompt functions
        with patch("src.chat.economist_prompt", return_value="Economist prompt"):
            with patch("src.chat.lawyer_prompt", return_value="Lawyer prompt"):
                with patch("src.chat.sociologist_prompt", return_value="Sociologist prompt"):
                    with patch("src.chat.synthesizer_prompt", return_value="Synthesizer prompt"):
                        # Mock instances
                        mock_agent_instance = Mock()
                        mock_agent.return_value = mock_agent_instance
                        mock_chat_instance = Mock()
                        mock_chat.return_value = mock_chat_instance
                        mock_manager_instance = Mock()
                        mock_manager.return_value = mock_manager_instance

                        result = _construct_group_from_memory()

                        # Verify result structure
                        assert len(result) == 3
                        manager, user_proxy, synthesizer = result

                        # Verify agents and components were created
                        assert (
                            mock_agent.call_count >= 4
                        )  # economist, lawyer, sociologist, user_proxy, synthesizer
                        mock_chat.assert_called_once()
                        mock_manager.assert_called_once()

    @patch("src.chat._anthropic_cfg")
    @patch("src.chat._compose_system")
    @patch("src.chat.settings")
    @patch("src.chat.ConversableAgent")
    @patch("src.chat.GroupChat")
    @patch("src.chat.GroupChatManager")
    def test_construct_group_agent_names(
        self, mock_manager, mock_chat, mock_agent, mock_settings, mock_compose, mock_anthropic
    ):
        """Test that agents are created with correct names."""
        # Mock settings
        mock_settings.model_specialists = "claude-3-sonnet"
        mock_settings.model_synth = "claude-3-haiku"
        mock_settings.temperature_economist = 0.7
        mock_settings.temperature_lawyer = 0.5
        mock_settings.temperature_sociologist = 0.6
        mock_settings.temperature_synth = 0.4
        mock_settings.max_tokens_specialists = 4000
        mock_settings.max_tokens_synth = 2000
        mock_settings.top_p = 0.9

        # Mock LLM config as context manager
        mock_llm_config = Mock()
        mock_llm_config.__enter__ = Mock(return_value=mock_llm_config)
        mock_llm_config.__exit__ = Mock(return_value=None)
        mock_anthropic.return_value = mock_llm_config
        mock_compose.return_value = "System message"

        # Mock prompt functions
        with patch("src.chat.economist_prompt", return_value="Economist prompt"):
            with patch("src.chat.lawyer_prompt", return_value="Lawyer prompt"):
                with patch("src.chat.sociologist_prompt", return_value="Sociologist prompt"):
                    with patch("src.chat.synthesizer_prompt", return_value="Synthesizer prompt"):
                        _construct_group_from_memory()

                        # Check agent creation calls
                        calls = mock_agent.call_args_list
                        agent_names = [call[1]["name"] for call in calls if "name" in call[1]]

                        assert "economist" in agent_names
                        assert "lawyer" in agent_names
                        assert "sociologist" in agent_names
                        assert "synthesizer" in agent_names
                        assert "human" in agent_names


class TestRebuildGroup:
    """Test _rebuild_group function."""

    @patch("src.chat._construct_group_from_memory")
    def test_rebuild_group_no_preserve_messages(self, mock_construct):
        """Test rebuild group without preserving messages."""
        mock_manager = Mock()
        mock_user_proxy = Mock()
        mock_synthesizer = Mock()
        mock_construct.return_value = (mock_manager, mock_user_proxy, mock_synthesizer)

        with patch("src.chat._manager", None):
            result = _rebuild_group(preserve_messages=False)

            assert len(result) == 3
            mock_construct.assert_called_once()

    @patch("src.chat._construct_group_from_memory")
    def test_rebuild_group_preserve_messages_no_existing_manager(self, mock_construct):
        """Test rebuild group with preserve messages but no existing manager."""
        mock_manager = Mock()
        mock_user_proxy = Mock()
        mock_synthesizer = Mock()
        mock_construct.return_value = (mock_manager, mock_user_proxy, mock_synthesizer)

        with patch("src.chat._manager", None):
            result = _rebuild_group(preserve_messages=True)

            assert len(result) == 3
            mock_construct.assert_called_once()

    @patch("src.chat._construct_group_from_memory")
    def test_rebuild_group_preserve_messages_with_existing_manager(self, mock_construct):
        """Test rebuild group preserving messages from existing manager."""
        # Mock existing manager with messages
        existing_manager = Mock()
        existing_messages = [
            {"name": "human", "content": "Hello"},
            {"name": "economist", "content": "Hi there"},
        ]
        existing_manager.groupchat.messages = existing_messages

        # Mock new manager with proper message list
        new_manager = Mock()
        mock_messages_list = Mock()
        new_manager.groupchat.messages = mock_messages_list
        mock_user_proxy = Mock()
        mock_synthesizer = Mock()
        mock_construct.return_value = (new_manager, mock_user_proxy, mock_synthesizer)

        with patch("src.chat._manager", existing_manager):
            result = _rebuild_group(preserve_messages=True)

            # Check that messages were extended
            mock_messages_list.extend.assert_called_once_with(existing_messages)

    @patch("src.chat._construct_group_from_memory")
    def test_rebuild_group_updates_globals(self, mock_construct):
        """Test that rebuild_group updates global variables."""
        mock_manager = Mock()
        mock_user_proxy = Mock()
        mock_synthesizer = Mock()
        mock_construct.return_value = (mock_manager, mock_user_proxy, mock_synthesizer)

        # Import the module to access globals
        import src.chat as chat_module

        result = _rebuild_group(preserve_messages=False)

        # Check that globals were updated
        assert chat_module._manager == mock_manager
        assert chat_module._user_proxy == mock_user_proxy
        assert chat_module._synthesizer == mock_synthesizer


class TestBuildGroup:
    """Test build_group function."""

    @patch("src.chat._rebuild_group")
    @patch("src.chat.load_memory")
    def test_build_group_first_call(self, mock_load_memory, mock_rebuild):
        """Test build_group on first call (no cached manager)."""
        mock_memory = {"idea": "Test startup"}
        mock_load_memory.return_value = mock_memory

        mock_manager = Mock()
        mock_user_proxy = Mock()
        mock_synthesizer = Mock()
        mock_rebuild.return_value = (mock_manager, mock_user_proxy, mock_synthesizer)

        # Import module to reset globals
        import src.chat as chat_module

        chat_module._manager = None
        chat_module._memory_dict = None

        result = build_group()

        assert len(result) == 3
        mock_load_memory.assert_called_once()
        mock_rebuild.assert_called_once_with(preserve_messages=False)
        assert chat_module._memory_dict == mock_memory

    def test_build_group_cached_result(self):
        """Test build_group returns cached result."""
        # Set up cached globals
        import src.chat as chat_module

        mock_manager = Mock()
        mock_user_proxy = Mock()
        mock_synthesizer = Mock()
        chat_module._manager = mock_manager
        chat_module._user_proxy = mock_user_proxy
        chat_module._synthesizer = mock_synthesizer

        result = build_group()

        assert result == (mock_manager, mock_user_proxy, mock_synthesizer)

        # Reset for other tests
        chat_module._manager = None
        chat_module._user_proxy = None
        chat_module._synthesizer = None

    @patch("src.chat._rebuild_group")
    @patch("src.chat.load_memory")
    def test_build_group_memory_path(self, mock_load_memory, mock_rebuild):
        """Test build_group loads memory from correct path."""
        mock_load_memory.return_value = {}
        mock_rebuild.return_value = (Mock(), Mock(), Mock())

        import src.chat as chat_module

        chat_module._manager = None

        build_group()

        mock_load_memory.assert_called_once_with("data/sessions/session_memory.json")


class TestGetMemory:
    """Test get_memory function."""

    def test_get_memory_existing(self):
        """Test get_memory with existing memory dict."""
        import src.chat as chat_module

        test_memory = {"idea": "Test idea"}
        chat_module._memory_dict = test_memory

        result = get_memory()
        assert result == test_memory

    @patch("src.chat.build_group")
    def test_get_memory_none_initialize(self, mock_build_group):
        """Test get_memory initializes when memory is None."""
        import src.chat as chat_module

        chat_module._memory_dict = None

        result = get_memory()

        assert result == {}
        mock_build_group.assert_called_once()

    def test_get_memory_empty_dict(self):
        """Test get_memory with empty memory dict."""
        import src.chat as chat_module

        chat_module._memory_dict = {}

        result = get_memory()
        assert result == {}


class TestSetMemory:
    """Test set_memory function."""

    @patch("src.chat._rebuild_group")
    @patch("src.chat.save_memory")
    def test_set_memory_valid_dict(self, mock_save_memory, mock_rebuild):
        """Test set_memory with valid memory dict."""
        test_memory = {"idea": "New idea", "target_market": "B2B"}
        mock_result = (Mock(), Mock(), Mock())
        mock_rebuild.return_value = mock_result

        result = set_memory(test_memory)

        assert result == mock_result
        mock_save_memory.assert_called_once_with("data/sessions/session_memory.json", test_memory)
        mock_rebuild.assert_called_once_with(preserve_messages=True)

        # Check global was updated
        import src.chat as chat_module

        assert chat_module._memory_dict == test_memory

    @patch("src.chat._rebuild_group")
    @patch("src.chat.save_memory")
    def test_set_memory_none(self, mock_save_memory, mock_rebuild):
        """Test set_memory with None input."""
        mock_result = (Mock(), Mock(), Mock())
        mock_rebuild.return_value = mock_result

        result = set_memory(None)

        mock_save_memory.assert_called_once_with("data/sessions/session_memory.json", {})
        mock_rebuild.assert_called_once_with(preserve_messages=True)

        # Check global was updated to empty dict
        import src.chat as chat_module

        assert chat_module._memory_dict == {}

    @patch("src.chat._rebuild_group")
    @patch("src.chat.save_memory")
    def test_set_memory_empty_dict(self, mock_save_memory, mock_rebuild):
        """Test set_memory with empty dict."""
        mock_result = (Mock(), Mock(), Mock())
        mock_rebuild.return_value = mock_result

        result = set_memory({})

        mock_save_memory.assert_called_once_with("data/sessions/session_memory.json", {})
        mock_rebuild.assert_called_once_with(preserve_messages=True)


class TestClearMemory:
    """Test clear_memory function."""

    @patch("src.chat.set_memory")
    def test_clear_memory(self, mock_set_memory):
        """Test clear_memory function."""
        mock_result = (Mock(), Mock(), Mock())
        mock_set_memory.return_value = mock_result

        result = clear_memory()

        assert result == mock_result
        mock_set_memory.assert_called_once_with({})


class TestUpdateMemoryFromChat:
    """Test update_memory_from_chat function."""

    @patch("src.chat.build_group")
    @patch("src.chat.build_memory_from_messages")
    @patch("src.chat.set_memory")
    def test_update_memory_from_chat_success(
        self, mock_set_memory, mock_build_memory, mock_build_group
    ):
        """Test successful memory update from chat."""
        # Mock manager with messages
        mock_manager = Mock()
        mock_messages = [
            {"name": "human", "content": "I want to start a SaaS business"},
            {"name": "economist", "content": "That's a good market"},
        ]
        mock_manager.groupchat.messages = mock_messages
        mock_build_group.return_value = (mock_manager, Mock(), Mock())

        # Mock memory building
        new_memory = {"idea": "SaaS business", "target_market": "B2B"}
        mock_build_memory.return_value = new_memory

        result = update_memory_from_chat()

        assert result == new_memory
        mock_build_memory.assert_called_once_with(mock_messages)
        mock_set_memory.assert_called_once_with(new_memory)

    @patch("src.chat.build_group")
    @patch("src.chat.build_memory_from_messages")
    @patch("src.chat.set_memory")
    def test_update_memory_from_chat_empty_messages(
        self, mock_set_memory, mock_build_memory, mock_build_group
    ):
        """Test memory update with empty message list."""
        mock_manager = Mock()
        mock_manager.groupchat.messages = []
        mock_build_group.return_value = (mock_manager, Mock(), Mock())

        new_memory = {}
        mock_build_memory.return_value = new_memory

        result = update_memory_from_chat()

        assert result == new_memory
        mock_build_memory.assert_called_once_with([])
        mock_set_memory.assert_called_once_with(new_memory)


class TestRunSynthesizer:
    """Test run_synthesizer function."""

    @patch("src.chat.build_group")
    def test_run_synthesizer_success(self, mock_build_group):
        """Test successful synthesizer run."""
        # Mock components
        mock_manager = Mock()
        mock_messages = [{"name": "human", "content": "Generate report"}]
        mock_messages_list = Mock()
        mock_messages_list.__iter__ = Mock(return_value=iter(mock_messages))
        mock_manager.groupchat.messages = mock_messages_list

        mock_synthesizer = Mock()
        mock_synthesizer.generate_reply.return_value = "Synthesis report content"

        mock_build_group.return_value = (mock_manager, Mock(), mock_synthesizer)

        result = run_synthesizer()

        assert result == "Synthesis report content"
        mock_synthesizer.generate_reply.assert_called_once_with(messages=mock_messages_list)

        # Check message was appended
        expected_message = {"name": "synthesizer", "content": "Synthesis report content"}
        mock_messages_list.append.assert_called_once_with(expected_message)

    @patch("src.chat.build_group")
    def test_run_synthesizer_empty_messages(self, mock_build_group):
        """Test synthesizer run with empty messages."""
        mock_manager = Mock()
        mock_messages_list = Mock()
        mock_messages_list.__iter__ = Mock(return_value=iter([]))
        mock_manager.groupchat.messages = mock_messages_list

        mock_synthesizer = Mock()
        mock_synthesizer.generate_reply.return_value = "Empty context synthesis"

        mock_build_group.return_value = (mock_manager, Mock(), mock_synthesizer)

        result = run_synthesizer()

        assert result == "Empty context synthesis"
        mock_synthesizer.generate_reply.assert_called_once_with(messages=mock_messages_list)


class TestRunSynthesizerJson:
    """Test run_synthesizer_json function."""

    @patch("src.chat.build_group")
    def test_run_synthesizer_json_valid_json(self, mock_build_group):
        """Test synthesizer JSON run with valid JSON response."""
        mock_manager = Mock()
        mock_manager.groupchat.messages = []

        valid_json = {
            "executive_summary": "Great business idea",
            "economic_viability": "High potential",
            "legal_risks": "Low risk",
            "social_impact": "Positive",
            "next_steps": ["Market research", "Prototype"],
        }
        json_response = json.dumps(valid_json)

        mock_synthesizer = Mock()
        mock_synthesizer.generate_reply.return_value = json_response

        mock_build_group.return_value = (mock_manager, Mock(), mock_synthesizer)

        result = run_synthesizer_json()

        assert result == valid_json
        mock_synthesizer.generate_reply.assert_called_once()

    @patch("src.chat.build_group")
    def test_run_synthesizer_json_invalid_json(self, mock_build_group):
        """Test synthesizer JSON run with invalid JSON response."""
        mock_manager = Mock()
        mock_manager.groupchat.messages = []

        invalid_json_response = "This is not valid JSON content"

        mock_synthesizer = Mock()
        mock_synthesizer.generate_reply.return_value = invalid_json_response

        mock_build_group.return_value = (mock_manager, Mock(), mock_synthesizer)

        result = run_synthesizer_json()

        # Should return fallback structure
        assert "executive_summary" in result
        assert "economic_viability" in result
        assert "legal_risks" in result
        assert "social_impact" in result
        assert "next_steps" in result

        # Executive summary should be truncated raw response
        assert result["executive_summary"] == invalid_json_response[:800]
        assert result["economic_viability"] == ""
        assert result["legal_risks"] == ""
        assert result["social_impact"] == ""
        assert result["next_steps"] == []

    @patch("src.chat.build_group")
    def test_run_synthesizer_json_long_response(self, mock_build_group):
        """Test synthesizer JSON run with long invalid response."""
        mock_manager = Mock()
        mock_manager.groupchat.messages = []

        long_response = "x" * 1000  # Long invalid JSON

        mock_synthesizer = Mock()
        mock_synthesizer.generate_reply.return_value = long_response

        mock_build_group.return_value = (mock_manager, Mock(), mock_synthesizer)

        result = run_synthesizer_json()

        # Executive summary should be truncated to 800 chars
        assert len(result["executive_summary"]) == 800
        assert result["executive_summary"] == "x" * 800

    @patch("src.chat.build_group")
    def test_run_synthesizer_json_type_error(self, mock_build_group):
        """Test synthesizer JSON run with TypeError."""
        mock_manager = Mock()
        mock_messages_list = Mock()
        mock_manager.groupchat.messages = mock_messages_list

        mock_synthesizer = Mock()
        mock_synthesizer.generate_reply.return_value = None  # Will cause TypeError in json.loads

        mock_build_group.return_value = (mock_manager, Mock(), mock_synthesizer)

        # This should raise TypeError due to None slicing in the exception handler
        with pytest.raises(TypeError):
            run_synthesizer_json()

    @patch("src.chat.build_group")
    def test_run_synthesizer_json_message_appended(self, mock_build_group):
        """Test that synthesizer response is appended to messages."""
        mock_manager = Mock()
        mock_messages_list = Mock()
        mock_manager.groupchat.messages = mock_messages_list

        response = "Invalid JSON response"
        mock_synthesizer = Mock()
        mock_synthesizer.generate_reply.return_value = response

        mock_build_group.return_value = (mock_manager, Mock(), mock_synthesizer)

        result = run_synthesizer_json()

        # Check message was appended
        expected_message = {"name": "synthesizer", "content": response}
        mock_messages_list.append.assert_called_once_with(expected_message)


class TestGetMessages:
    """Test get_messages function."""

    @patch("src.chat.build_group")
    def test_get_messages_success(self, mock_build_group):
        """Test successful message retrieval."""
        mock_messages = [
            {"name": "human", "content": "Hello"},
            {"name": "economist", "content": "Hi there"},
            {"name": "synthesizer", "content": "Summary"},
        ]

        mock_manager = Mock()
        mock_manager.groupchat.messages = mock_messages

        mock_build_group.return_value = (mock_manager, Mock(), Mock())

        result = get_messages()

        assert result == mock_messages

    @patch("src.chat.build_group")
    def test_get_messages_empty(self, mock_build_group):
        """Test message retrieval with empty messages."""
        mock_manager = Mock()
        mock_manager.groupchat.messages = []

        mock_build_group.return_value = (mock_manager, Mock(), Mock())

        result = get_messages()

        assert result == []


class TestResetMessages:
    """Test reset_messages function."""

    @patch("src.chat.build_group")
    def test_reset_messages_success(self, mock_build_group):
        """Test successful message reset."""
        mock_messages_list = Mock()

        mock_manager = Mock()
        mock_manager.groupchat.messages = mock_messages_list

        mock_build_group.return_value = (mock_manager, Mock(), Mock())

        reset_messages()

        mock_messages_list.clear.assert_called_once()

    @patch("src.chat.build_group")
    def test_reset_messages_already_empty(self, mock_build_group):
        """Test message reset when already empty."""
        mock_messages_list = Mock()

        mock_manager = Mock()
        mock_manager.groupchat.messages = mock_messages_list

        mock_build_group.return_value = (mock_manager, Mock(), Mock())

        reset_messages()

        mock_messages_list.clear.assert_called_once()


class TestIntegration:
    """Test integration scenarios."""

    def test_all_functions_importable(self):
        """Test that all main functions can be imported."""
        try:
            from src.chat import (
                _anthropic_cfg,
                _compose_system,
                _construct_group_from_memory,
                _rebuild_group,
                build_group,
                clear_memory,
                get_memory,
                get_messages,
                reset_messages,
                run_synthesizer,
                run_synthesizer_json,
                set_memory,
                update_memory_from_chat,
            )

            assert True
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    def test_module_constants(self):
        """Test module-level constants."""
        import src.chat as chat_module

        assert hasattr(chat_module, "_manager")
        assert hasattr(chat_module, "_user_proxy")
        assert hasattr(chat_module, "_synthesizer")
        assert hasattr(chat_module, "_memory_dict")
        assert hasattr(chat_module, "_MEMORY_PATH")
        assert chat_module._MEMORY_PATH == "data/sessions/session_memory.json"

    def test_memory_workflow(self):
        """Test complete memory workflow."""
        # Setup initial memory
        initial_memory = {"idea": "Initial idea"}

        # Test workflow: get memory
        with patch("src.chat._memory_dict", initial_memory):
            memory = get_memory()
            assert memory == initial_memory

        # Test that get_memory initializes when None
        with patch("src.chat._memory_dict", None):
            with patch("src.chat.build_group") as mock_build:
                memory = get_memory()
                assert memory == {}
                mock_build.assert_called_once()

    @patch("src.chat.build_group")
    def test_synthesizer_workflow(self, mock_build_group):
        """Test complete synthesizer workflow."""
        mock_manager = Mock()
        mock_messages_list = Mock()
        mock_manager.groupchat.messages = mock_messages_list

        mock_synthesizer = Mock()
        mock_synthesizer.generate_reply.return_value = '{"executive_summary": "Test summary"}'

        mock_build_group.return_value = (mock_manager, Mock(), mock_synthesizer)

        # Test both synthesizer functions
        text_result = run_synthesizer()
        json_result = run_synthesizer_json()

        assert text_result == '{"executive_summary": "Test summary"}'
        assert json_result == {"executive_summary": "Test summary"}

        # Both should have appended messages
        assert mock_messages_list.append.call_count == 2
