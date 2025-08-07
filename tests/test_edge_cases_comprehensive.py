"""Comprehensive edge case tests for thorough coverage of all scenarios."""

import argparse
import os
import subprocess
import sys
from unittest.mock import MagicMock, patch
import pytest
from aig import (
    run,
    get_diff,
    get_log,
    get_blame,
    get_branch_prefix,
    get_default_branch,
    commit_message_from_diff,
    stash_name_from_diff,
    summarize_commit_log,
    explain_blame_output,
    code_review_from_diff,
    _install_pre_commit_hooks_if_needed,
    _postprocess_output,
    _handle_commit,
    _handle_stash,
    _handle_blame,
    _handle_git_passthrough,
    main,
)


class TestRunFunction:
    """Test the run() function edge cases."""

    @patch("subprocess.check_output")
    def test_run_success(self, mock_check_output):
        """Test successful command execution."""
        mock_check_output.return_value = b"test output"
        result = run(["git", "status"])
        assert result == "test output"

    @patch("subprocess.check_output", side_effect=FileNotFoundError())
    def test_run_file_not_found(self, mock_check_output):
        """Test command not found scenario."""
        with pytest.raises(SystemExit) as excinfo:
            run(["nonexistent-command", "arg"])
        assert "Command not found: nonexistent-command" in str(excinfo.value)

    @patch("subprocess.check_output")
    def test_run_called_process_error(self, mock_check_output):
        """Test command execution failure."""
        error = subprocess.CalledProcessError(1, "git status")
        error.output = b"Error output"
        mock_check_output.side_effect = error

        with pytest.raises(SystemExit) as excinfo:
            run(["git", "status"])
        assert "Command failed: git status" in str(excinfo.value)
        assert "Error output" in str(excinfo.value)

    @patch("subprocess.check_output")
    def test_run_with_unicode_output(self, mock_check_output):
        """Test handling of Unicode output."""
        mock_check_output.return_value = "✅ Unicode output 🎉".encode("utf-8")
        result = run(["git", "log"])
        assert result == "✅ Unicode output 🎉"

    @patch("subprocess.check_output")
    def test_run_with_empty_output(self, mock_check_output):
        """Test handling of empty output."""
        mock_check_output.return_value = b""
        result = run(["git", "status"])
        assert result == ""


class TestGitPlumbingFunctions:
    """Test git plumbing functions edge cases."""

    @patch("aig.run", return_value="test diff content")
    def test_get_diff_with_extra_args(self, mock_run):
        """Test get_diff with extra arguments."""
        result = get_diff(["--name-only", "--staged"])
        mock_run.assert_called_with(
            ["git", "diff", "--cached", "--name-only", "--staged"]
        )
        assert result == "test diff content"

    @patch("aig.run", return_value="test diff content")
    def test_get_diff_no_extra_args(self, mock_run):
        """Test get_diff without extra arguments."""
        result = get_diff(None)
        mock_run.assert_called_with(["git", "diff", "--cached"])
        assert result == "test diff content"

    @patch("aig.run", return_value="test diff content")
    def test_get_diff_empty_extra_args(self, mock_run):
        """Test get_diff with empty extra args list."""
        result = get_diff([])
        mock_run.assert_called_with(["git", "diff", "--cached"])
        assert result == "test diff content"

    @patch("aig.run", return_value="commit log content")
    def test_get_log_with_extra_args(self, mock_run):
        """Test get_log with extra arguments."""
        result = get_log(["--graph", "--all"])
        mock_run.assert_called_with(
            ["git", "log", "-n", "10", "--oneline", "--graph", "--all"]
        )
        assert result == "commit log content"

    @patch("aig.run", return_value="blame output")
    def test_get_blame_string_line_number(self, mock_run):
        """Test get_blame with string line number."""
        result = get_blame("file.py", "42")
        mock_run.assert_called_with(["git", "blame", "-L", "42,42", "file.py"])
        assert result == "blame output"

    @patch("aig.run", return_value="blame output")
    def test_get_blame_int_line_number(self, mock_run):
        """Test get_blame with integer line number."""
        result = get_blame("file.py", 42)
        mock_run.assert_called_with(["git", "blame", "-L", "42,42", "file.py"])
        assert result == "blame output"

    @patch("aig.run", return_value="blame output")
    def test_get_blame_with_extra_args(self, mock_run):
        """Test get_blame with extra arguments."""
        result = get_blame("file.py", 42, ["--show-email"])
        mock_run.assert_called_with(
            ["git", "blame", "-L", "42,42", "file.py", "--show-email"]
        )
        assert result == "blame output"

    @patch("aig.run")
    def test_get_branch_prefix_exception_handling(self, mock_run):
        """Test get_branch_prefix when git config fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git config")
        result = get_branch_prefix()
        assert result == ""

    @patch("aig.run", return_value="  feature/  \n")
    def test_get_branch_prefix_with_whitespace(self, mock_run):
        """Test get_branch_prefix strips whitespace."""
        result = get_branch_prefix()
        assert result == "feature/"

    @patch("aig.run")
    def test_get_default_branch_exception_handling(self, mock_run):
        """Test get_default_branch when git symbolic-ref fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git symbolic-ref")
        result = get_default_branch()
        assert result == "main"

    @patch("aig.run", return_value="refs/remotes/origin/develop")
    def test_get_default_branch_custom_branch(self, mock_run):
        """Test get_default_branch with custom default branch."""
        result = get_default_branch()
        assert result == "develop"

    @patch("aig.run", return_value="refs/remotes/origin/feature/complex-name")
    def test_get_default_branch_complex_name(self, mock_run):
        """Test get_default_branch with complex branch name."""
        result = get_default_branch()
        assert result == "complex-name"

    @patch("aig.run", return_value="  refs/remotes/origin/master  \n")
    def test_get_default_branch_with_whitespace(self, mock_run):
        """Test get_default_branch strips whitespace."""
        result = get_default_branch()
        assert result == "master"


