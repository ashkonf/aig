from unittest.mock import patch, Mock
import pytest
import main
import sys
import argparse

# ------------------------------------------------------------------------------
# Mocks and Fixtures
# ------------------------------------------------------------------------------


@pytest.fixture
def mock_run():
    """Fixture for mocking the `run` function."""
    with patch("main.run") as mock:
        yield mock


@pytest.fixture
def mock_ask_gemini():
    """Fixture for mocking the `ask_gemini` function."""
    with patch("main.ask_gemini") as mock:
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


@patch("os.path.exists")
@patch("subprocess.run")
def test_install_pre_commit_hooks_if_needed(mock_run, mock_exists):
    """Test that pre-commit hooks are installed if they don't exist."""
    mock_exists.return_value = False
    main._install_pre_commit_hooks_if_needed()
    mock_run.assert_called_once_with(
        [sys.executable, "-m", "pre_commit", "install"],
        check=True,
        capture_output=True,
        text=True,
    )


@patch("os.path.exists")
@patch("subprocess.run")
def test_install_pre_commit_hooks_if_needed_already_installed(mock_run, mock_exists):
    """Test that pre-commit hooks are not installed if they already exist."""
    mock_exists.return_value = True
    main._install_pre_commit_hooks_if_needed()
    mock_run.assert_not_called()


# ------------------------------------------------------------------------------
# Tests for Main CLI Logic
# ------------------------------------------------------------------------------


@patch("subprocess.run")
@patch("main.commit_message_from_diff", return_value="feat: Test commit")
@patch("main.get_diff", return_value="some diff")
@patch("main._install_pre_commit_hooks_if_needed", return_value=None)
def test_main_commit_yes(
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
            ["git", "commit", "-m", "feat: Test commit"],
            check=True,
            capture_output=True,
            text=True,
        )


@patch("main.get_diff", return_value="some diff")
@patch("main.commit_message_from_diff", return_value="feat: Test commit")
@patch("main._install_pre_commit_hooks_if_needed", return_value=None)
def test_main_commit_interactive_yes(
    mock_install_hooks: Mock,
    mock_commit_message: Mock,
    mock_get_diff: Mock,
    mock_input: Mock,
    mock_subprocess_run: Mock,
) -> None:
    """Test the main function with `commit` and interactive 'yes'."""
    mock_input.return_value = "y"
    with patch("sys.argv", ["gai", "commit"]):
        main.main()
        mock_input.assert_called_once()
        mock_subprocess_run.assert_called_with(
            ["git", "commit", "-m", "feat: Test commit"],
            check=True,
            capture_output=True,
            text=True,
        )


@patch("main.get_diff", return_value="some diff")
@patch("main.commit_message_from_diff", return_value="feat: Test commit")
@patch("main._install_pre_commit_hooks_if_needed")
def test_main_commit_interactive_no(
    mock_install_hooks: Mock,
    mock_commit_message: Mock,
    mock_get_diff: Mock,
    mock_input: Mock,
    mock_subprocess_run: Mock,
) -> None:
    """Test the main function with `commit` and interactive 'no'."""
    mock_input.return_value = "n"
    with patch("sys.argv", ["gai", "commit"]):
        main.main()
        mock_input.assert_called_once()
        mock_subprocess_run.assert_not_called()


@patch("main.get_log", return_value="some log")
@patch("main.summarize_commit_log", return_value="Summary of commits")
def test_main_log(mock_summarize: Mock, mock_get_log: Mock) -> None:
    """Test the main function with `log`."""
    with patch("sys.argv", ["gai", "log"]):
        main.main()
        mock_get_log.assert_called_once()
        mock_summarize.assert_called_with("some log")


@patch("main.get_blame", return_value="some blame")
@patch("main.explain_blame_output", return_value="Explanation of blame")
def test_main_blame(mock_explain: Mock, mock_get_blame: Mock) -> None:
    """Test the main function with `blame`."""
    with patch("sys.argv", ["gai", "blame", "file.txt", "1"]):
        main.main()
        mock_get_blame.assert_called_with("file.txt", "1", [])
        mock_explain.assert_called_with("some blame")


@patch("main.get_diff", return_value="")
@patch("main._install_pre_commit_hooks_if_needed")
def test_main_commit_no_changes(
    mock_install_hooks: Mock, mock_get_diff: Mock, mock_subprocess_run: Mock
) -> None:
    """Test the main function with `commit` and no staged changes."""
    with patch("sys.argv", ["gai", "commit"]):
        main.main()
        mock_get_diff.assert_called_once()
        mock_subprocess_run.assert_not_called()


# ------------------------------------------------------------------------------
# Tests for CLI Argument Parsing and Error Handling
# ------------------------------------------------------------------------------


@patch("os.getenv", return_value=None)
def test_missing_api_key(mock_getenv: Mock) -> None:
    """Test that the program exits if the API key is missing."""
    with pytest.raises(SystemExit) as e:
        # We need to reload main to re-evaluate the API_KEY check
        import importlib

        importlib.reload(main)
    assert "GEMINI_API_KEY" in str(e.value)


def test_invalid_command() -> None:
    """Test that the program exits if an invalid command is provided."""
    with patch("sys.argv", ["gai", "invalid-command"]):
        with pytest.raises(SystemExit):
            main.main()


@patch("subprocess.run")
def test_git_passthrough(mock_run: Mock) -> None:
    """Test that unknown commands are passed through to git."""
    with patch("sys.argv", ["gai", "status"]):
        with pytest.raises(SystemExit):
            main.main()
    mock_run.assert_called_with(
        ["git", "status"], capture_output=True, text=True, check=False
    )


@patch("main.get_branch_prefix", return_value="feature")
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
        capture_output=True,
        text=True,
        check=False,
    )


@patch("main.get_branch_prefix", return_value="feature")
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
        capture_output=True,
        text=True,
        check=False,
    )


@patch("main.run")
def test_main_config_set_prefix(mock_run: Mock) -> None:
    """Test the main function with `config --branch-prefix`."""
    with patch("sys.argv", ["gai", "config", "--branch-prefix", "feature"]):
        with patch("argparse.ArgumentParser.parse_known_args") as mock_parse:
            mock_parse.return_value = (
                argparse.Namespace(
                    command="config",
                    branch_prefix="feature",
                    google_api_key=None,
                    gemini_api_key=None,
                ),
                [],
            )
            main.main()
    mock_run.assert_called_with(["git", "config", "gai.branch-prefix", "feature"])


@patch("main.run")
def test_main_config_unset_prefix(mock_run: Mock) -> None:
    """Test the main function with `config --branch-prefix ''`."""
    with patch("sys.argv", ["gai", "config", "--branch-prefix", ""]):
        with patch("argparse.ArgumentParser.parse_known_args") as mock_parse:
            mock_parse.return_value = (
                argparse.Namespace(
                    command="config",
                    branch_prefix="",
                    google_api_key=None,
                    gemini_api_key=None,
                ),
                [],
            )
            main.main()
    mock_run.assert_called_with(["git", "config", "--unset", "gai.branch-prefix"])
