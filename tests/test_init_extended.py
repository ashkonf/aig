import argparse
from unittest.mock import MagicMock, patch
import pytest
from aig import (
    _handle_commit,
    _handle_stash,
    _handle_review,
    _install_pre_commit_hooks_if_needed,
    _handle_git_passthrough,
    main,
)
import subprocess


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
        with pytest.raises(SystemExit):
            _handle_git_passthrough()
        mock_run.assert_called_with(
            ["git", "checkout", "-b", "feature/new-branch"], text=True, check=False
        )


@patch("aig.get_branch_prefix", return_value="feature")
@patch("subprocess.run")
def test_handle_git_passthrough_branch(mock_run, mock_get_branch_prefix):
    with patch("sys.argv", ["aig", "branch", "new-branch"]):
        with pytest.raises(SystemExit):
            _handle_git_passthrough()
        mock_run.assert_called_with(
            ["git", "branch", "feature/new-branch"], text=True, check=False
        )


@patch("subprocess.run", side_effect=FileNotFoundError)
def test_handle_git_passthrough_git_not_found(mock_run):
    with patch("sys.argv", ["aig", "status"]):
        with pytest.raises(SystemExit) as e:
            _handle_git_passthrough()
        assert "git is not installed" in str(e.value)


@patch("argparse.ArgumentParser.parse_known_args")
def test_main_help(mock_parse_args):
    # Mock the parse_known_args to raise SystemExit (which is what argparse does for -h)
    mock_parse_args.side_effect = SystemExit(0)
    with patch("sys.argv", ["aig", "-h"]):
        with pytest.raises(SystemExit):
            main()


@patch("aig.get_unstaged_diff", return_value="")
def test_handle_stash_no_diff(mock_get_diff, mock_args, capsys):
    _handle_stash(mock_args, [])
    captured = capsys.readouterr()
    assert "No changes to stash" in captured.out
