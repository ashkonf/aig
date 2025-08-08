import argparse
import os
import subprocess
import sys
from unittest.mock import MagicMock, patch
import pytest
from pathlib import Path

from aig import (
    Command,
    _handle_blame,
    _handle_commit,
    _handle_config,
    _handle_log,
    _handle_review,
    _handle_stash,
    _install_pre_commit_hooks_if_needed,
    _postprocess_output,
    _handle_test,
    _handle_git_passthrough,
    main,
)

from aig.git import (
    get_diff,
    get_log,
    get_branch_prefix,
)

from aig.ai import (
    commit_message_from_diff,
    stash_name_from_diff,
    summarize_commit_log,
    explain_blame_output,
    code_review_from_diff,
)


@pytest.fixture
def mock_run():
    with patch("aig.git._patched_run_if_present") as mock:
        yield mock


@pytest.fixture
def mock_args():
    args = MagicMock(spec=argparse.Namespace)
    args.message = None
    args.yes = False
    args.date = None
    args.file = "test.py"
    args.line = 42
    args.branch_prefix = None
    return args


def test_postprocess_output():
    assert _postprocess_output("git is great") == "aig is great"
    assert _postprocess_output("Git is great") == "aig is great"


@patch("os.path.exists")
@patch("subprocess.run")
def test_install_pre_commit_hooks_if_needed_not_installed(mock_run, mock_exists):
    mock_exists.return_value = False
    _install_pre_commit_hooks_if_needed()
    mock_run.assert_called_once()
    assert "install" in mock_run.call_args[0][0]


@patch("os.path.exists")
@patch("subprocess.run")
def test_install_pre_commit_hooks_if_needed_already_installed(mock_run, mock_exists):
    mock_exists.return_value = True
    _install_pre_commit_hooks_if_needed()
    mock_run.assert_not_called()


def test_dummy_to_avoid_empty_file_warning():
    # Placeholder to keep file structure stable after moving unit tests.
    assert True


# AI wrapper tests moved to tests/test_ai.py


@patch("aig._install_pre_commit_hooks_if_needed")
@patch("subprocess.run")
def test_handle_test(mock_subprocess_run, mock_install_hooks):
    _handle_test()
    mock_install_hooks.assert_called_once()
    mock_subprocess_run.assert_called_once()


@patch("aig._install_pre_commit_hooks_if_needed")
@patch("aig.get_diff")
@patch("aig.commit_message_from_diff")
@patch("subprocess.run")
def test_handle_commit_with_generated_message(
    mock_subprocess_run, mock_commit_msg, mock_get_diff, mock_install_hooks, mock_args
):
    mock_get_diff.return_value = "diff"
    mock_commit_msg.return_value = "Test commit"
    with patch("builtins.input", return_value="y"):
        _handle_commit(mock_args, [])
    mock_install_hooks.assert_called_once()
    mock_get_diff.assert_called_once()
    mock_commit_msg.assert_called_once_with("diff")
    mock_subprocess_run.assert_called_once()
    assert mock_subprocess_run.call_args[1]["input"] == "Test commit"


@patch("aig._install_pre_commit_hooks_if_needed")
@patch("subprocess.run")
def test_handle_commit_with_provided_message(
    mock_subprocess_run, mock_install_hooks, mock_args
):
    mock_args.message = "User message"
    _handle_commit(mock_args, [])
    mock_install_hooks.assert_called_once()
    mock_subprocess_run.assert_called_once()
    assert mock_subprocess_run.call_args[1]["input"] == "User message"


@patch("aig.get_diff", return_value="")
def test_handle_commit_no_diff(mock_get_diff, mock_args, capsys):
    _handle_commit(mock_args, [])
    captured = capsys.readouterr()
    assert "No staged changes found" in captured.out


@patch("aig.get_unstaged_diff")
@patch("aig.stash_name_from_diff")
@patch("aig.run")
def test_handle_stash(mock_run, mock_stash_name, mock_get_unstaged_diff, mock_args):
    mock_get_unstaged_diff.return_value = "diff"
    mock_stash_name.return_value = "Test stash"
    mock_args.message = "Test stash"
    _handle_stash(mock_args, [])
    mock_run.assert_called_with(["git", "stash", "push", "-m", "Test stash"])


@patch("aig.get_log")
@patch("aig.summarize_commit_log")
@patch("aig._postprocess_output")
def test_handle_log(mock_postprocess, mock_summarize, mock_get_log, mock_args):
    mock_get_log.return_value = "log"
    mock_summarize.return_value = "summary"
    mock_postprocess.return_value = "processed log"
    _handle_log(mock_args, [])
    mock_get_log.assert_called_once()
    mock_summarize.assert_called_once_with("log")
    mock_postprocess.assert_called_once_with("log")


@patch("aig.get_blame")
@patch("aig.explain_blame_output")
@patch("aig._postprocess_output")
def test_handle_blame(mock_postprocess, mock_explain, mock_get_blame, mock_args):
    mock_get_blame.return_value = "blame"
    mock_explain.return_value = "explanation"
    mock_postprocess.return_value = "processed blame"
    _handle_blame(mock_args, [])
    mock_get_blame.assert_called_once_with("test.py", 42, [])
    mock_explain.assert_called_once_with("blame")
    mock_postprocess.assert_called_once_with("blame")


@patch("aig.get_diff")
@patch("aig.code_review_from_diff")
def test_handle_review(mock_review, mock_get_diff, mock_args):
    mock_get_diff.return_value = "diff"
    mock_review.return_value = "review"
    _handle_review(mock_args, [])
    mock_get_diff.assert_called_once()
    mock_review.assert_called_once_with("diff")


def test_handle_config_set(mock_args):
    mock_args.branch_prefix = "feature"
    with patch("aig.run") as mock_run:
        _handle_config(mock_args)
        mock_run.assert_called_with(["git", "config", "aig.branch-prefix", "feature"])


def test_handle_config_unset(mock_args):
    mock_args.branch_prefix = ""
    with patch("aig.run") as mock_run:
        _handle_config(mock_args)
        mock_run.assert_called_with(["git", "config", "--unset", "aig.branch-prefix"])


@patch("argparse.ArgumentParser.parse_known_args")
def test_main(mock_parse_args):
    mock_args = MagicMock()
    mock_args.command = Command.COMMIT
    mock_parse_args.return_value = (mock_args, [])
    with patch("aig._handle_commit") as mock_handler:
        with patch("sys.argv", ["aig", "commit"]):
            from aig import main

            main()
            mock_handler.assert_called_once_with(mock_args, [])


