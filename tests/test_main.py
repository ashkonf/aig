from unittest.mock import patch, Mock, mock_open
import pytest
import gai as main
import sys
import subprocess
import runpy

import importlib


def _reload_module():
    """Reload the main module to test different configurations."""
    importlib.reload(main)


# ------------------------------------------------------------------------------
# Mocks and Fixtures
# ------------------------------------------------------------------------------


@pytest.fixture
def mock_run():
    """Fixture for mocking the `run` function."""
    with patch("gai.run") as mock:
        yield mock


@pytest.fixture
def mock_ask_gemini():
    """Fixture for mocking the `ask_gemini` function."""
    with patch("gai.ask_gemini") as mock:
        yield mock


@pytest.fixture
def mock_subprocess_run():
    """Fixture for mocking `subprocess.run`."""
    with patch("subprocess.run") as mock:
        yield mock


@pytest.fixture
def mock_input():
    """Fixture for mocking `builtins.input`."""
    with patch("builtins.input") as mock:
        yield mock


# ------------------------------------------------------------------------------
# Tests for Core Functions
# ------------------------------------------------------------------------------


def test_get_diff(mock_run: Mock) -> None:
    """Test the `get_diff` function."""
    mock_run.return_value = "diff --git a/file.txt b/file.txt"
    diff = main.get_diff()
    assert "diff --git" in diff
    mock_run.assert_called_with(["git", "diff", "--cached"])


def test_get_log(mock_run: Mock) -> None:
    """Test the `get_log` function."""
    mock_run.return_value = "hash1 Commit 1"
    log = main.get_log()
    assert "hash1" in log
    mock_run.assert_called_with(["git", "log", "-n", "10", "--oneline"])


def test_get_blame(mock_run: Mock) -> None:
    """Test the `get_blame` function."""
    mock_run.return_value = "blame output"
    blame = main.get_blame("file.txt", 1)
    assert "blame output" in blame
    mock_run.assert_called_with(["git", "blame", "-L", "1,1", "file.txt"])


@patch(
    "subprocess.check_output",
    side_effect=FileNotFoundError("Command not found"),
)
def test_run_file_not_found(mock_check_output: Mock) -> None:
    """Test that the run function exits if the command is not found."""
    with pytest.raises(SystemExit) as e:
        main.run(["some-command"])
    assert "Command not found" in str(e.value)


@patch("gai.run")
def test_get_diff_with_extra_args(mock_run: Mock) -> None:
    """Test the `get_diff` function with extra arguments."""
    main.get_diff(["--", "file.txt"])
    mock_run.assert_called_with(["git", "diff", "--cached", "--", "file.txt"])


def test_get_log_with_extra_args(mock_run: Mock) -> None:
    """Test the `get_log` function with extra arguments."""
    main.get_log(["--author", "test"])
    mock_run.assert_called_with(
        ["git", "log", "-n", "10", "--oneline", "--author", "test"]
    )


def test_get_blame_with_extra_args(mock_run: Mock) -> None:
    """Test the `get_blame` function with extra arguments."""
    main.get_blame("file.txt", 1, ["-w"])
    mock_run.assert_called_with(["git", "blame", "-L", "1,1", "file.txt", "-w"])


@patch("gai.run", side_effect=subprocess.CalledProcessError(1, "cmd"))
def test_get_branch_prefix_error(mock_run: Mock) -> None:
    """Test that `get_branch_prefix` returns an empty string on error."""
    prefix = main.get_branch_prefix()
    assert prefix == ""


@patch("gai.run", side_effect=subprocess.CalledProcessError(1, "cmd"))
def test_get_default_branch_error(mock_run: Mock) -> None:
    """Test that `get_default_branch` returns 'main' on error."""
    branch = main.get_default_branch()
    assert branch == "main"


@patch(
    "subprocess.check_output",
    side_effect=subprocess.CalledProcessError(1, "cmd", "output"),
)
def test_run_called_process_error(mock_check_output: Mock) -> None:
    """Test that the run function exits if the command fails."""
    with pytest.raises(SystemExit) as e:
        main.run(["some-command"])
    assert "Command failed" in str(e.value)


@patch("gai._model.generate_content", side_effect=Exception("API key not valid"))
def test_ask_gemini_invalid_api_key(mock_generate_content: Mock) -> None:
    """Test that `ask_gemini` handles an invalid API key."""
    with pytest.raises(SystemExit) as e:
        main.ask_gemini("test prompt")
    assert "API key is not valid" in str(e.value)


