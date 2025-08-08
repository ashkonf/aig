import subprocess
from unittest.mock import patch
import pytest

from aig.git import run, get_diff, get_unstaged_diff, get_log, get_blame, get_branch_prefix


# run() tests (moved from test_init.py and test_edge_cases_comprehensive.py)
@patch("subprocess.check_output")
def test_run_success(mock_check_output):
    mock_check_output.return_value = b"success"
    assert run(["echo", "success"]) == "success"
    mock_check_output.assert_called_with(["echo", "success"], stderr=subprocess.STDOUT)


@patch("subprocess.check_output", side_effect=FileNotFoundError)
def test_run_file_not_found(_mock_check_output):
    with pytest.raises(SystemExit) as e:
        run(["nonexistent"])
    assert "Command not found" in str(e.value)


@patch(
    "subprocess.check_output",
    side_effect=subprocess.CalledProcessError(1, "cmd", output=b"error"),
)
def test_run_called_process_error(_mock_check_output):
    with pytest.raises(SystemExit) as e:
        run(["git", "error"])
    assert "Command failed" in str(e.value)


@patch("subprocess.check_output")
def test_run_with_unicode_output(mock_check_output):
    mock_check_output.return_value = "✅ Unicode output 🎉".encode("utf-8")
    result = run(["git", "log"])
    assert result == "✅ Unicode output 🎉"


@patch("subprocess.check_output")
def test_run_with_empty_output(mock_check_output):
    mock_check_output.return_value = b""
    result = run(["git", "status"])
    assert result == ""


# git plumbing tests (moved from test_init.py and test_edge_cases_comprehensive.py)
@patch("aig.run", return_value="file diff")
def test_get_diff_basic(mock_run):
    assert get_diff() == "file diff"
    mock_run.assert_called_with(["git", "diff", "--cached"])


@patch("aig.run", return_value="file diff")
def test_get_diff_with_args(mock_run):
    assert get_diff(["--staged"]) == "file diff"
    mock_run.assert_called_with(["git", "diff", "--cached", "--staged"])


@patch("aig.run", return_value="commit log")
def test_get_log(mock_run):
    assert get_log() == "commit log"
    mock_run.assert_called_with(["git", "log", "-n", "10", "--oneline"])
    assert get_log(["--author=test"]) == "commit log"
    mock_run.assert_called_with([
        "git",
        "log",
        "-n",
        "10",
        "--oneline",
        "--author=test",
    ])


@patch("aig.run", return_value="blame output")
def test_get_blame(mock_run):
    assert get_blame("file.py", 10) == "blame output"
    mock_run.assert_called_with(["git", "blame", "-L", "10,10", "file.py"])
    assert get_blame("file.py", 10, ["-w"]) == "blame output"
    mock_run.assert_called_with(["git", "blame", "-L", "10,10", "file.py", "-w"])


@patch("aig.git._patched_run_if_present", side_effect=subprocess.CalledProcessError(1, "git config"))
def test_get_branch_prefix_exception_handling(_mock_patched_run):
    result = get_branch_prefix()
    assert result == ""


@patch("aig.run", return_value="  feature/  \n")
def test_get_branch_prefix_with_whitespace(mock_run):
    result = get_branch_prefix()
    assert result == "feature/"


# Additional edge plumbing tests
@patch("aig.run", return_value="test diff content")
def test_get_diff_empty_extra_list(mock_run):
    result = get_diff([])
    mock_run.assert_called_with(["git", "diff", "--cached"])
    assert result == "test diff content"


@patch("aig.run", return_value="stash diff")
def test_get_unstaged_diff(mock_run):
    result = get_unstaged_diff(["--name-only"])  # exercise function
    mock_run.assert_called_with(["git", "diff", "--name-only"])
    assert result == "stash diff"


@patch("aig.run", return_value="x" * 50000)
def test_very_long_command_output(mock_run):
    result = get_log()
    assert len(result) == 50000