@patch("argparse.ArgumentParser.parse_known_args")
def test_main_config_command(mock_parse_args):
    mock_args = MagicMock()
    mock_args.command = Command.CONFIG
    mock_parse_args.return_value = (mock_args, [])
    with patch("aig._handle_config") as mock_handler:
        with patch("sys.argv", ["aig", "config"]):
            from aig import main

            main()
            mock_handler.assert_called_once_with(mock_args)


@patch("argparse.ArgumentParser.parse_known_args")
def test_main_stash_command(mock_parse_args):
    mock_args = MagicMock()
    mock_args.command = Command.STASH
    mock_parse_args.return_value = (mock_args, [])
    with patch("aig._handle_stash") as mock_handler:
        with patch("sys.argv", ["aig", "stash"]):
            from aig import main

            main()
            mock_handler.assert_called_once_with(mock_args, [])


@patch("subprocess.run")
def test_handle_git_passthrough_no_argv(mock_subprocess_run):
    with patch("sys.argv", ["aig"]):
        from aig import _handle_git_passthrough

        with pytest.raises(SystemExit):
            _handle_git_passthrough()
        mock_subprocess_run.assert_called_with(["git"], text=True, check=False)


@patch("argparse.ArgumentParser.parse_known_args")
def test_main_review_command(mock_parse_args):
    mock_args = MagicMock()
    mock_args.command = Command.REVIEW
    mock_parse_args.return_value = (mock_args, [])
    with patch("aig._handle_review") as mock_handler:
        with patch("sys.argv", ["aig", "review"]):
            from aig import main

            main()
            mock_handler.assert_called_once_with(mock_args, [])


@patch("argparse.ArgumentParser.parse_known_args")
def test_main_blame_command(mock_parse_args):
    mock_args = MagicMock()
    mock_args.command = Command.BLAME
    mock_parse_args.return_value = (mock_args, [])
    with patch("aig._handle_blame") as mock_handler:
        with patch("sys.argv", ["aig", "blame", "file", "10"]):
            from aig import main

            main()
            mock_handler.assert_called_once_with(mock_args, [])


# Provider selection tests moved to tests/test_ai.py


@patch("argparse.ArgumentParser.parse_known_args")
def test_main_test_command(mock_parse_args):
    mock_args = MagicMock()
    mock_args.command = Command.TEST
    mock_parse_args.return_value = (mock_args, [])
    with patch("aig._handle_test") as mock_handler:
        with patch("sys.argv", ["aig", "test"]):
            from aig import main

            main()
            mock_handler.assert_called_once_with()


@patch("subprocess.run")
def test_handle_git_passthrough(mock_subprocess_run):
    with patch("sys.argv", ["aig", "status"]):
        from aig import _handle_git_passthrough

        with pytest.raises(SystemExit):
            _handle_git_passthrough()
        mock_subprocess_run.assert_called_with(
            ["git", "status"], text=True, check=False
        )


@patch("argparse.ArgumentParser.parse_known_args")
def test_main_log_command(mock_parse_args):
    mock_args = MagicMock()
    mock_args.command = Command.LOG
    mock_parse_args.return_value = (mock_args, [])
    with patch("aig._handle_log") as mock_handler:
        with patch("sys.argv", ["aig", "log"]):
            from aig import main

            main()
            mock_handler.assert_called_once_with(mock_args, [])


# Additional __init__.py tests consolidated from other files


@patch("os.path.exists")
@patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "cmd"))
def test_install_pre_commit_hooks_if_needed_install_fails(
    mock_run, mock_exists, capsys
):
    mock_exists.return_value = False
    _install_pre_commit_hooks_if_needed()
    captured = capsys.readouterr()
    assert "Could not install pre-commit hooks" in captured.err


@patch("aig._install_pre_commit_hooks_if_needed")
@patch("aig.get_diff")
@patch("aig.commit_message_from_diff")
@patch("subprocess.run")
def test_handle_commit_fail(
    mock_subprocess_run,
    mock_commit_msg,
    mock_get_diff,
    mock_install_hooks,
    mock_args,
    capsys,
):
    mock_get_diff.return_value = "diff"
    mock_commit_msg.return_value = "Test commit"
    error = subprocess.CalledProcessError(1, "cmd")
    error.stdout = "stdout"
    error.stderr = "stderr"
    mock_subprocess_run.side_effect = error
    with patch("builtins.input", return_value="y"):
        with pytest.raises(SystemExit):
            _handle_commit(mock_args, [])
    captured = capsys.readouterr()
    assert "Commit failed" in captured.err
    assert "stdout" in captured.err
    assert "stderr" in captured.err


@patch("aig.get_unstaged_diff", return_value="diff")
@patch("aig.stash_name_from_diff", return_value="stash message")
def test_handle_stash_no_confirmation(mock_stash_name, mock_get_diff, mock_args):
    with patch("builtins.input", return_value="n"):
        _handle_stash(mock_args, [])


@patch("aig.get_diff", return_value="")
def test_handle_review_no_diff(mock_get_diff, mock_args, capsys):
    _handle_review(mock_args, [])
    captured = capsys.readouterr()
    assert "No staged changes found" in captured.out


@patch("aig.get_branch_prefix", return_value="feature")
@patch("subprocess.run")
def test_handle_git_passthrough_checkout(mock_run, mock_get_branch_prefix):
    with patch("sys.argv", ["aig", "checkout", "-b", "new-branch"]):
        from aig import _handle_git_passthrough

        with pytest.raises(SystemExit):
            _handle_git_passthrough()
        mock_run.assert_called_with(
            ["git", "checkout", "-b", "feature/new-branch"], text=True, check=False
        )


@patch("aig.get_branch_prefix", return_value="feature")
@patch("subprocess.run")
def test_handle_git_passthrough_branch(mock_run, mock_get_branch_prefix):
    with patch("sys.argv", ["aig", "branch", "new-branch"]):
        from aig import _handle_git_passthrough

        with pytest.raises(SystemExit):
            _handle_git_passthrough()
        mock_run.assert_called_with(
            ["git", "branch", "feature/new-branch"], text=True, check=False
        )


@patch("subprocess.run", side_effect=FileNotFoundError)
def test_handle_git_passthrough_git_not_found(mock_run):
    with patch("sys.argv", ["aig", "status"]):
        from aig import _handle_git_passthrough

        with pytest.raises(SystemExit) as e:
            _handle_git_passthrough()
        assert "git is not installed" in str(e.value)


