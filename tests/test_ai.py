import os
import importlib
from unittest.mock import patch
import pytest

from aig.ai import (
    commit_message_from_diff,
    stash_name_from_diff,
    summarize_commit_log,
    explain_blame_output,
    code_review_from_diff,
)


@pytest.fixture
def mock_ask():
    with patch("aig.ai.ask") as mock:
        yield mock


# Basic AI wrapper tests (moved from test_init.py)
def test_commit_message_from_diff(mock_ask):
    mock_ask.return_value = "commit message"
    diff = "test diff"
    result = commit_message_from_diff(diff)
    assert result == "commit message"
    mock_ask.assert_called_once()
    assert diff in mock_ask.call_args[0][0]
    assert "commit message" in mock_ask.call_args[0][0]


def test_stash_name_from_diff(mock_ask):
    mock_ask.return_value = "stash name"
    diff = "test diff"
    result = stash_name_from_diff(diff)
    assert result == "stash name"
    mock_ask.assert_called_once()
    assert diff in mock_ask.call_args[0][0]
    assert "stash message" in mock_ask.call_args[0][0]


def test_summarize_commit_log(mock_ask):
    mock_ask.return_value = "summary"
    log = "test log"
    result = summarize_commit_log(log)
    assert result == "summary"
    mock_ask.assert_called_once()
    assert log in mock_ask.call_args[0][0]
    assert "Summarize" in mock_ask.call_args[0][0]


def test_explain_blame_output(mock_ask):
    mock_ask.return_value = "explanation"
    blame = "test blame"
    result = explain_blame_output(blame)
    assert result == "explanation"
    mock_ask.assert_called_once()
    assert blame in mock_ask.call_args[0][0]
    assert "Explain why this line was changed" in mock_ask.call_args[0][0]


def test_code_review_from_diff(mock_ask):
    mock_ask.return_value = "review"
    diff = "test diff"
    result = code_review_from_diff(diff)
    assert result == "review"
    mock_ask.assert_called_once()
    assert diff in mock_ask.call_args[0][0]
    assert "Review the following code changes" in mock_ask.call_args[0][0]


# Edge-case AI wrapper tests (moved from test_edge_cases_comprehensive.py)
class TestAIWrappers:
    @patch("aig.ai.ask", return_value="✨ Add new feature")
    def test_commit_message_from_diff_with_unicode(self, mock_ask):
        diff = "diff --git a/file.py\n+print('Hello 🌍')"
        result = commit_message_from_diff(diff)
        assert result == "✨ Add new feature"
        mock_ask.assert_called_once()

    @patch("aig.ai.ask", return_value="")
    def test_commit_message_from_diff_empty_response(self, mock_ask):
        diff = "simple diff"
        result = commit_message_from_diff(diff)
        assert result == ""

    @patch("aig.ai.ask", return_value="🔧 Fix configuration")
    def test_stash_name_from_diff_normal(self, mock_ask):
        diff = "diff --git a/config.py"
        result = stash_name_from_diff(diff)
        assert result == "🔧 Fix configuration"

    @patch("aig.ai.ask", return_value="• Feature A\n• Bug fix B")
    def test_summarize_commit_log_multiline(self, mock_ask):
        log = "abc123 Add feature A\ndef456 Fix bug B"
        result = summarize_commit_log(log)
        assert result == "• Feature A\n• Bug fix B"

    @patch("aig.ai.ask", return_value="🔍 This change improves performance")
    def test_explain_blame_output_normal(self, mock_ask):
        blame = "abc123 (author@email.com 2024-01-01) line content"
        result = explain_blame_output(blame)
        assert result == "🔍 This change improves performance"

    @patch("aig.ai.ask", return_value="✅ Code looks good!")
    def test_code_review_from_diff_positive(self, mock_ask):
        diff = "diff --git a/test.py\n+def test_function():"
        result = code_review_from_diff(diff)
        assert result == "✅ Code looks good!"


# Provider selection and error scenarios (moved)
@patch("os.getenv")
def test_unknown_provider(mock_getenv):
    mock_getenv.side_effect = lambda key: "unknown" if key == "PROVIDER" else None
    with pytest.raises(SystemExit):
        import aig.ai

        importlib.reload(aig.ai)


@patch.dict(os.environ, {}, clear=True)
@patch("aig.google.is_available", return_value=False)
@patch("aig.openai.is_available", return_value=False)
@patch("aig.anthropic.is_available", return_value=False)
def test_no_api_keys_available(
    _mock_anthropic_avail, _mock_openai_avail, _mock_google_avail
):
    with pytest.raises(SystemExit) as excinfo:
        import aig.ai

        importlib.reload(aig.ai)
    assert "No API keys found in environment variables" in str(excinfo.value)


class TestAPIProviderInitialization:
    @patch.dict(os.environ, {}, clear=True)
    @patch("aig.google.is_available", return_value=False)
    @patch("aig.openai.is_available", return_value=True)
    @patch("aig.anthropic.is_available", return_value=False)
    @patch("aig.openai.init")
    def test_openai_provider_initialization(
        self,
        mock_openai_init,
        _mock_anthropic_avail,
        _mock_openai_avail,
        _mock_google_avail,
    ):
        import aig.ai as ai_mod

        importlib.reload(ai_mod)
        mock_openai_init.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)
    @patch("aig.google.is_available", return_value=False)
    @patch("aig.openai.is_available", return_value=False)
    @patch("aig.anthropic.is_available", return_value=True)
    @patch("aig.anthropic.init")
    def test_anthropic_provider_initialization(
        self,
        mock_anthropic_init,
        _mock_anthropic_avail,
        _mock_openai_avail,
        _mock_google_avail,
    ):
        import aig.ai as ai_mod

        importlib.reload(ai_mod)
        mock_anthropic_init.assert_called_once()


# Additional AI behavior tests (moved)
@patch("aig.ai.ask", return_value="🚀 添加新功能")
def test_commit_message_with_unicode(mock_ask):
    diff = "diff --git a/文件.py\n+print('你好世界')"
    result = commit_message_from_diff(diff)
    assert result == "🚀 添加新功能"


@patch("aig.ai.ask", return_value="Long response" * 100)
def test_long_diff_input(mock_ask):
    long_diff = "+" + "x" * 10000
    result = commit_message_from_diff(long_diff)
    assert len(result) > 0


class TestEnvironmentVariables:
    @patch.dict(os.environ, {"MODEL_NAME": "custom-model"}, clear=False)
    @patch("aig.ai.ask")
    def test_custom_model_name(self, mock_ask):
        commit_message_from_diff("test diff")
        mock_ask.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)
    @patch("aig.ai.ask")
    def test_default_model_name(self, mock_ask):
        commit_message_from_diff("test diff")
        mock_ask.assert_called_once()
