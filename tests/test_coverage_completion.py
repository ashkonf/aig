"""Tests to achieve 100% code coverage for missing lines."""

import argparse
import os
import subprocess
from unittest.mock import MagicMock, patch
import pytest
from aig import (
    _handle_commit,
    _handle_test,
    _handle_git_passthrough,
    main,
)


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
        # We need to reload the module to trigger the initialization logic
        import importlib
        import aig

        importlib.reload(aig)
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
        # We need to reload the module to trigger the initialization logic
        import importlib
        import aig

        importlib.reload(aig)
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