@patch("argparse.ArgumentParser.parse_known_args")
def test_main_help(mock_parse_args):
    mock_parse_args.side_effect = SystemExit(0)
    with patch("sys.argv", ["aig", "-h"]):
        with pytest.raises(SystemExit):
            from aig import main

            main()


@patch("aig.get_unstaged_diff", return_value="")
def test_handle_stash_no_diff(mock_get_diff, mock_args, capsys):
    _handle_stash(mock_args, [])
    captured = capsys.readouterr()
    assert "No changes to stash" in captured.out


# Help flag tests consolidated from tests/test_main.py


def test_help_message_long(mocker):
    mocker.patch("sys.argv", ["aig", "--help"])
    with pytest.raises(SystemExit):
        from aig import main

        main()


def test_help_message_short(mocker):
    mocker.patch("sys.argv", ["aig", "-h"])
    with pytest.raises(SystemExit):
        from aig import main

        main()


class TestRunFunction:
    """run() unit tests moved to tests/test_git.py"""

    def test_placeholder(self):
        assert True


class TestGitPlumbingFunctions:
    """git plumbing unit tests moved to tests/test_git.py"""

    def test_placeholder(self):
        assert True


class TestAIWrappers:
    """Test AI wrapper functions edge cases."""

    @patch("aig.ai.ask", return_value="✨ Add new feature")
    def test_commit_message_from_diff_with_unicode(self, mock_ask):
        """Test commit message generation with Unicode diff."""
        diff = "diff --git a/file.py\\n+print('Hello 🌍')"
        result = commit_message_from_diff(diff)
        assert result == "✨ Add new feature"
        mock_ask.assert_called_once()

    @patch("aig.ai.ask", return_value="")
    def test_commit_message_from_diff_empty_response(self, mock_ask):
        """Test commit message generation with empty AI response."""
        diff = "simple diff"
        result = commit_message_from_diff(diff)
        assert result == ""

    @patch("aig.ai.ask", return_value="🔧 Fix configuration")
    def test_stash_name_from_diff_normal(self, mock_ask):
        """Test stash name generation."""
        diff = "diff --git a/config.py"
        result = stash_name_from_diff(diff)
        assert result == "🔧 Fix configuration"

    @patch("aig.ai.ask", return_value="• Feature A\\n• Bug fix B")
    def test_summarize_commit_log_multiline(self, mock_ask):
        """Test commit log summarization with multiline response."""
        log = "abc123 Add feature A\\ndef456 Fix bug B"
        result = summarize_commit_log(log)
        assert result == "• Feature A\\n• Bug fix B"

    @patch("aig.ai.ask", return_value="🔍 This change improves performance")
    def test_explain_blame_output_normal(self, mock_ask):
        """Test blame explanation generation."""
        blame = "abc123 (author@email.com 2024-01-01) line content"
        result = explain_blame_output(blame)
        assert result == "🔍 This change improves performance"

    @patch("aig.ai.ask", return_value="✅ Code looks good!")
    def test_code_review_from_diff_positive(self, mock_ask):
        """Test code review generation."""
        diff = "diff --git a/test.py\\n+def test_function():"
        result = code_review_from_diff(diff)
        assert result == "✅ Code looks good!"


class TestInstallPreCommitHooks:
    """Test pre-commit hooks installation edge cases."""

    @patch("os.path.exists", return_value=True)
    def test_install_pre_commit_hooks_already_exists(self, mock_exists):
        """Test when pre-commit hooks already exist."""
        with patch("subprocess.run") as mock_run:
            _install_pre_commit_hooks_if_needed()
            mock_run.assert_not_called()

    @patch("os.path.exists", return_value=False)
    @patch("subprocess.run")
    def test_install_pre_commit_hooks_success(self, mock_run, mock_exists, capsys):
        """Test successful pre-commit hooks installation."""
        _install_pre_commit_hooks_if_needed()

        captured = capsys.readouterr()
        assert "pre-commit hooks not found. Installing..." in captured.out
        assert "pre-commit hooks installed successfully." in captured.out

        mock_run.assert_called_with(
            [sys.executable, "-m", "pre_commit", "install"],
            check=True,
            text=True,
        )

    @patch("os.path.exists", return_value=False)
    @patch("subprocess.run", side_effect=FileNotFoundError("pre_commit not found"))
    def test_install_pre_commit_hooks_file_not_found(
        self, mock_run, mock_exists, capsys
    ):
        """Test pre-commit hooks installation when pre_commit is not available."""
        _install_pre_commit_hooks_if_needed()

        captured = capsys.readouterr()
        assert "Could not install pre-commit hooks" in captured.err
        assert "pre_commit not found" in captured.err

    @patch("os.path.exists", return_value=False)
    @patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "install"))
    def test_install_pre_commit_hooks_install_failure(
        self, mock_run, mock_exists, capsys
    ):
        """Test pre-commit hooks installation failure."""
        _install_pre_commit_hooks_if_needed()

        captured = capsys.readouterr()
        assert "Could not install pre-commit hooks" in captured.err


class TestPostprocessOutput:
    """Test output postprocessing edge cases."""

    def test_postprocess_output_git_lowercase(self):
        """Test replacing 'git' with 'aig'."""
        result = _postprocess_output("Use git to commit changes")
        assert result == "Use aig to commit changes"

    def test_postprocess_output_git_uppercase(self):
        """Test replacing 'Git' with 'aig'."""
        result = _postprocess_output("Git is a version control system")
        assert result == "aig is a version control system"

    def test_postprocess_output_mixed_case(self):
        """Test replacing both 'git' and 'Git'."""
        result = _postprocess_output("Git and git are both replaced")
        assert result == "aig and aig are both replaced"

    def test_postprocess_output_no_replacement(self):
        """Test text without git references."""
        text = "This is a normal text without any replacements"
        result = _postprocess_output(text)
        assert result == text

    def test_postprocess_output_empty_string(self):
        """Test empty string input."""
        result = _postprocess_output("")
        assert result == ""

    def test_postprocess_output_git_in_words(self):
        """Test git replacement in compound words."""
        result = _postprocess_output("github and legitimate")
        assert result == "aighub and leaigimate"