@patch("gai._model.generate_content", side_effect=Exception("Some other error"))
def test_ask_gemini_other_error(mock_generate_content: Mock) -> None:
    """Test that `ask_gemini` handles other API errors."""
    with pytest.raises(SystemExit) as e:
        main.ask_gemini("test prompt")
    assert "Gemini API error" in str(e.value)


def test_commit_message_from_diff(mock_ask_gemini: Mock) -> None:
    """Test the `commit_message_from_diff` function."""
    mock_ask_gemini.return_value = "feat: Implement new feature"
    msg = main.commit_message_from_diff("some diff")
    assert "feat: Implement new feature" in msg
    mock_ask_gemini.assert_called_once()


def test_summarize_commit_log(mock_ask_gemini: Mock) -> None:
    """Test the `summarize_commit_log` function."""
    mock_ask_gemini.return_value = "Summary of commits"
    summary = main.summarize_commit_log("some log")
    assert "Summary of commits" in summary
    mock_ask_gemini.assert_called_once()


def test_explain_blame_output(mock_ask_gemini: Mock) -> None:
    """Test the `explain_blame_output` function."""
    mock_ask_gemini.return_value = "Explanation of blame"
    explanation = main.explain_blame_output("some blame")
    assert "Explanation of blame" in explanation
    mock_ask_gemini.assert_called_once()


def test_code_review_from_diff(mock_ask_gemini: Mock) -> None:
    """Test the `code_review_from_diff` function."""
    mock_ask_gemini.return_value = "LGTM!"
    review = main.code_review_from_diff("some diff")
    assert "LGTM!" in review
    mock_ask_gemini.assert_called_once()


def test_stash_name_from_diff(mock_ask_gemini: Mock) -> None:
    """Test the `stash_name_from_diff` function."""
    mock_ask_gemini.return_value = "WIP: Stash"
    msg = main.stash_name_from_diff("some diff")
    assert "WIP: Stash" in msg
    mock_ask_gemini.assert_called_once()


def test_pr_summary_from_diff(mock_ask_gemini: Mock) -> None:
    """Test the `pr_summary_from_diff` function."""
    mock_ask_gemini.return_value = '{"title": "Test PR", "body": "PR body"}'
    summary = main.pr_summary_from_diff("some diff")
    assert "Test PR" in summary
    mock_ask_gemini.assert_called_once()


@patch("os.path.exists")
@patch("subprocess.run")
def test_install_pre_commit_hooks_if_needed(mock_run, mock_exists):
    """Test that pre-commit hooks are installed if they don't exist."""
    mock_exists.return_value = False
    main._install_pre_commit_hooks_if_needed()
    mock_run.assert_called_once_with(
        [sys.executable, "-m", "pre_commit", "install"],
        check=True,
        text=True,
    )


@patch("os.path.exists")
@patch("subprocess.run")
def test_install_pre_commit_hooks_if_needed_already_installed(mock_run, mock_exists):
    """Test that pre-commit hooks are not installed if they already exist."""
    mock_exists.return_value = True
    main._install_pre_commit_hooks_if_needed()
    mock_run.assert_not_called()


@patch("os.path.exists", return_value=False)
@patch(
    "subprocess.run",
    side_effect=subprocess.CalledProcessError(1, "cmd"),
)
def test_install_pre_commit_hooks_if_needed_error(
    mock_run: Mock, mock_exists: Mock
) -> None:
    """Test that pre-commit hook installation errors are handled."""
    main._install_pre_commit_hooks_if_needed()
    mock_run.assert_called_once()


# ------------------------------------------------------------------------------
# Tests for Main CLI Logic
# ------------------------------------------------------------------------------


@patch("subprocess.run")
@patch("gai.commit_message_from_diff", return_value="feat: Test commit")
@patch("gai.get_diff", return_value="some diff")
@patch("gai._install_pre_commit_hooks_if_needed", return_value=None)
@patch("os.environ.copy", return_value={})
def test_main_commit_yes(
    mock_env_copy: Mock,
    mock_install_hooks: Mock,
    mock_get_diff: Mock,
    mock_commit_message: Mock,
    mock_subprocess_run: Mock,
) -> None:
    """Test the main function with `commit --yes`."""
    with patch("sys.argv", ["gai", "commit", "--yes"]):
        main.main()
        mock_get_diff.assert_called_once()
        mock_commit_message.assert_called_with("some diff")
        mock_subprocess_run.assert_called_with(
            ["git", "commit", "-F", "-", "--yes"],
            input="feat: Test commit",
            check=True,
            text=True,
            env={},
        )


