import pytest
from unittest.mock import ANY
from aig import main


def test_commit(mocker):
    """Test that the commit command calls the correct handler."""
    mocker.patch("sys.argv", ["aig", "commit"])
    mock_handler = mocker.patch("aig._handle_commit")
    main()
    mock_handler.assert_called_once_with(ANY, [])


def test_log(mocker):
    """Test that the log command calls the correct handler."""
    mocker.patch("sys.argv", ["aig", "log"])
    mock_handler = mocker.patch("aig._handle_log")
    main()
    mock_handler.assert_called_once_with(ANY, [])


def test_blame(mocker):
    """Test that the blame command calls the correct handler."""
    mocker.patch("sys.argv", ["aig", "blame", "file.py", "10"])
    mock_handler = mocker.patch("aig._handle_blame")
    main()
    mock_handler.assert_called_once_with(ANY, [])


def test_config(mocker):
    """Test that the config command calls the correct handler."""
    mocker.patch("sys.argv", ["aig", "config"])
    mock_handler = mocker.patch("aig._handle_config")
    main()
    mock_handler.assert_called_once_with(ANY)


def test_test(mocker):
    """Test that the test command calls the correct handler."""
    mocker.patch("sys.argv", "aig test".split())
    mock_handler = mocker.patch("aig._handle_test")
    main()
    mock_handler.assert_called_once_with()


def test_stash(mocker):
    """Test that the stash command calls the correct handler."""
    mocker.patch("sys.argv", ["aig", "stash"])
    mock_handler = mocker.patch("aig._handle_stash")
    main()
    mock_handler.assert_called_once_with(ANY, [])


def test_review(mocker):
    """Test that the review command calls the correct handler."""
    mocker.patch("sys.argv", ["aig", "review"])
    mock_handler = mocker.patch("aig._handle_review")
    main()
    mock_handler.assert_called_once_with(ANY, [])


def test_git_passthrough(mocker):
    """Test that unrecognized commands are passed through to git."""
    mocker.patch("sys.argv", ["aig", "status"])
    mock_passthrough = mocker.patch("aig._handle_git_passthrough")
    mock_passthrough.side_effect = SystemExit
    with pytest.raises(SystemExit):
        main()
    mock_passthrough.assert_called_once_with()


def test_help_message_long(mocker):
    """Test that the --help flag exits the program."""
    mocker.patch("sys.argv", ["aig", "--help"])
    with pytest.raises(SystemExit):
        main()


def test_help_message_short(mocker):
    """Test that the -h flag exits the program."""
    mocker.patch("sys.argv", ["aig", "-h"])
    with pytest.raises(SystemExit):
        main()