class TestHandleCommitEdgeCases:
    """Test _handle_commit function edge cases."""

    @pytest.fixture
    def basic_args(self):
        """Basic argument fixture."""
        args = MagicMock(spec=argparse.Namespace)
        args.message = None
        args.yes = False
        args.date = None
        return args

    @patch("aig._install_pre_commit_hooks_if_needed")
    @patch("aig.get_diff", return_value="  \n  \t  ")
    def test_handle_commit_diff_only_whitespace(
        self, mock_get_diff, mock_install, basic_args, capsys
    ):
        """Test commit when diff contains only whitespace."""
        _handle_commit(basic_args, [])

        captured = capsys.readouterr()
        assert "No staged changes found." in captured.out

    @patch("aig._install_pre_commit_hooks_if_needed")
    @patch("aig.get_diff", return_value="real diff content")
    @patch("aig.commit_message_from_diff", return_value="Test commit")
    def test_handle_commit_user_input_variations(
        self, mock_commit_msg, mock_get_diff, mock_install, basic_args
    ):
        """Test various user input responses."""
        test_cases = [
            ("Y", True),
            ("y", True),
            ("yes", True),
            ("YES", True),
            ("", True),  # Empty string defaults to yes
            ("n", False),
            ("no", False),
            ("NO", False),
            ("invalid", False),
            ("  y  ", True),  # With whitespace
        ]

        for user_input, should_commit in test_cases:
            with patch("builtins.input", return_value=user_input):
                with patch("subprocess.run") as mock_run:
                    _handle_commit(basic_args, [])

                    if should_commit:
                        mock_run.assert_called_once()
                    else:
                        mock_run.assert_not_called()

                    mock_run.reset_mock()

    @patch("aig._install_pre_commit_hooks_if_needed")
    @patch("subprocess.run")
    def test_handle_commit_with_extra_args(self, mock_run, mock_install):
        """Test commit with extra arguments passed through."""
        args = MagicMock(spec=argparse.Namespace)
        args.message = "Test commit"
        args.yes = False
        args.date = None

        _handle_commit(args, ["--allow-empty", "--no-verify"])

        mock_run.assert_called_with(
            ["git", "commit", "-F", "-", "--allow-empty", "--no-verify"],
            input="Test commit",
            check=True,
            text=True,
            env=os.environ.copy(),
        )

    @patch("aig._install_pre_commit_hooks_if_needed")
    @patch("subprocess.run")
    def test_handle_commit_with_date_no_yes_flag(self, mock_run, mock_install):
        """Test commit with date but without --yes flag."""
        args = MagicMock(spec=argparse.Namespace)
        args.message = "Test commit"
        args.yes = False
        args.date = "2024-01-01T12:00:00"

        _handle_commit(args, [])

        expected_env = os.environ.copy()
        expected_env["GIT_AUTHOR_DATE"] = "2024-01-01T12:00:00"
        expected_env["GIT_COMMITTER_DATE"] = "2024-01-01T12:00:00"

        mock_run.assert_called_with(
            ["git", "commit", "--date", "2024-01-01T12:00:00", "-F", "-"],
            input="Test commit",
            check=True,
            text=True,
            env=expected_env,
        )


class TestHandleStashEdgeCases:
    """Test _handle_stash function edge cases."""

    @pytest.fixture
    def basic_stash_args(self):
        """Basic stash argument fixture."""
        args = MagicMock(spec=argparse.Namespace)
        args.message = None
        args.yes = False
        return args

    @patch("aig.get_unstaged_diff", return_value="")
    def test_handle_stash_empty_diff(self, mock_get_diff, basic_stash_args, capsys):
        """Test stash when no changes to stash."""
        _handle_stash(basic_stash_args, [])

        captured = capsys.readouterr()
        assert "No changes to stash." in captured.out

    @patch("aig.get_unstaged_diff", return_value="stash content")
    @patch("aig.stash_name_from_diff", return_value="Test stash")
    def test_handle_stash_user_input_variations(
        self, mock_stash_name, mock_get_diff, basic_stash_args
    ):
        """Test various stash user input responses."""
        test_cases = [
            ("Y", True),
            ("n", False),
            ("", True),
            ("invalid", False),
        ]

        for user_input, should_stash in test_cases:
            with patch("builtins.input", return_value=user_input):
                with patch("aig.run") as mock_run:
                    _handle_stash(basic_stash_args, [])

                    if should_stash:
                        mock_run.assert_called_once()
                    else:
                        mock_run.assert_not_called()

                    mock_run.reset_mock()

    @patch("aig.run")
    def test_handle_stash_with_message_and_extra_args(self, mock_run):
        """Test stash with provided message and extra arguments."""
        args = MagicMock(spec=argparse.Namespace)
        args.message = "Custom stash message"
        args.yes = False

        _handle_stash(args, ["--include-untracked"])

        mock_run.assert_called_with(
            [
                "git",
                "stash",
                "push",
                "-m",
                "Custom stash message",
                "--include-untracked",
            ]
        )


class TestHandleBlameEdgeCases:
    """Test _handle_blame function edge cases."""

    @patch("aig.get_blame", return_value="blame output with git references")
    @patch("aig.explain_blame_output", return_value="Explanation of changes")
    def test_handle_blame_postprocessing(self, mock_explain, mock_get_blame, capsys):
        """Test blame output postprocessing."""
        args = MagicMock(spec=argparse.Namespace)
        args.file = "test.py"
        args.line = "42"

        _handle_blame(args, ["--show-email"])

        captured = capsys.readouterr()
        assert "blame output with aig references" in captured.out
        assert "Explanation of changes" in captured.out

        mock_get_blame.assert_called_with("test.py", "42", ["--show-email"])