@patch("subprocess.run")
@patch("gai.commit_message_from_diff", return_value="feat: Test commit")
@patch("gai.get_diff", return_value="some diff")
@patch("gai._install_pre_commit_hooks_if_needed", return_value=None)
@patch("os.environ.copy", return_value={})
def test_main_commit_with_date(
    mock_env_copy: Mock,
    mock_install_hooks: Mock,
    mock_get_diff: Mock,
    mock_commit_message: Mock,
    mock_subprocess_run: Mock,
) -> None:
    """Test the main function with `commit --date`."""
    test_date = "2023-01-01T12:00:00"
    with patch("sys.argv", ["gai", "commit", "--yes", "--date", test_date]):
        main.main()
        mock_get_diff.assert_called_once()
        mock_commit_message.assert_called_with("some diff")
        mock_subprocess_run.assert_called_with(
            ["git", "commit", "--date", test_date, "-F", "-", "--yes"],
            input="feat: Test commit",
            check=True,
            text=True,
            env={"GIT_AUTHOR_DATE": test_date, "GIT_COMMITTER_DATE": test_date},
        )


@patch("subprocess.run")
@patch("gai.get_diff", return_value="some diff")
@patch("gai._install_pre_commit_hooks_if_needed", return_value=None)
@patch("os.environ.copy", return_value={})
def test_main_commit_with_message(
    mock_env_copy: Mock,
    mock_install_hooks: Mock,
    mock_get_diff: Mock,
    mock_subprocess_run: Mock,
) -> None:
    """Test the main function with `commit -m`."""
    with patch("sys.argv", ["gai", "commit", "-m", "my custom message"]):
        main.main()
        mock_get_diff.assert_not_called()
        mock_subprocess_run.assert_called_with(
            ["git", "commit", "-F", "-"],
            input="my custom message",
            check=True,
            text=True,
            env={},
        )


@patch("subprocess.run")
@patch("builtins.input", return_value="y")
@patch("os.environ.copy", return_value={})
@patch("gai._install_pre_commit_hooks_if_needed", return_value=None)
@patch("gai.commit_message_from_diff", return_value="feat: Test commit")
@patch("gai.get_diff", return_value="some diff")
def test_main_commit_interactive_yes(
    mock_get_diff: Mock,
    mock_commit_message: Mock,
    mock_install_hooks: Mock,
    mock_env_copy: Mock,
    mock_input: Mock,
    mock_subprocess_run: Mock,
) -> None:
    """Test the main function with `commit` and interactive 'yes'."""
    with patch("sys.argv", ["gai", "commit"]):
        main.main()
        mock_input.assert_called_once()
        mock_subprocess_run.assert_called_with(
            ["git", "commit", "-F", "-"],
            input="feat: Test commit",
            check=True,
            text=True,
            env={},
        )


@patch("subprocess.run")
@patch("builtins.input", return_value="n")
@patch("os.environ.copy", return_value={})
@patch("gai._install_pre_commit_hooks_if_needed", return_value=None)
@patch("gai.commit_message_from_diff", return_value="feat: Test commit")
@patch("gai.get_diff", return_value="some diff")
def test_main_commit_interactive_no(
    mock_get_diff: Mock,
    mock_commit_message: Mock,
    mock_install_hooks: Mock,
    mock_env_copy: Mock,
    mock_input: Mock,
    mock_subprocess_run: Mock,
) -> None:
    """Test the main function with `commit` and interactive 'no'."""
    with patch("sys.argv", ["gai", "commit"]):
        main.main()
        mock_input.assert_called_once()
        mock_subprocess_run.assert_not_called()


@patch("gai._install_pre_commit_hooks_if_needed")
@patch(
    "subprocess.run",
    side_effect=subprocess.CalledProcessError(1, "cmd", "output", "stderr"),
)
def test_main_commit_error(mock_subprocess_run: Mock, mock_install_hooks: Mock) -> None:
    """Test the main function with `commit` and an error."""
    with patch("sys.argv", ["gai", "commit", "-m", "my custom message"]):
        with pytest.raises(SystemExit):
            main.main()
        mock_install_hooks.assert_called_once()


