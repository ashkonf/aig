import os
import pytest
from unittest.mock import patch, MagicMock
import aig
import aig.openai
from aig.openai import is_available, init, ask_openai


@pytest.fixture
def mock_aig_client():
    """Fixture to mock the aig.openai.client."""
    original_client = aig.openai.client
    mock_client = MagicMock()
    aig.openai.client = mock_client
    yield mock_client
    aig.openai.client = original_client


def test_ask_openai_returns_text(mock_aig_client):
    """Test that ask_openai returns the text from the response."""
    os.environ["OPENAI_API_KEY"] = "test-key"
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "  Test response  "
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_aig_client.chat.completions.create.return_value = mock_response
    response = ask_openai("Hello")
    assert response == "Test response"
    mock_aig_client.chat.completions.create.assert_called_once()


def test_ask_openai_returns_empty_string_for_no_content(mock_aig_client):
    """Test that ask_openai returns an empty string if there is no content."""
    os.environ["OPENAI_API_KEY"] = "test-key"
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = None
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_aig_client.chat.completions.create.return_value = mock_response
    response = ask_openai("Hello")
    assert response == ""
    mock_aig_client.chat.completions.create.assert_called_once()


def test_ask_openai_handles_api_error(mock_aig_client):
    """Test that ask_openai handles a generic API error."""
    os.environ["OPENAI_API_KEY"] = "test-key"
    mock_aig_client.chat.completions.create.side_effect = Exception("API error")
    with pytest.raises(Exception, match="API error"):
        ask_openai("Hello")


@pytest.fixture(autouse=True)
def clean_env_vars():
    """Fixture to clean up environment variables before and after tests."""
    original_environ = os.environ.copy()
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]
    yield
    os.environ.clear()
    os.environ.update(original_environ)


def test_is_available():
    """Test that is_available checks for the OPENAI_API_KEY environment variable."""
    os.environ["OPENAI_API_KEY"] = "test-key"
    assert is_available() is True
    del os.environ["OPENAI_API_KEY"]
    assert is_available() is False


def test_init_raises_error_if_no_key():
    """Test that init raises a SystemExit if the API key is not set."""
    with pytest.raises(SystemExit):
        init()


@patch("aig.openai.OpenAI")
def test_init_sets_client(mock_openai):
    """Test that init sets the client with the API key."""
    os.environ["OPENAI_API_KEY"] = "test-key"
    init()
    mock_openai.assert_called_with(api_key="test-key")


def test_ask_openai_raises_error_if_not_initialized():
    """Test that ask_openai raises an error if the client is not initialized."""
    with patch("aig.openai.client", None):
        with pytest.raises(Exception, match="OpenAI client not initialized"):
            ask_openai("Hello")