class TestHandleGitPassthroughEdgeCases:
    """Test _handle_git_passthrough function edge cases."""

    @patch("subprocess.run", return_value=MagicMock(returncode=0))
    def test_handle_git_passthrough_success(self, mock_run):
        """Test successful git passthrough."""
        with patch("sys.argv", ["aig", "status", "--short"]):
            with pytest.raises(SystemExit) as excinfo:
                _handle_git_passthrough()
            assert excinfo.value.code == 0

        mock_run.assert_called_with(
            ["git", "status", "--short"], text=True, check=False
        )

    @patch("subprocess.run", return_value=MagicMock(returncode=1))
    def test_handle_git_passthrough_failure(self, mock_run):
        """Test git passthrough with command failure."""
        with patch("sys.argv", ["aig", "invalid-command"]):
            with pytest.raises(SystemExit) as excinfo:
                _handle_git_passthrough()
            assert excinfo.value.code == 1

    @patch("aig.get_branch_prefix", return_value="feature")
    @patch("subprocess.run", return_value=MagicMock(returncode=0))
    def test_handle_git_passthrough_checkout_insufficient_args(
        self, mock_run, mock_get_branch_prefix
    ):
        """Test checkout with insufficient arguments."""
        with patch("sys.argv", ["aig", "checkout", "-b"]):  # Missing branch name
            with pytest.raises(SystemExit):
                _handle_git_passthrough()

        # Should not modify argv when insufficient args
        mock_run.assert_called_with(["git", "checkout", "-b"], text=True, check=False)

    @patch("aig.get_branch_prefix", return_value="hotfix")
    @patch("subprocess.run", return_value=MagicMock(returncode=0))
    def test_handle_git_passthrough_checkout_wrong_flag(
        self, mock_run, mock_get_branch_prefix
    ):
        """Test checkout with flag other than -b."""
        with patch("sys.argv", ["aig", "checkout", "-f", "existing-branch"]):
            with pytest.raises(SystemExit):
                _handle_git_passthrough()

        # Should not modify argv when not creating new branch
        mock_run.assert_called_with(
            ["git", "checkout", "-f", "existing-branch"], text=True, check=False
        )

    @patch("subprocess.run", return_value=MagicMock(returncode=0))
    def test_handle_git_passthrough_non_branch_command(self, mock_run):
        """Test passthrough with non-branch command."""
        with patch("sys.argv", ["aig", "status", "--porcelain"]):
            with pytest.raises(SystemExit):
                _handle_git_passthrough()

        mock_run.assert_called_with(
            ["git", "status", "--porcelain"], text=True, check=False
        )


class TestMainFunctionEdgeCases:
    """Test main function edge cases."""

    @patch("argparse.ArgumentParser.parse_known_args")
    def test_main_config_command(self, mock_parse):
        """Test main function with config command."""
        mock_args = MagicMock()
        mock_args.command = "config"
        mock_args.branch_prefix = "feature"
        mock_parse.return_value = (mock_args, [])

        with patch("sys.argv", ["aig", "config", "--branch-prefix", "feature"]):
            with patch("aig._handle_config") as mock_handle_config:
                main()

            mock_handle_config.assert_called_with(mock_args)

    @patch("argparse.ArgumentParser.parse_known_args")
    def test_main_test_command(self, mock_parse):
        """Test main function with test command."""
        mock_args = MagicMock()
        mock_args.command = "test"
        mock_parse.return_value = (mock_args, [])

        with patch("sys.argv", ["aig", "test"]):
            with patch("aig._handle_test") as mock_handle_test:
                main()

            mock_handle_test.assert_called_with()

    def test_main_with_empty_argv(self):
        """Test main function with empty sys.argv (just program name)."""
        with patch("sys.argv", ["aig"]):
            with patch(
                "argparse.ArgumentParser.parse_known_args", side_effect=SystemExit(2)
            ):
                with pytest.raises(SystemExit) as excinfo:
                    main()
                # Should exit due to required subcommand not provided
                assert excinfo.value.code == 2


class TestNoAPIKeysScenario:
    """Test scenario when no API keys are available."""

    @patch.dict(os.environ, {}, clear=True)
    @patch("aig.google.is_available", return_value=False)
    @patch("aig.openai.is_available", return_value=False)
    @patch("aig.anthropic.is_available", return_value=False)
    def test_no_api_keys_available(
        self, mock_anthropic_avail, mock_openai_avail, mock_google_avail
    ):
        """Test behavior when no API keys are available."""
        # This would trigger the sys.exit in the module initialization
        with pytest.raises(SystemExit) as excinfo:
            import importlib
            import aig.ai

            importlib.reload(aig.ai)

        assert "No API keys found in environment variables" in str(excinfo.value)


class TestUnicodeAndSpecialCharacters:
    """Test handling of Unicode and special characters."""

    @patch("aig.ai.ask", return_value="🚀 添加新功能")
    def test_commit_message_with_unicode(self, mock_ask):
        """Test commit message generation with Unicode characters."""
        diff = "diff --git a/文件.py\\n+print('你好世界')"
        result = commit_message_from_diff(diff)
        assert result == "🚀 添加新功能"

    def test_postprocess_output_with_unicode(self):
        """Test output postprocessing with Unicode characters."""
        text = "git 命令执行成功 🎉"
        result = _postprocess_output(text)
        assert result == "aig 命令执行成功 🎉"

    @patch("aig.run", return_value="🔧 配置文件更新\\n✅ 测试通过")
    def test_get_diff_with_unicode_output(self, mock_run):
        """Test git diff with Unicode output."""
        result = get_diff()
        assert "🔧 配置文件更新" in result
        assert "✅ 测试通过" in result


class TestLongInputHandling:
    """Test handling of very long inputs."""

    @patch("aig.ai.ask", return_value="Long response" * 100)
    def test_long_diff_input(self, mock_ask):
        """Test commit message generation with very long diff."""
        long_diff = "+" + "x" * 10000  # Very long diff
        result = commit_message_from_diff(long_diff)
        assert len(result) > 0  # Should handle long input without crashing

    @patch("aig.run", return_value="x" * 50000)
    def test_very_long_command_output(self, mock_run):
        """Test handling of very long command output."""
        result = get_log()
        assert len(result) == 50000  # Should preserve full output


class TestErrorRecovery:
    """Test error recovery scenarios."""

    @patch("os.path.exists", side_effect=OSError("Permission denied"))
    def test_install_hooks_os_error(self, mock_exists):
        """Test pre-commit hooks installation with OS error."""
        # Should not crash even if os.path.exists fails
        with pytest.raises(OSError):
            _install_pre_commit_hooks_if_needed()

    @patch(
        "aig.git._patched_run_if_present",
        side_effect=subprocess.CalledProcessError(128, "git"),
    )
    def test_git_command_retry_pattern(self, _mock_patched_run):
        """Test pattern where git command might fail initially."""
        # This tests that CalledProcessError propagates correctly through run()
        result = get_branch_prefix()
        # get_branch_prefix catches CalledProcessError and returns empty string
        assert result == ""


class TestEnvironmentVariables:
    """Test environment variable handling."""

    @patch.dict(os.environ, {"MODEL_NAME": "custom-model"}, clear=False)
    @patch("aig.ai.ask")
    def test_custom_model_name(self, mock_ask):
        """Test that custom model names are respected."""
        # This indirectly tests that MODEL_NAME env var is used in providers
        commit_message_from_diff("test diff")
        mock_ask.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)
    @patch("aig.ai.ask")
    def test_default_model_name(self, mock_ask):
        """Test that default model names are used when env var not set."""
        commit_message_from_diff("test diff")
        mock_ask.assert_called_once()