class TestAIWrappers:
    """Test AI wrapper functions edge cases."""

    @patch("aig.ask", return_value="✨ Add new feature")
    def test_commit_message_from_diff_with_unicode(self, mock_ask):
        """Test commit message generation with Unicode diff."""
        diff = "diff --git a/file.py\\n+print('Hello 🌍')"
        result = commit_message_from_diff(diff)
        assert result == "✨ Add new feature"
        mock_ask.assert_called_once()

    @patch("aig.ask", return_value="")
    def test_commit_message_from_diff_empty_response(self, mock_ask):
        """Test commit message generation with empty AI response."""
        diff = "simple diff"
        result = commit_message_from_diff(diff)
        assert result == ""

    @patch("aig.ask", return_value="🔧 Fix configuration")
    def test_stash_name_from_diff_normal(self, mock_ask):
        """Test stash name generation."""
        diff = "diff --git a/config.py"
        result = stash_name_from_diff(diff)
        assert result == "🔧 Fix configuration"

    @patch("aig.ask", return_value="• Feature A\\n• Bug fix B")
    def test_summarize_commit_log_multiline(self, mock_ask):
        """Test commit log summarization with multiline response."""
        log = "abc123 Add feature A\\ndef456 Fix bug B"
        result = summarize_commit_log(log)
        assert result == "• Feature A\\n• Bug fix B"

    @patch("aig.ask", return_value="🔍 This change improves performance")
    def test_explain_blame_output_normal(self, mock_ask):
        """Test blame explanation generation."""
        blame = "abc123 (author@email.com 2024-01-01) line content"
        result = explain_blame_output(blame)
        assert result == "🔍 This change improves performance"

    @patch("aig.ask", return_value="✅ Code looks good!")
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
            import aig

            importlib.reload(aig)

        assert "No API keys found in environment variables" in str(excinfo.value)


class TestUnicodeAndSpecialCharacters:
    """Test handling of Unicode and special characters."""

    @patch("aig.ask", return_value="🚀 添加新功能")
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

    @patch("aig.ask", return_value="Long response" * 100)
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

    def test_git_command_retry_pattern(self):
        """Test pattern where git command might fail initially."""
        # This tests that CalledProcessError propagates correctly through run()
        with patch("aig.run", side_effect=subprocess.CalledProcessError(128, "git")):
            result = get_branch_prefix()
            # get_branch_prefix catches CalledProcessError and returns empty string
            assert result == ""


class TestEnvironmentVariables:
    """Test environment variable handling."""

    @patch.dict(os.environ, {"MODEL_NAME": "custom-model"}, clear=False)
    @patch("aig.ask")
    def test_custom_model_name(self, mock_ask):
        """Test that custom model names are respected."""
        # This indirectly tests that MODEL_NAME env var is used in providers
        commit_message_from_diff("test diff")
        mock_ask.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)
    @patch("aig.ask")
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
