import os
import pytest
from unittest.mock import patch, MagicMock
from anthropic.types import TextBlock
import aig
import aig.anthropic
from aig.anthropic import is_available, init, ask_anthropic


@pytest.fixture
def mock_aig_client():
    """Fixture to mock the aig.anthropic.client."""
    original_client = aig.anthropic.client
    mock_client = MagicMock()
    aig.anthropic.client = mock_client
    yield mock_client
    aig.anthropic.client = original_client


def test_ask_anthropic_returns_text(mock_aig_client):
    """Test that ask_anthropic returns the text from the response."""
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    mock_response = MagicMock()
    mock_text_block = MagicMock(spec=TextBlock)
    mock_text_block.text = "  Test response  "
    mock_response.content = [mock_text_block]
    mock_aig_client.messages.create.return_value = mock_response
    response = ask_anthropic("Hello")
    assert response == "Test response"
    mock_aig_client.messages.create.assert_called_once()


def test_ask_anthropic_no_text_block(mock_aig_client):
    """Test that ask_anthropic raises an exception if no text block is found."""
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    mock_response = MagicMock()
    mock_response.content = []
    mock_aig_client.messages.create.return_value = mock_response
    with pytest.raises(Exception, match="No text block found in response"):
        ask_anthropic("Hello")


def test_ask_anthropic_handles_api_error_invalid_key(mock_aig_client):
    """Test that ask_anthropic handles an invalid API key error."""
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    mock_aig_client.messages.create.side_effect = Exception("API key not valid")
    with pytest.raises(
        Exception, match="Anthropic API key is not valid. Please check your .env file."
    ):
        ask_anthropic("Hello")


def test_ask_anthropic_handles_api_error(mock_aig_client):
    """Test that ask_anthropic handles a generic API error."""
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    mock_aig_client.messages.create.side_effect = Exception("API error")
    with pytest.raises(Exception, match="API error"):
        ask_anthropic("Hello")


@pytest.fixture(autouse=True)
def clean_env_vars():
    """Fixture to clean up environment variables before and after tests."""
    original_environ = os.environ.copy()
    if "ANTHROPIC_API_KEY" in os.environ:
        del os.environ["ANTHROPIC_API_KEY"]
    yield
    os.environ.clear()
    os.environ.update(original_environ)


def test_is_available():
    """Test that is_available checks for the ANTHROPIC_API_KEY environment variable."""
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    assert is_available() is True
    del os.environ["ANTHROPIC_API_KEY"]
    assert is_available() is False


def test_init_raises_error_if_no_key():
    """Test that init raises a SystemExit if the API key is not set."""
    with pytest.raises(SystemExit):
        init()


@patch("aig.anthropic.Anthropic")
def test_init_sets_client(mock_anthropic):
    """Test that init sets the client with the API key."""
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    init()
    mock_anthropic.assert_called_with(api_key="test-key")


def test_ask_anthropic_raises_error_if_not_initialized():
    """Test that ask_anthropic raises an error if the client is not initialized."""
    with patch("aig.anthropic.client", None):
        with pytest.raises(Exception, match="Anthropic client not initialized"):
            ask_anthropic("Hello")


def test_ask_anthropic_with_non_text_block(mock_aig_client):
    """Test ask_anthropic with a block that is not a TextBlock."""
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_aig_client.messages.create.return_value = mock_response
    with pytest.raises(Exception, match="No text block found in response"):
        ask_anthropic("Hello")


def test_ask_anthropic_with_model_name_env_var(mock_aig_client):
    """Test that ask_anthropic uses the model name from the environment variable."""
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    os.environ["MODEL_NAME"] = "my-custom-model"
    mock_response = MagicMock()
    mock_text_block = MagicMock(spec=TextBlock)
    mock_text_block.text = "  Test response  "
    mock_response.content = [mock_text_block]
    mock_aig_client.messages.create.return_value = mock_response
    ask_anthropic("Hello")
    mock_aig_client.messages.create.assert_called_with(
        model="my-custom-model",
        max_tokens=400,
        temperature=0.3,
        messages=[{"role": "user", "content": "Hello"}],
    )
