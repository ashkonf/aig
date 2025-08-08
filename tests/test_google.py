import os
from unittest.mock import MagicMock
import pytest
from aig import google


def test_is_available_gemini(monkeypatch):
    """Test that is_available returns True when GEMINI_API_KEY is set."""
    monkeypatch.setenv("GEMINI_API_KEY", "test_key")
    assert google.is_available() is True


def test_is_available_google(monkeypatch):
    """Test that is_available returns True when GOOGLE_API_KEY is set."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key")
    assert google.is_available() is True


def test_is_not_available(monkeypatch):
    """Test that is_available returns False when no API key is set."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert google.is_available() is False


def test_init_exits_without_api_key(monkeypatch, mocker):
    """Test that init exits if no API key is set."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    mock_exit = mocker.patch("sys.exit")
    google.init()
    mock_exit.assert_called_once_with(
        "Google API key not found. Please set the relevant environment variable."
    )


def test_init_does_not_exit_with_api_key(monkeypatch):
    """Test that init does not exit if an API key is set."""
    monkeypatch.setenv("GEMINI_API_KEY", "test_key")
    try:
        google.init()
    except SystemExit:
        pytest.fail("init() exited unexpectedly")


@pytest.fixture
def mock_generative_model(mocker: MagicMock):
    """Fixture to mock the GenerativeModel class."""
    return mocker.patch("aig.google.genai.GenerativeModel")


def test_ask_gemini_with_code_block(mock_generative_model: MagicMock):
    """Test that ask_gemini correctly trims a code block with a language."""
    mock_model_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "```python\nprint('Hello, World!')\n```"
    mock_model_instance.generate_content.return_value = mock_response
    mock_generative_model.return_value = mock_model_instance
    response = google.ask_gemini("test prompt")
    assert response == "python\nprint('Hello, World!')"


def test_ask_gemini_with_code_block_no_lang(mock_generative_model: MagicMock):
    """Test that ask_gemini correctly trims a code block without a language."""
    mock_model_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "```\nprint('Hello, World!')\n```"
    mock_model_instance.generate_content.return_value = mock_response
    mock_generative_model.return_value = mock_model_instance
    response = google.ask_gemini("test prompt")
    assert response == "print('Hello, World!')"


def test_ask_gemini_without_code_block(mock_generative_model: MagicMock):
    """Test that ask_gemini returns the text as is when no code block is present."""
    mock_model_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Hello, World!"
    mock_model_instance.generate_content.return_value = mock_response
    mock_generative_model.return_value = mock_model_instance
    response = google.ask_gemini("test prompt")
    assert response == "Hello, World!"


def test_ask_gemini_empty_response(mock_generative_model: MagicMock):
    """Test that ask_gemini handles an empty response."""
    mock_model_instance = MagicMock()
    mock_response = MagicMock()
    mock_generative_model.return_value = mock_model_instance
    mock_model_instance.generate_content.return_value = mock_response

    # Test with empty string
    mock_response.text = ""
    response = google.ask_gemini("test prompt")
    assert response == ""

    # Test with None
    mock_response.text = None
    response = google.ask_gemini("test prompt")
    assert response == ""

    # Test with no text attribute
    del mock_response.text
    response = google.ask_gemini("test prompt")
    assert response == ""


def test_ask_gemini_api_key_error(mock_generative_model: MagicMock):
    """Test that ask_gemini handles an invalid API key error."""
    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.side_effect = Exception("API key not valid")
    mock_generative_model.return_value = mock_model_instance
    with pytest.raises(
        Exception, match="Gemini API key is not valid. Please check your .env file."
    ):
        google.ask_gemini("test prompt")


def test_ask_gemini_generic_error(mock_generative_model: MagicMock):
    """Test that ask_gemini handles a generic API error."""
    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.side_effect = Exception("Generic error")
    mock_generative_model.return_value = mock_model_instance
    with pytest.raises(Exception, match="Gemini API error: Generic error"):
        google.ask_gemini("test prompt")


def test_model_name_from_env(mock_generative_model: MagicMock, monkeypatch: MagicMock):
    """Test that the model name is taken from the environment variable."""
    monkeypatch.setenv("MODEL_NAME", "test-model")
    google.ask_gemini("test prompt")
    mock_generative_model.assert_called_with("test-model")


# --- Live integration tests moved from tests/test_google_integration.py ---
integration = pytest.mark.integration
skip_if_no_key = pytest.mark.skipif(
    os.getenv("GOOGLE_API_KEY") is None and os.getenv("GEMINI_API_KEY") is None,
    reason="GOOGLE_API_KEY/GEMINI_API_KEY not set; skipping live Gemini integration tests",
)


@integration
@skip_if_no_key
def test_gemini_init_available(monkeypatch: pytest.MonkeyPatch):
    # Prefer a faster/cheaper model for live tests if available
    monkeypatch.setenv("MODEL_NAME", os.getenv("MODEL_NAME", "gemini-1.5-flash-latest"))
    assert google.is_available() is True
    # Should not exit when a key is present
    google.init()


@integration
@skip_if_no_key
def test_gemini_ask_live(monkeypatch: pytest.MonkeyPatch):
    # Prefer a faster/cheaper model for live tests if available
    monkeypatch.setenv("MODEL_NAME", os.getenv("MODEL_NAME", "gemini-1.5-flash-latest"))
    google.init()
    response = google.ask_gemini("Respond with exactly: PONG", max_tokens=10)
    assert isinstance(response, str)
    assert "pong" in response.strip().lower()