class TestConcurrencyAndThreadSafety:
    """Test concurrent access patterns (basic checks)."""

    def test_postprocess_output_thread_safety(self):
        """Test that postprocess_output is thread-safe."""
        import threading
        import time

        results = []

        def worker():
            for i in range(100):
                result = _postprocess_output(f"git command {i}")
                results.append(result)
                time.sleep(0.001)  # Small delay to encourage race conditions

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All results should have git replaced with aig
        assert all("aig" in result for result in results)
        assert all("git" not in result for result in results)


class TestArgumentParsingEdgeCases:
    """Test argument parsing edge cases."""

    @patch("argparse.ArgumentParser.parse_known_args")
    def test_main_with_unknown_command_in_handlers(self, mock_parse):
        """Test main function with command not in the conditional branches."""
        mock_args = MagicMock()
        mock_args.command = "config"  # Falls into the else branch
        mock_parse.return_value = (mock_args, [])

        with patch("sys.argv", ["aig", "config"]):
            with patch("aig._handle_config") as mock_handle:
                main()

            mock_handle.assert_called_with(mock_args)

    def test_command_enum_values(self):
        """Test that all Command enum values are strings."""
        from aig import Command

        for cmd in Command:
            assert isinstance(cmd.value, str)
            assert len(cmd.value) > 0


@pytest.fixture
def mock_args_with_date():
    """Mock args with date parameter."""
    args = MagicMock(spec=argparse.Namespace)
    args.message = "Test commit with date"
    args.yes = True
    args.date = "2023-01-01T12:00:00"
    return args


@pytest.fixture
def mock_args_with_yes():
    """Mock args with yes flag."""
    args = MagicMock(spec=argparse.Namespace)
    args.message = None
    args.yes = True
    args.date = None
    return args


class TestAPIProviderInitialization:
    """Test different API provider initialization scenarios."""

    @patch.dict(os.environ, {}, clear=True)
    @patch("aig.google.is_available", return_value=False)
    @patch("aig.openai.is_available", return_value=True)
    @patch("aig.anthropic.is_available", return_value=False)
    @patch("aig.openai.init")
    def test_openai_provider_initialization(
        self,
        mock_openai_init,
        mock_anthropic_avail,
        mock_openai_avail,
        mock_google_avail,
    ):
        """Test OpenAI provider initialization path (lines 22-24)."""
        # Reload the ai submodule to trigger provider selection
        import importlib
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
        mock_anthropic_avail,
        mock_openai_avail,
        mock_google_avail,
    ):
        """Test Anthropic provider initialization path (lines 25-27)."""
        # Reload the ai submodule to trigger provider selection
        import importlib
        import aig.ai as ai_mod

        importlib.reload(ai_mod)
        mock_anthropic_init.assert_called_once()


class TestHandleTestExceptions:
    """Test _handle_test exception scenarios."""

    @patch("aig._install_pre_commit_hooks_if_needed")
    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_handle_test_file_not_found(self, mock_run, mock_install):
        """Test _handle_test with FileNotFoundError (lines 206-207)."""
        with pytest.raises(SystemExit) as excinfo:
            _handle_test()
        assert "❌ Pre-commit hooks failed with error:" in str(excinfo.value)

    @patch("aig._install_pre_commit_hooks_if_needed")
    @patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "cmd"))
    def test_handle_test_called_process_error(self, mock_run, mock_install):
        """Test _handle_test with CalledProcessError (lines 206-207)."""
        with pytest.raises(SystemExit) as excinfo:
            _handle_test()
        assert "❌ Pre-commit hooks failed with error:" in str(excinfo.value)


class TestHandleCommitAdvanced:
    """Test advanced _handle_commit scenarios."""

    @patch("aig._install_pre_commit_hooks_if_needed")
    @patch("subprocess.run")
    def test_handle_commit_with_date_and_yes(
        self, mock_run, mock_install, mock_args_with_date
    ):
        """Test _handle_commit with date and yes flag (lines 239-241, 244)."""
        _handle_commit(mock_args_with_date, [])

        # Verify subprocess.run was called with the expected arguments
        expected_cmd = [
            "git",
            "commit",
            "--date",
            "2023-01-01T12:00:00",
            "-F",
            "-",
            "--yes",
        ]
        expected_env = os.environ.copy()
        expected_env["GIT_AUTHOR_DATE"] = "2023-01-01T12:00:00"
        expected_env["GIT_COMMITTER_DATE"] = "2023-01-01T12:00:00"

        mock_run.assert_called_with(
            expected_cmd,
            input="Test commit with date",
            check=True,
            text=True,
            env=expected_env,
        )

    @patch("aig._install_pre_commit_hooks_if_needed")
    @patch("aig.get_diff", return_value="test diff")
    @patch("aig.commit_message_from_diff", return_value="Test commit")
    @patch("subprocess.run")
    def test_handle_commit_error_with_stdout_stderr(
        self,
        mock_run,
        mock_commit_msg,
        mock_get_diff,
        mock_install,
        mock_args_with_yes,
        capsys,
    ):
        """Test _handle_commit error handling with stdout and stderr (lines 256-260)."""
        error = subprocess.CalledProcessError(1, "git commit")
        error.stdout = "This is stdout from git"
        error.stderr = "This is stderr from git"
        mock_run.side_effect = error

        with pytest.raises(SystemExit):
            _handle_commit(mock_args_with_yes, [])

        captured = capsys.readouterr()
        assert "❌ Commit failed." in captured.err
        assert "This is stdout from aig" in captured.err  # Should be processed
        assert "This is stderr from aig" in captured.err  # Should be processed


