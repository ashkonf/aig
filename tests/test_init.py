import argparse
import subprocess
from unittest.mock import MagicMock, patch
import pytest
from aig import (
    Command,
    _handle_blame,
    _handle_commit,
    _handle_config,
    _handle_log,
    _handle_review,
    _handle_stash,
    _handle_test,
    _install_pre_commit_hooks_if_needed,
    _postprocess_output,
    code_review_from_diff,
    commit_message_from_diff,
    explain_blame_output,
    get_blame,
    get_branch_prefix,
    get_default_branch,
    get_diff,
    get_log,
    run,
    stash_name_from_diff,
    summarize_commit_log,
)


@pytest.fixture
def mock_run():
    with patch("aig.run") as mock:
        yield mock


@pytest.fixture
def mock_ask():
    with patch("aig.ask") as mock:
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


@patch("subprocess.check_output")
def test_run_success(mock_check_output):
    mock_check_output.return_value = b"success"
    assert run(["echo", "success"]) == "success"
    mock_check_output.assert_called_with(["echo", "success"], stderr=subprocess.STDOUT)


@patch("subprocess.check_output", side_effect=FileNotFoundError)
def test_run_file_not_found(mock_check_output):
    with pytest.raises(SystemExit) as e:
        run(["nonexistent"])
    assert "Command not found" in str(e.value)


@patch(
    "subprocess.check_output",
    side_effect=subprocess.CalledProcessError(1, "cmd", output=b"error"),
)
def test_run_called_process_error(mock_check_output):
    with pytest.raises(SystemExit) as e:
        run(["git", "error"])
    assert "Command failed" in str(e.value)


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


def test_get_diff(mock_run):
    mock_run.return_value = "file diff"
    assert get_diff() == "file diff"
    mock_run.assert_called_with(["git", "diff", "--cached"])
    assert get_diff(["--staged"]) == "file diff"
    mock_run.assert_called_with(["git", "diff", "--cached", "--staged"])


def test_get_log(mock_run):
    mock_run.return_value = "commit log"
    assert get_log() == "commit log"
    mock_run.assert_called_with(["git", "log", "-n", "10", "--oneline"])
    assert get_log(["--author=test"]) == "commit log"
    mock_run.assert_called_with(
        ["git", "log", "-n", "10", "--oneline", "--author=test"]
    )


def test_get_blame(mock_run):
    mock_run.return_value = "blame output"
    assert get_blame("file.py", 10) == "blame output"
    mock_run.assert_called_with(["git", "blame", "-L", "10,10", "file.py"])
    assert get_blame("file.py", 10, ["-w"]) == "blame output"
    mock_run.assert_called_with(["git", "blame", "-L", "10,10", "file.py", "-w"])


def test_get_branch_prefix(mock_run):
    mock_run.return_value = "  feature/  "
    assert get_branch_prefix() == "feature/"


def test_get_branch_prefix_error(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
    assert get_branch_prefix() == ""


def test_get_default_branch(mock_run):
    mock_run.return_value = "refs/remotes/origin/main\n"
    assert get_default_branch() == "main"


def test_get_default_branch_error(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
    assert get_default_branch() == "main"


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


@patch("aig.get_diff")
@patch("aig.stash_name_from_diff")
@patch("aig.run")
def test_handle_stash(mock_run, mock_stash_name, mock_get_diff, mock_args):
    mock_get_diff.return_value = "diff"
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


def test_handle_config_set(mock_run, mock_args):
    mock_args.branch_prefix = "feature"
    _handle_config(mock_args)
    mock_run.assert_called_with(["git", "config", "aig.branch-prefix", "feature"])


def test_handle_config_unset(mock_run, mock_args):
    mock_args.branch_prefix = ""
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


@patch("os.getenv")
def test_unknown_provider(mock_getenv):
    mock_getenv.side_effect = lambda key: "unknown" if key == "PROVIDER" else None
    from importlib import reload
    import aig

    with pytest.raises(SystemExit):
        reload(aig)


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