@patch("gai.get_log", return_value="some log")
@patch("gai.summarize_commit_log", return_value="Summary of commits")
def test_main_log(mock_summarize: Mock, mock_get_log: Mock) -> None:
    """Test the main function with `log`."""
    with patch("sys.argv", ["gai", "log"]):
        main.main()
        mock_get_log.assert_called_once()
        mock_summarize.assert_called_with("some log")


@patch("gai.get_blame", return_value="some blame")
@patch("gai.explain_blame_output", return_value="Explanation of blame")
def test_main_blame(mock_explain: Mock, mock_get_blame: Mock) -> None:
    """Test the main function with `blame`."""
    with patch("sys.argv", ["gai", "blame", "file.txt", "1"]):
        main.main()
        mock_get_blame.assert_called_with("file.txt", "1", [])
        mock_explain.assert_called_with("some blame")


@patch("gai.get_diff", return_value="some diff")
@patch("gai.code_review_from_diff", return_value="LGTM!")
def test_main_review(mock_review: Mock, mock_get_diff: Mock) -> None:
    """Test the main function with `review`."""
    with patch("sys.argv", ["gai", "review"]):
        main.main()
        mock_get_diff.assert_called_once()
        mock_review.assert_called_with("some diff")


@patch("gai.get_diff", return_value="")
@patch("gai._install_pre_commit_hooks_if_needed")
def test_main_commit_no_changes(
    mock_install_hooks: Mock, mock_get_diff: Mock, mock_subprocess_run: Mock
) -> None:
    """Test the main function with `commit` and no staged changes."""
    with patch("sys.argv", ["gai", "commit"]):
        main.main()
        mock_get_diff.assert_called_once()
        mock_subprocess_run.assert_not_called()


@patch("gai.run")
@patch("gai.stash_name_from_diff", return_value="feat: Test stash")
@patch("gai.get_diff", return_value="some diff")
def test_main_stash_interactive_yes(
    mock_get_diff: Mock, mock_stash_name: Mock, mock_run: Mock, mock_input: Mock
) -> None:
    """Test the main function with `stash` and interactive 'yes'."""
    mock_input.return_value = "y"
    with patch("sys.argv", ["gai", "stash"]):
        main.main()
        mock_get_diff.assert_called_once()
        mock_stash_name.assert_called_with("some diff")
        mock_input.assert_called_once()
        mock_run.assert_called_with(["git", "stash", "push", "-m", "feat: Test stash"])


@patch("gai.run")
@patch("gai.stash_name_from_diff", return_value="feat: Test stash")
@patch("gai.get_diff", return_value="some diff")
def test_main_stash_interactive_no(
    mock_get_diff: Mock, mock_stash_name: Mock, mock_run: Mock, mock_input: Mock
) -> None:
    """Test the main function with `stash` and interactive 'no'."""
    mock_input.return_value = "n"
    with patch("sys.argv", ["gai", "stash"]):
        main.main()
        mock_get_diff.assert_called_once()
        mock_stash_name.assert_called_with("some diff")
        mock_input.assert_called_once()
        mock_run.assert_not_called()


# ------------------------------------------------------------------------------
# Tests for CLI Argument Parsing and Error Handling
# ------------------------------------------------------------------------------


@patch("os.getenv", return_value=None)
def test_missing_api_key(mock_getenv: Mock) -> None:
    """Test that the program exits if the API key is missing."""
    with pytest.raises(SystemExit) as e:
        # We need to reload main to re-evaluate the API_KEY check
        _reload_module()
    assert "GEMINI_API_KEY" in str(e.value)


def test_invalid_command() -> None:
    """Test that the program exits if an invalid command is provided."""
    with patch("sys.argv", ["gai", "invalid-command"]):
        with pytest.raises(SystemExit):
            main.main()


@patch("sys.stdout.isatty", return_value=True)
@patch("os.getenv", return_value=None)
@patch("builtins.open", new_callable=mock_open)
@patch("builtins.input", return_value="test-api-key")
def test_prompt_for_api_key(mock_input, mock_open_file, mock_getenv, mock_isatty):
    """Test that the user is prompted for an API key if it's not set."""
    # We need to reload main to re-evaluate the API_KEY check
    importlib.reload(main)

    # Check that isatty was called
    mock_isatty.assert_called_once()

    # Check that input was called
    mock_input.assert_called_with("Please enter your API key: ")

    # Check that the API key is written to the .env file
    mock_open_file.assert_called_with(".env", "a")
    mock_open_file().write.assert_called_with("GEMINI_API_KEY=test-api-key\n")