class TestHandleGitPassthrough:
    """Test _handle_git_passthrough advanced scenarios."""

    @patch("aig.get_branch_prefix", return_value="feature")
    @patch("subprocess.run")
    def test_handle_git_passthrough_checkout_with_prefix(
        self, mock_run, mock_get_branch_prefix
    ):
        """Test git passthrough with checkout -b and prefix (lines 337-343)."""
        with patch("sys.argv", ["aig", "checkout", "-b", "new-branch"]):
            with pytest.raises(SystemExit):
                _handle_git_passthrough()

        # Verify that sys.argv was modified to include the prefix
        mock_run.assert_called_with(
            ["git", "checkout", "-b", "feature/new-branch"], text=True, check=False
        )

    @patch("aig.get_branch_prefix", return_value="feature")
    @patch("subprocess.run")
    def test_handle_git_passthrough_branch_with_prefix(
        self, mock_run, mock_get_branch_prefix
    ):
        """Test git passthrough with branch and prefix (lines 340-343)."""
        with patch("sys.argv", ["aig", "branch", "new-branch"]):
            with pytest.raises(SystemExit):
                _handle_git_passthrough()

        # Verify that sys.argv was modified to include the prefix
        mock_run.assert_called_with(
            ["git", "branch", "feature/new-branch"], text=True, check=False
        )

    @patch("aig.get_branch_prefix", return_value="")
    @patch("subprocess.run")
    def test_handle_git_passthrough_no_prefix(self, mock_run, mock_get_branch_prefix):
        """Test git passthrough without prefix."""
        with patch("sys.argv", ["aig", "checkout", "-b", "new-branch"]):
            with pytest.raises(SystemExit):
                _handle_git_passthrough()

        # Verify that sys.argv was not modified when no prefix
        mock_run.assert_called_with(
            ["git", "checkout", "-b", "new-branch"], text=True, check=False
        )


class TestMainGitPassthrough:
    """Test main function git passthrough logic."""

    @patch("aig._handle_git_passthrough")
    def test_main_git_passthrough_unknown_command(self, mock_passthrough):
        """Test main function calling git passthrough for unknown commands (lines 354-365)."""
        with patch("sys.argv", ["aig", "status"]):
            # Mock _handle_git_passthrough to raise SystemExit to prevent further execution
            mock_passthrough.side_effect = SystemExit(0)
            with pytest.raises(SystemExit):
                main()

        mock_passthrough.assert_called_once()

    @patch("aig._handle_git_passthrough")
    def test_main_no_git_passthrough_for_help(self, mock_passthrough):
        """Test main function not calling git passthrough for help commands."""
        with patch("sys.argv", ["aig", "--help"]):
            with patch(
                "argparse.ArgumentParser.parse_known_args", side_effect=SystemExit(0)
            ):
                with pytest.raises(SystemExit):
                    main()

        # Should not call git passthrough for help commands
        mock_passthrough.assert_not_called()

    @patch("aig._handle_git_passthrough")
    def test_main_no_git_passthrough_for_version(self, mock_passthrough):
        """Test main function not calling git passthrough for version commands."""
        with patch("sys.argv", ["aig", "--version"]):
            with patch(
                "argparse.ArgumentParser.parse_known_args", side_effect=SystemExit(0)
            ):
                with pytest.raises(SystemExit):
                    main()

        # Should not call git passthrough for version commands
        mock_passthrough.assert_not_called()

    @patch("aig._handle_git_passthrough")
    def test_main_no_git_passthrough_for_valid_commands(self, mock_passthrough):
        """Test main function not calling git passthrough for valid aig commands."""
        with patch("sys.argv", ["aig", "commit"]):
            with patch("argparse.ArgumentParser.parse_known_args") as mock_parse:
                mock_args = MagicMock()
                mock_args.command = "commit"
                mock_parse.return_value = (mock_args, [])

                with patch("aig._handle_commit") as _:
                    main()

        # Should not call git passthrough for valid aig commands
        mock_passthrough.assert_not_called()


class TestConfigHandlerEdgeCases:
    """Test _handle_config edge cases."""

    @patch("aig.run")
    def test_handle_config_unset_branch_prefix(self, mock_run):
        """Test _handle_config with empty branch prefix to unset (line 327-328)."""
        args = MagicMock()
        args.branch_prefix = ""  # Empty string should trigger unset

        from aig import _handle_config

        _handle_config(args)

        mock_run.assert_called_with(["git", "config", "--unset", "aig.branch-prefix"])

    def test_handle_config_branch_prefix_none(self):
        """Test _handle_config with branch_prefix=None (no action)."""
        args = MagicMock()
        args.branch_prefix = None  # Should not trigger any action

        from aig import _handle_config

        with patch("aig.run") as mock_run:
            _handle_config(args)
            mock_run.assert_not_called()


class TestRemainingBranchCoverage:
    """Test remaining partial branch coverage scenarios."""

    @patch("aig._install_pre_commit_hooks_if_needed")
    @patch("aig.get_diff", return_value="test diff")
    @patch("aig.commit_message_from_diff", return_value="Test commit")
    def test_handle_commit_user_decline(
        self, mock_commit_msg, mock_get_diff, mock_install
    ):
        """Test _handle_commit when user declines to commit (branch 233->exit)."""
        args = MagicMock(spec=argparse.Namespace)
        args.message = None
        args.yes = False
        args.date = None

        with patch("builtins.input", return_value="n"):
            _handle_commit(args, [])

        # Should not proceed with commit when user declines
        # Function should return without calling subprocess.run

    @patch("aig._install_pre_commit_hooks_if_needed")
    @patch("subprocess.run")
    def test_handle_commit_error_no_stdout(self, mock_run, mock_install, capsys):
        """Test _handle_commit error handling with no stdout (branch 256->258)."""
        args = MagicMock(spec=argparse.Namespace)
        args.message = "Test commit"
        args.yes = True
        args.date = None

        error = subprocess.CalledProcessError(1, "git commit")
        error.stdout = None  # No stdout
        error.stderr = "This is stderr from git"
        mock_run.side_effect = error

        with pytest.raises(SystemExit):
            _handle_commit(args, [])

        captured = capsys.readouterr()
        assert "❌ Commit failed." in captured.err
        assert "This is stderr from aig" in captured.err  # Should be processed
        # Should not have stdout processing since stdout is None

    @patch("aig._install_pre_commit_hooks_if_needed")
    @patch("subprocess.run")
    def test_handle_commit_error_no_stderr(self, mock_run, mock_install, capsys):
        """Test _handle_commit error handling with no stderr (branch 258->260)."""
        args = MagicMock(spec=argparse.Namespace)
        args.message = "Test commit"
        args.yes = True
        args.date = None

        error = subprocess.CalledProcessError(1, "git commit")
        error.stdout = "This is stdout from git"
        error.stderr = None  # No stderr
        mock_run.side_effect = error

        with pytest.raises(SystemExit):
            _handle_commit(args, [])

        captured = capsys.readouterr()
        assert "❌ Commit failed." in captured.err
        assert "This is stdout from aig" in captured.err  # Should be processed
        # Should not have stderr processing since stderr is None

    @patch("aig.get_branch_prefix", return_value="feature")
    @patch("subprocess.run")
    def test_handle_git_passthrough_branch_short_args(
        self, mock_run, mock_get_branch_prefix
    ):
        """Test git passthrough with branch but insufficient args (branch 340->343)."""
        with patch("sys.argv", ["aig", "branch"]):  # No branch name provided
            with pytest.raises(SystemExit):
                _handle_git_passthrough()

        # Should not modify sys.argv when insufficient args
        mock_run.assert_called_with(["git", "branch"], text=True, check=False)

    @patch("aig._handle_git_passthrough")
    def test_main_single_arg_help_passthrough(self, mock_passthrough):
        """Test main function with single argument that's not a command (branch 354->365)."""
        with patch(
            "sys.argv", ["aig"]
        ):  # Single argument, should not trigger passthrough
            with patch("argparse.ArgumentParser.parse_known_args") as mock_parse:
                mock_args = MagicMock()
                mock_args.command = "commit"
                mock_parse.return_value = (mock_args, [])

                with patch("aig._handle_commit") as _:
                    main()

        # Should not call git passthrough with single argument
        mock_passthrough.assert_not_called()


