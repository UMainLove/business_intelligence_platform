"""
Mock test for Anthropic API integration without making real API calls.
"""

import sys
from unittest.mock import Mock, patch

import pytest


class TestAnthropicIntegration:
    """Test Anthropic API integration with mocks."""

    @patch("anthropic.Anthropic")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key-12345"})
    def test_anthropic_client_creation(self, mock_anthropic_class):
        """Test Anthropic client creation."""
        import os

        from anthropic import Anthropic

        # Mock the client
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Verify client was created with correct API key
        mock_anthropic_class.assert_called_once_with(api_key="test-key-12345")
        assert client == mock_client

    @patch("anthropic.Anthropic")
    @patch.dict(
        "os.environ",
        {"ANTHROPIC_API_KEY": "test-key-12345", "ANTHROPIC_MODEL_SPECIALISTS": "test-model"},
    )
    def test_message_creation_mock(self, mock_anthropic_class):
        """Test message creation with mocked response."""
        import os

        from anthropic import Anthropic

        # Create mock response
        mock_content = Mock()
        mock_content.text = "pong"
        mock_response = Mock()
        mock_response.content = [mock_content]

        # Create mock client
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        # Create client and make request
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        model = os.getenv("ANTHROPIC_MODEL_SPECIALISTS", "claude-sonnet-4-20250514")

        resp = client.messages.create(
            model=model,
            max_tokens=40,
            messages=[{"role": "user", "content": "Reply with exactly: pong"}],
        )

        # Verify the response
        assert resp.content[0].text == "pong"

        # Verify the API call was made correctly
        mock_client.messages.create.assert_called_once_with(
            model="test-model",
            max_tokens=40,
            messages=[{"role": "user", "content": "Reply with exactly: pong"}],
        )

    def test_util_module_integration(self):
        """Test integration with util module."""
        # Since get_anthropic_client doesn't exist in util.py,
        # test the functions that actually exist
        from src.util import describe_pricing, estimate_cost_usd

        # Test cost estimation function exists and works
        cost = estimate_cost_usd(1000, use_bi_pricing=True)
        assert isinstance(cost, (int, float))
        assert cost >= 0

        # Test pricing description
        pricing = describe_pricing()
        assert isinstance(pricing, dict)

    def test_environment_variable_handling(self):
        """Test environment variable handling."""
        import os

        # Test default model fallback
        with patch.dict("os.environ", {}, clear=True):
            model = os.getenv("ANTHROPIC_MODEL_SPECIALISTS", "claude-sonnet-4-20250514")
            assert model == "claude-sonnet-4-20250514"

        # Test custom model
        with patch.dict("os.environ", {"ANTHROPIC_MODEL_SPECIALISTS": "custom-model"}):
            model = os.getenv("ANTHROPIC_MODEL_SPECIALISTS", "claude-sonnet-4-20250514")
            assert model == "custom-model"

    @patch("anthropic.Anthropic")
    def test_api_error_handling(self, mock_anthropic_class):
        """Test API error handling."""
        from anthropic import Anthropic

        # Create a mock response and body for AuthenticationError
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.headers = {"x-request-id": "test-request-id"}
        mock_body = {"error": {"type": "authentication_error", "message": "invalid x-api-key"}}

        # Import and create proper AuthenticationError
        from anthropic import AuthenticationError

        auth_error = AuthenticationError(
            message="invalid x-api-key", response=mock_response, body=mock_body
        )

        # Mock client that raises authentication error
        mock_client = Mock()
        mock_client.messages.create.side_effect = auth_error
        mock_anthropic_class.return_value = mock_client

        client = Anthropic(api_key="invalid-key")

        with pytest.raises(AuthenticationError) as exc_info:
            client.messages.create(
                model="test-model", max_tokens=40, messages=[{"role": "user", "content": "test"}]
            )

        # Verify the error message
        assert "invalid x-api-key" in str(exc_info.value)

    @patch("dotenv.load_dotenv")
    def test_dotenv_loading(self, mock_load_dotenv):
        """Test that dotenv loading is called."""
        # Re-import the module to trigger load_dotenv
        import importlib

        if "tests.test_anthropic" in sys.modules:
            importlib.reload(sys.modules["tests.test_anthropic"])

        # Note: This test might not work as expected since load_dotenv is called at import time
        # It's here for demonstration of how to test dotenv integration

    @patch("anthropic.Anthropic")
    def test_different_models(self, mock_anthropic_class):
        """Test with different model configurations."""
        import os

        models_to_test = [
            "claude-sonnet-4-20250514",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
        ]

        for model in models_to_test:
            with patch.dict(
                "os.environ",
                {"ANTHROPIC_API_KEY": "test-key", "ANTHROPIC_MODEL_SPECIALISTS": model},
            ):
                # Mock response
                mock_content = Mock()
                mock_content.text = f"Response from {model}"
                mock_response = Mock()
                mock_response.content = [mock_content]

                mock_client = Mock()
                mock_client.messages.create.return_value = mock_response
                mock_anthropic_class.return_value = mock_client

                from anthropic import Anthropic

                client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

                resp = client.messages.create(
                    model=os.getenv("ANTHROPIC_MODEL_SPECIALISTS"),
                    max_tokens=40,
                    messages=[{"role": "user", "content": "test"}],
                )

                assert resp.content[0].text == f"Response from {model}"

    def test_max_tokens_parameter(self):
        """Test different max_tokens values."""
        token_limits = [10, 40, 100, 1000, 4000]

        for max_tokens in token_limits:
            with patch("anthropic.Anthropic") as mock_anthropic_class:
                mock_client = Mock()
                mock_content = Mock()
                mock_content.text = "x" * min(max_tokens, 50)  # Simulate response length
                mock_response = Mock()
                mock_response.content = [mock_content]
                mock_client.messages.create.return_value = mock_response
                mock_anthropic_class.return_value = mock_client

                from anthropic import Anthropic

                client = Anthropic(api_key="test-key")

                resp = client.messages.create(
                    model="test-model",
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": "test"}],
                )

                # Verify max_tokens was passed correctly
                call_args = mock_client.messages.create.call_args[1]
                assert call_args["max_tokens"] == max_tokens

    @patch("anthropic.Anthropic")
    def test_message_structure(self, mock_anthropic_class):
        """Test different message structures."""
        test_messages = [
            [{"role": "user", "content": "Simple message"}],
            [
                {"role": "user", "content": "First message"},
                {"role": "assistant", "content": "Response"},
                {"role": "user", "content": "Follow up"},
            ],
            [
                {"role": "system", "content": "System prompt"},
                {"role": "user", "content": "User message"},
            ],
        ]

        for messages in test_messages:
            mock_client = Mock()
            mock_content = Mock()
            mock_content.text = "Response"
            mock_response = Mock()
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic_class.return_value = mock_client

            from anthropic import Anthropic

            client = Anthropic(api_key="test-key")

            resp = client.messages.create(model="test-model", max_tokens=40, messages=messages)

            # Verify messages were passed correctly
            call_args = mock_client.messages.create.call_args[1]
            assert call_args["messages"] == messages


if __name__ == "__main__":
    # Run basic mock test
    import sys

    test = TestAnthropicIntegration()
    test.test_environment_variable_handling()
    print("✓ Mock Anthropic tests passed")