@patch("sys.stdout.isatty", return_value=True)
@patch("os.getenv", return_value=None)
@patch("builtins.input", return_value="")
def test_prompt_for_api_key_empty(mock_input, mock_getenv, mock_isatty):
    """Test that the program exits if the user provides an empty API key."""
    with pytest.raises(SystemExit) as e:
        _reload_module()
    assert "Gemini API key is required" in str(e.value)


@patch("subprocess.run")
def test_git_passthrough(mock_run: Mock) -> None:
    """Test that unknown commands are passed through to git."""
    with patch("sys.argv", ["gai", "status"]):
        with pytest.raises(SystemExit):
            main.main()
    mock_run.assert_called_with(["git", "status"], text=True, check=False)


@patch("gai.get_branch_prefix", return_value="feature")
@patch("subprocess.run")
def test_git_passthrough_branch_rewrite(
    mock_run: Mock, mock_get_branch_prefix: Mock
) -> None:
    """Test that `checkout -b` is rewritten with the branch prefix."""
    with patch("sys.argv", ["gai", "checkout", "-b", "new-branch-1"]):
        with pytest.raises(SystemExit):
            main.main()
    mock_run.assert_called_with(
        ["git", "checkout", "-b", "feature/new-branch-1"],
        text=True,
        check=False,
    )


@patch("gai.get_branch_prefix", return_value="feature")
@patch("subprocess.run")
def test_git_passthrough_branch_rewrite_short(
    mock_run: Mock, mock_get_branch_prefix: Mock
) -> None:
    """Test that `branch <name>` is rewritten with the branch prefix."""
    with patch("sys.argv", ["gai", "branch", "new-branch-2"]):
        with pytest.raises(SystemExit):
            main.main()
    mock_run.assert_called_with(
        ["git", "branch", "feature/new-branch-2"],
        text=True,
        check=False,
    )


@patch("gai.run")
def test_main_config_set_prefix(mock_run: Mock) -> None:
    """Test the main function with `config --branch-prefix`."""
    with patch("sys.argv", ["gai", "config", "--branch-prefix", "feature"]):
        main.main()
    mock_run.assert_called_with(["git", "config", "gai.branch-prefix", "feature"])


@patch("gai.run")
def test_main_config_unset_prefix(mock_run: Mock) -> None:
    """Test the main function with `config --branch-prefix ''`."""
    with patch("sys.argv", ["gai", "config", "--branch-prefix", ""]):
        main.main()
    mock_run.assert_called_with(["git", "config", "--unset", "gai.branch-prefix"])


@patch("gai.run")
@patch(
    "gai.pr_summary_from_diff", return_value='{"title": "Test PR", "body": "PR body"}'
)
@patch("gai.get_default_branch", return_value="main")
@patch("gai._check_gh_installed", return_value=None)
def test_main_submit_with_base(
    mock_check_gh: Mock,
    mock_get_default_branch: Mock,
    mock_pr_summary: Mock,
    mock_run: Mock,
) -> None:
    """Test the main function with `submit --base`."""
    mock_run.return_value = "diff"
    with patch("sys.argv", ["gai", "submit", "--yes", "--base", "develop"]):
        main.main()
    mock_run.assert_any_call(
        [
            "gh",
            "pr",
            "create",
            "--title",
            "Test PR",
            "--body",
            "PR body",
            "--base",
            "develop",
        ]
    )


@patch("gai._install_pre_commit_hooks_if_needed")
@patch(
    "subprocess.run",
    side_effect=subprocess.CalledProcessError(1, "cmd"),
)
def test_main_test_error(mock_subprocess_run: Mock, mock_install_hooks: Mock) -> None:
    """Test the main function with `test` and an error."""
    with patch("sys.argv", ["gai", "test"]):
        with pytest.raises(SystemExit):
            main.main()
        mock_install_hooks.assert_called_once()
        mock_subprocess_run.assert_called_with(
            [sys.executable, "-m", "pre_commit", "run", "--all-files"],
            check=True,
        )