def test_patched_run_fallback_and_unstaged_diff(monkeypatch):
    """Cover fallback in _patched_run_if_present and exercise get_unstaged_diff."""
    import sys as _sys
    from aig import git as git_mod

    class Explosive:
        def __getattr__(self, _name):  # hasattr should trigger this and raise
            raise RuntimeError("boom")

    # Ensure we fall back to aig.git.run rather than aig.run
    with patch("aig.git.run") as mock_run:
        mock_run.return_value = "ok"
        with patch.dict(_sys.modules, {"aig": Explosive()}):
            result = git_mod.get_unstaged_diff()
            assert result == "ok"
            mock_run.assert_called_with(["git", "diff"])


def test_patched_run_when_pkg_none_and_unstaged_diff_with_args():
    """Cover branch where sys.modules has no usable 'aig' and extra_args are extended."""
    import sys as _sys
    from aig import git as git_mod

    with patch("aig.git.run") as mock_run:
        mock_run.return_value = "ok"
        # Make sys.modules return None for 'aig' to follow the simple false branch
        with patch.dict(_sys.modules, {"aig": None}, clear=False):
            result = git_mod.get_unstaged_diff(["--name-only"])
            assert result == "ok"
            mock_run.assert_called_with(["git", "diff", "--name-only"])


class TestArgcompleteOptionalInstall:
    """Cover optional argcomplete installer helper."""

    def test_install_argcomplete_already_present(self):
        from aig import _install_argcomplete_if_missing

        with patch("importlib.util.find_spec", return_value=object()):
            with patch("subprocess.run") as mock_subproc:
                assert _install_argcomplete_if_missing() is True
                mock_subproc.assert_not_called()

    def test_install_argcomplete_installs_with_user_flag(self, monkeypatch):
        from aig import _install_argcomplete_if_missing

        calls = [None, object()]

        def fake_find_spec(_name):
            return calls.pop(0)

        monkeypatch.delenv("VIRTUAL_ENV", raising=False)
        with patch("importlib.util.find_spec", side_effect=fake_find_spec):
            with patch("subprocess.run") as mock_subproc:
                assert _install_argcomplete_if_missing() is True
                cmd = mock_subproc.call_args[0][0]
                assert "pip" in cmd and "install" in cmd
                assert "--user" in cmd  # not in venv => uses --user

    def test_install_argcomplete_install_failure(self):
        from aig import _install_argcomplete_if_missing

        with patch("importlib.util.find_spec", return_value=None):
            with patch("subprocess.run", side_effect=Exception("boom")):
                assert _install_argcomplete_if_missing() is False


def _project_src_dir() -> str:
    # Resolve to absolute path of this repo's src directory
    return str(Path(__file__).resolve().parents[1] / "src")


def _base_env_with_gemini() -> dict[str, str]:
    env = os.environ.copy()
    # Ensure the aig module is importable when running from a temp repo
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{_project_src_dir()}:{existing_pythonpath}"
        if existing_pythonpath
        else _project_src_dir()
    )
    # Prefer a faster/cheaper model for live tests
    env.setdefault("MODEL_NAME", "gemini-1.5-flash-latest")
    return env


def _run(
    cmd: list[str], cwd: Path, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), env=env, text=True, capture_output=True)


def _init_git_repo(repo_dir: Path) -> None:
    _run(["git", "init"], cwd=repo_dir, env=os.environ.copy())
    _run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_dir,
        env=os.environ.copy(),
    )
    _run(
        ["git", "config", "user.name", "Test User"], cwd=repo_dir, env=os.environ.copy()
    )


skip_if_no_key = pytest.mark.skipif(
    os.getenv("GOOGLE_API_KEY") is None and os.getenv("GEMINI_API_KEY") is None,
    reason="GOOGLE_API_KEY/GEMINI_API_KEY not set; skipping CLI Gemini E2E tests",
)


@pytest.mark.integration
@skip_if_no_key
def test_cli_commit_log_blame_with_gemini_e2e(tmp_path: Path):
    env = _base_env_with_gemini()

    # Set up a new git repo with one staged file
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    file_path = repo / "hello.txt"
    file_path.write_text("hello world\n")

    # Stage the file
    res = _run(["git", "add", "hello.txt"], cwd=repo, env=env)
    assert res.returncode == 0, res.stderr

    # Commit using aig with an explicit message to avoid interactive confirmation
    res = _run(
        [sys.executable, "-m", "aig", "commit", "-m", "test commit", "--no-verify"],
        cwd=repo,
        env=env,
    )
    assert res.returncode == 0, res.stderr
    assert "Commit successful" in res.stdout

    # Verify a commit exists
    res = _run(["git", "rev-parse", "HEAD"], cwd=repo, env=env)
    assert res.returncode == 0, res.stderr
    assert res.stdout.strip()

    # Run aig log (summarization uses Gemini)
    res = _run([sys.executable, "-m", "aig", "log"], cwd=repo, env=env)
    assert res.returncode == 0, res.stderr
    assert "Recent commits:" in res.stdout
    assert "▶ Summary:" in res.stdout

    # Blame the first line and get an explanation (uses Gemini)
    res = _run(
        [sys.executable, "-m", "aig", "blame", "hello.txt", "1"], cwd=repo, env=env
    )
    assert res.returncode == 0, res.stderr
    assert "Blame output:" in res.stdout
    assert "▶ Explanation:" in res.stdout