@patch("gai._install_pre_commit_hooks_if_needed")
@patch("subprocess.run")
def test_main_test(mock_subprocess_run: Mock, mock_install_hooks: Mock) -> None:
    """Test the main function with `test`."""
    with patch("sys.argv", ["gai", "test"]):
        main.main()
        mock_install_hooks.assert_called_once()
        mock_subprocess_run.assert_called_with(
            [sys.executable, "-m", "pre_commit", "run", "--all-files"],
            check=True,
        )


@patch("gai.run")
@patch(
    "gai.pr_summary_from_diff",
    return_value='```json\n{"title": "Test PR", "body": "PR body"}\n```',
)
@patch("gai.get_default_branch", return_value="main")
@patch("gai._check_gh_installed", return_value=None)
def test_main_submit_json_with_fences(
    mock_check_gh: Mock,
    mock_get_default_branch: Mock,
    mock_pr_summary: Mock,
    mock_run: Mock,
    mock_input: Mock,
) -> None:
    """Test the main function with `submit` and a JSON response with fences."""
    mock_input.return_value = "y"
    mock_run.return_value = "diff"
    with patch("sys.argv", ["gai", "submit"]):
        main.main()
    mock_run.assert_any_call(
        ["gh", "pr", "create", "--title", "Test PR", "--body", "PR body"]
    )


@patch("gai.run")
@patch("gai.pr_summary_from_diff", return_value='{"bad": "json"}')
@patch("gai.get_default_branch", return_value="main")
@patch("gai._check_gh_installed", return_value=None)
def test_main_submit_bad_json(
    mock_check_gh: Mock,
    mock_get_default_branch: Mock,
    mock_pr_summary: Mock,
    mock_run: Mock,
    mock_input: Mock,
) -> None:
    """Test the main function with `submit` and bad JSON."""
    mock_input.return_value = "y"
    mock_run.return_value = "diff"
    with patch("sys.argv", ["gai", "submit"]):
        with pytest.raises(SystemExit) as e:
            main.main()
    assert "Could not parse PR summary" in str(e.value)


@patch("gai.get_branch_prefix", return_value="")
@patch("subprocess.run")
def test_git_passthrough_branch_rewrite_no_prefix(
    mock_run: Mock, mock_get_branch_prefix: Mock
) -> None:
    """Test that `checkout -b` is not rewritten when no prefix is set."""
    with patch("sys.argv", ["gai", "checkout", "-b", "new-branch-1"]):
        with pytest.raises(SystemExit):
            main.main()
    mock_run.assert_called_with(
        ["git", "checkout", "-b", "new-branch-1"],
        text=True,
        check=False,
    )


@patch("gai.get_diff", return_value="")
def test_main_review_no_changes(mock_get_diff: Mock) -> None:
    """Test the main function with `review` and no staged changes."""
    with patch("sys.argv", ["gai", "review"]):
        main.main()
        mock_get_diff.assert_called_once()


@patch("shutil.which", return_value=None)
def test_check_gh_installed_not_found(mock_which: Mock) -> None:
    """Test that `_check_gh_installed` exits if gh is not found."""
    with pytest.raises(SystemExit) as e:
        main._check_gh_installed()
    assert "The 'gh' command-line tool is not installed" in str(e.value)


@patch("gai.run", side_effect=subprocess.CalledProcessError(1, "cmd"))
@patch("gai._check_gh_installed", return_value=None)
def test_main_submit_diff_error(mock_check_gh: Mock, mock_run: Mock) -> None:
    """Test the main function with `submit` and an error getting the diff."""
    with patch("sys.argv", ["gai", "submit"]):
        with pytest.raises(SystemExit) as e:
            main.main()
    assert "Could not get diff" in str(e.value)


@patch("gai.run")
@patch(
    "gai.pr_summary_from_diff", return_value='{"title": "Test PR", "body": "PR body"}'
)
@patch("gai.get_default_branch", return_value="main")
@patch("gai._check_gh_installed", return_value=None)
def test_main_submit_gh_error(
    mock_check_gh: Mock,
    mock_get_default_branch: Mock,
    mock_pr_summary: Mock,
    mock_run: Mock,
    mock_input: Mock,
) -> None:
    """Test the main function with `submit` and an error from gh."""

    def run_side_effect(cmd):
        if "diff" in cmd:
            return "diff"
        if "gh" in cmd:
            raise subprocess.CalledProcessError(1, "cmd", "output", "stderr")
        return ""

    mock_input.return_value = "y"
    mock_run.side_effect = run_side_effect
    with patch("sys.argv", ["gai", "submit", "--yes"]):
        with pytest.raises(SystemExit) as e:
            main.main()
    assert "Failed to create pull request" in str(e.value)


@patch("subprocess.run", side_effect=FileNotFoundError)
def test_git_passthrough_not_found(mock_run: Mock) -> None:
    """Test that git passthrough exits if git is not found."""
    with patch("sys.argv", ["gai", "status"]):
        with pytest.raises(SystemExit) as e:
            main.main()
    assert "git is not installed" in str(e.value)


def test_main_entrypoint() -> None:
    """Test the main entrypoint."""
    with patch("sys.argv", ["gai", "--help"]):
        try:
            runpy.run_module("gai.__main__", run_name="__main__")
        except SystemExit as e:
            assert e.code == 0


@patch("gai.get_diff", return_value="")
def test_main_stash_no_changes(mock_get_diff: Mock, mock_run: Mock) -> None:
    """Test the main function with `stash` and no staged changes."""
    with patch("sys.argv", ["gai", "stash"]):
        main.main()
        mock_get_diff.assert_called_once()
        mock_run.assert_not_called()


@patch("gai.get_default_branch", return_value="main")
@patch("gai.get_diff", return_value=" ")
@patch("gai._check_gh_installed", return_value=None)
def test_main_submit_no_changes(
    mock_check_gh: Mock, mock_get_diff: Mock, mock_get_default_branch: Mock
) -> None:
    """Test the main function with `submit` and no changes."""
    with patch("sys.argv", ["gai", "submit"]):
        with patch("gai.run") as mock_run:
            mock_run.return_value = ""
            with pytest.raises(SystemExit) as e:
                main.main()
    assert "No changes to submit" in str(e.value)


@patch("gai.run")
@patch(
    "gai.pr_summary_from_diff", return_value='{"title": "Test PR", "body": "PR body"}'
)
@patch("gai.get_default_branch", return_value="main")
@patch("gai._check_gh_installed", return_value=None)
def test_main_submit_interactive_no(
    mock_check_gh: Mock,
    mock_get_default_branch: Mock,
    mock_pr_summary: Mock,
    mock_run: Mock,
    mock_input: Mock,
) -> None:
    """Test the main function with `submit` and interactive 'no'."""
    mock_input.return_value = "n"
    mock_run.return_value = "diff"
    with patch("sys.argv", ["gai", "submit"]):
        main.main()
    assert mock_run.call_count == 2


@patch(
    "gai._model.generate_content",
    return_value=Mock(
        text="```\nfoo\n```",
    ),
)
def test_ask_gemini_with_fences(mock_generate_content: Mock) -> None:
    """Test that `ask_gemini` handles a response with fences."""
    response = main.ask_gemini("test prompt")
    assert response == "foo"


@patch(
    "gai._model.generate_content",
    return_value=Mock(
        text="foo",
    ),
)
def test_ask_gemini_no_fences(mock_generate_content: Mock) -> None:
    """Test that `ask_gemini` handles a response with no fences."""
    response = main.ask_gemini("test prompt")
    assert response == "foo"


@patch("gai.run")
@patch(
    "gai.pr_summary_from_diff", return_value='{"title": "Test PR", "body": "PR body"}'
)
@patch("gai.get_default_branch", return_value="main")
@patch("gai._check_gh_installed", return_value=None)
def test_main_submit_with_draft(
    mock_check_gh: Mock,
    mock_get_default_branch: Mock,
    mock_pr_summary: Mock,
    mock_run: Mock,
) -> None:
    """Test the main function with `submit --draft`."""
    mock_run.return_value = "diff"
    with patch("sys.argv", ["gai", "submit", "--yes", "--draft"]):
        main.main()
    mock_run.assert_any_call(
        [
            "gh",
            "pr",
            "create",
            "--title",
            "Test PR",
            "--body",
            "PR body",
            "--draft",
        ]
    )


@patch("gai.run")
@patch("gai.get_diff", return_value="diff")
@patch("gai.stash_name_from_diff", return_value="stash message")
def test_main_stash_with_message(
    mock_stash_name: Mock, mock_get_diff: Mock, mock_run: Mock
) -> None:
    """Test the main function with `stash -m`."""
    with patch("sys.argv", ["gai", "stash", "-m", "my custom message"]):
        main.main()
        mock_run.assert_called_with(["git", "stash", "push", "-m", "my custom message"])
