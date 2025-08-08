#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
import difflib
import importlib
from enum import Enum
from typing import Callable
from dotenv import load_dotenv

# Optional argcomplete support at import time
try:
    from argcomplete import autocomplete as _argcomplete_autocomplete  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    _argcomplete_autocomplete: Callable | None = None  # type: ignore

load_dotenv()

from .ai import (
    commit_message_from_diff,
    stash_name_from_diff,
    summarize_commit_log,
    explain_blame_output,
    code_review_from_diff,
)

from .git import (
    run,
    get_diff,
    get_unstaged_diff,
    get_log,
    get_blame,
    get_branch_prefix,
)


class Command(str, Enum):
    COMMIT = "commit"
    LOG = "log"
    BLAME = "blame"
    CONFIG = "config"
    TEST = "test"
    STASH = "stash"
    REVIEW = "review"


def _install_pre_commit_hooks_if_needed() -> None:
    """Install pre-commit hooks if they are not already installed."""
    if not os.path.exists(os.path.join(".git", "hooks", "pre-commit")):
        print("▶ pre-commit hooks not found. Installing...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pre_commit", "install"],
                check=True,
                text=True,
            )
            print("✅ pre-commit hooks installed successfully.")
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            error_message: str = str(e)
            print(
                f"⚠️ Could not install pre-commit hooks: {error_message}",
                file=sys.stderr,
            )


def _postprocess_output(text: str) -> str:
    """Replace 'git' with 'aig' in the text."""
    return text.replace("git", "aig").replace("Git", "aig")


def _install_argcomplete_if_missing() -> bool:  # pragma: no cover - interactive optional install
    """Install argcomplete with pip if missing and return True if importable (interactive)."""
    try:
        if importlib.util.find_spec("argcomplete") is not None:  # type: ignore[attr-defined]
            return True
        # Determine environment (venv vs system) to decide on --user
        in_virtualenv: bool = (
            os.environ.get("VIRTUAL_ENV") is not None
            or getattr(sys, "base_prefix", sys.prefix) != sys.prefix
        )

        pip_cmd: list[str] = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--quiet",
            "argcomplete",
        ]
        if not in_virtualenv:
            pip_cmd.insert(4, "--user")

        print("▶ Installing argcomplete for tab-completion...", file=sys.stderr)
        subprocess.run(pip_cmd, check=True, text=True)

        # Re-check availability
        return importlib.util.find_spec("argcomplete") is not None  # type: ignore[attr-defined]
    except Exception:
        return False


def _is_interactive_stdout() -> bool:  # pragma: no cover - environment dependent
    """Return True if stdout is attached to a TTY (interactive)."""
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def _collect_git_subcommands() -> list[str]:  # pragma: no cover - depends on local git help output
    """Collect git subcommands by parsing `git help -a` output (best-effort)."""
    help_out: str = run(["git", "help", "-a"])
    candidates: list[str] = []
    for line in help_out.splitlines():
        stripped: str = line.strip()
        if not stripped or stripped.startswith("usage:"):
            continue
        for token in stripped.split():
            if token.isalpha() and token.islower():
                candidates.append(token)
    # Deduplicate while preserving order
    seen: set[str] = set()
    return [c for c in candidates if not (c in seen or seen.add(c))]


def _suggest_git_subcommands(partial_subcommand: str) -> list[str]:  # pragma: no cover - UX helper
    """Return suggested git subcommands for a partial token, preferring prefix then close matches."""
    try:
        commands_list: list[str] = _collect_git_subcommands()
    except SystemExit:
        return []

    # Prefix matches
    prefix_matches: list[str] = [
        c for c in commands_list if c.startswith(partial_subcommand)
    ]
    # Close matches
    close_matches: list[str] = difflib.get_close_matches(
        partial_subcommand, commands_list, n=5, cutoff=0.6
    )
    suggestions: list[str] = []
    for item in prefix_matches + close_matches:
        if item not in suggestions:
            suggestions.append(item)
    return suggestions


def _maybe_print_suggestions_for_partial(  # pragma: no cover - interactive UX
    partial_subcommand: str, limit: int = 8
) -> None:
    """Print suggestions if any for the given partial subcommand (interactive only)."""
    if (
        not _is_interactive_stdout()
        or not partial_subcommand
        or partial_subcommand.startswith("-")
    ):
        return
    suggestions: list[str] = _suggest_git_subcommands(partial_subcommand)
    if suggestions:
        print("💡 Did you mean:", ", ".join(suggestions[:limit]))


def _enable_argcomplete_if_possible(parser: argparse.ArgumentParser) -> None:  # pragma: no cover - interactive optional completion
    """Enable argcomplete on the parser, attempting install if missing (interactive shells only)."""
    if not _is_interactive_stdout():
        return

    autocomplete_func: Callable | None = _argcomplete_autocomplete
    if autocomplete_func is None:
        if _install_argcomplete_if_missing():
            try:
                module = importlib.import_module("argcomplete")
                autocomplete_func = getattr(module, "autocomplete", None)
            except Exception:
                autocomplete_func = None

    try:
        if callable(autocomplete_func):  # type: ignore[call-arg]
            autocomplete_func(parser)  # type: ignore[misc]
        else:
            print(
                "💡 Tip: Install and enable argcomplete for tab completion: "
                "pip install argcomplete && activate-global-python-argcomplete",
                file=sys.stderr,
            )
    except Exception:
        # Ignore argcomplete runtime errors
        pass


def _handle_test() -> None:
    """Handle the 'test' command."""
    _install_pre_commit_hooks_if_needed()
    print("▶ Running pre-commit hooks...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pre_commit", "run", "--all-files"],
            check=True,
        )
        print("✅ Pre-commit hooks passed.")
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        sys.exit(f"❌ Pre-commit hooks failed with error: {e}")


def _generate_commit_message_from_staged_changes(
    extra_args: list[str],
) -> str | None:
    """Return an AI-generated commit message for staged changes, or None if no diff."""
    diff: str = get_diff(extra_args)
    if not diff.strip():
        return None
    return commit_message_from_diff(diff)


def _prepare_commit_message(
    args: argparse.Namespace, extra_args: list[str]
) -> tuple[str | None, bool]:
    """Prepare the commit message and return (message or None, provided_by_user)."""
    if getattr(args, "message", None):
        return args.message, True

    msg: str | None = _generate_commit_message_from_staged_changes(extra_args)
    if msg is None:
        print("⚠️ No staged changes found.")
        return None, False

    print("\nSuggested commit message:\n")
    print(msg)
    return msg, False


def _confirm_commit(args: argparse.Namespace, message_was_provided: bool) -> bool:
    """Return True if we should proceed with committing."""
    if message_was_provided:
        return True
    return args.yes or input("\nUse this commit message? [Y/n] ").strip().lower() in (
        "",
        "y",
        "yes",
    )


def _run_git_commit(msg: str, args: argparse.Namespace, extra_args: list[str]) -> None:
    """Execute `git commit` with the given message and args, handling errors."""
    try:
        commit_cmd: list[str] = ["git", "commit"]
        env: dict[str, str] = os.environ.copy()
        if getattr(args, "date", None):
            commit_cmd.extend(["--date", args.date])
            env["GIT_AUTHOR_DATE"] = args.date
            env["GIT_COMMITTER_DATE"] = args.date
        commit_cmd.extend(["-F", "-"])
        if getattr(args, "yes", False):
            commit_cmd.append("--yes")
        commit_cmd.extend(extra_args)
        subprocess.run(
            commit_cmd,
            input=msg,
            check=True,
            text=True,
            env=env,
        )
        print("✅ Commit successful.")
    except subprocess.CalledProcessError as e:
        print("❌ Commit failed.", file=sys.stderr)
        if e.stdout:
            print(_postprocess_output(e.stdout), file=sys.stderr)
        if e.stderr:
            print(_postprocess_output(e.stderr), file=sys.stderr)
        sys.exit(1)


def _handle_commit(args: argparse.Namespace, extra_args: list[str]) -> None:
    """Handle the 'commit' command."""
    _install_pre_commit_hooks_if_needed()

    msg, message_was_provided = _prepare_commit_message(args, extra_args)
    if not msg:
        return

    if not _confirm_commit(args, message_was_provided):
        return

    _run_git_commit(msg, args, extra_args)


def _handle_stash(args: argparse.Namespace, extra_args: list[str]) -> None:
    """Handle the 'stash' command."""
    if args.message:
        msg: str = args.message
    else:
        diff: str = get_unstaged_diff(extra_args)
        if not diff.strip():
            print("⚠️ No changes to stash.")
            return
        msg: str = stash_name_from_diff(diff)
        print("\nSuggested stash message:\n")
        print(msg)

    # If message is provided, don't ask for confirmation
    if args.message:
        should_stash: bool = True
    else:
        should_stash: bool = args.yes or input(
            "\nUse this stash message? [Y/n] "
        ).strip().lower() in ("", "y", "yes")

    if should_stash:
        run(["git", "stash", "push", "-m", msg] + extra_args)
        print("✅ Stashed successfully.")


def _handle_log(args: argparse.Namespace, extra_args: list[str]) -> None:
    """Handle the 'log' command."""
    log: str = get_log(extra_args)
    print("\nRecent commits:\n")
    print(_postprocess_output(log))
    summary: str = summarize_commit_log(log)
    print("\n▶ Summary:\n")
    print(summary)


def _handle_blame(args: argparse.Namespace, extra_args: list[str]) -> None:
    """Handle the 'blame' command."""
    blame: str = get_blame(args.file, args.line, extra_args)
    print("\nBlame output:\n")
    print(_postprocess_output(blame))
    explanation: str = explain_blame_output(blame)
    print("\n▶ Explanation:\n")
    print(explanation)


def _handle_review(args: argparse.Namespace, extra_args: list[str]) -> None:
    """Handle the 'review' command."""
    diff: str = get_diff(extra_args)
    if not diff.strip():
        print("⚠️ No staged changes found to review.")
        return
    review: str = code_review_from_diff(diff)
    print("\n▶ Code Review:\n")
    print(review)


def _handle_config(args: argparse.Namespace) -> None:
    """Handle the 'config' command."""
    if args.branch_prefix is not None:
        if args.branch_prefix:
            run(["git", "config", "aig.branch-prefix", args.branch_prefix])
            print(f"✅ Branch prefix set to: {args.branch_prefix}")
        else:
            run(["git", "config", "--unset", "aig.branch-prefix"])
            print("✅ Branch prefix unset.")


def _handle_git_passthrough() -> None:
    """Pass through the command to git."""

    # Handle branch prefix rewriting for `aig checkout -b <branch>` or `aig branch <branch>`
    if len(sys.argv) > 1 and sys.argv[1] in ("checkout", "branch"):
        prefix: str | None = get_branch_prefix()
        if prefix:
            if sys.argv[1] == "checkout" and len(sys.argv) > 3 and sys.argv[2] == "-b":
                sys.argv[3] = f"{prefix}/{sys.argv[3]}"
            elif sys.argv[1] == "branch" and len(sys.argv) > 2:
                sys.argv[2] = f"{prefix}/{sys.argv[2]}"

    # Inline suggestions for partial git subcommands (interactive only)
    try:
        # Replace "git" with "aig" in the command's output
        # Before executing, if running interactively and the first token looks like
        # a partial/unknown git command, suggest likely matches.
        if len(sys.argv) > 1:
            _maybe_print_suggestions_for_partial(sys.argv[1])

        result: subprocess.CompletedProcess[str] = subprocess.run(
            ["git"] + sys.argv[1:], text=True, check=False
        )
        sys.exit(result.returncode)
    except FileNotFoundError:
        sys.exit("❌ git is not installed or not in your PATH.")


def main() -> None:
    """Main entry point for the CLI."""

    if len(sys.argv) > 1:
        if sys.argv[1] not in {c.value for c in Command}:
            # Let argparse handle help and version requests
            if sys.argv[1] not in [
                "-h",
                "--help",
                "-v",
                "--version",
            ]:
                _handle_git_passthrough()

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="aig", description="AI-enhanced git wrapper"
    )
    # Enable argcomplete-based completion if available; try to install if missing
    _enable_argcomplete_if_possible(parser)

    subs: argparse._SubParsersAction = parser.add_subparsers(
        dest="command", required=True
    )

    commit_p: argparse.ArgumentParser = subs.add_parser(
        Command.COMMIT.value, help="Generate a commit message from staged changes"
    )
    commit_p.add_argument(
        "-y", "--yes", action="store_true", help="Commit without confirmation"
    )
    commit_p.add_argument(
        "-m", "--message", help="Provide a commit message instead of generating one"
    )
    commit_p.add_argument("--date", help="Override the date of the commit")

    stash_p: argparse.ArgumentParser = subs.add_parser(
        Command.STASH.value, help="Generate a stash message from staged changes"
    )
    stash_p.add_argument(
        "-y", "--yes", action="store_true", help="Stash without confirmation"
    )
    stash_p.add_argument(
        "-m", "--message", help="Provide a stash message instead of generating one"
    )
    subs.add_parser(Command.LOG.value, help="Summarize the last 10 commits")
    subs.add_parser(Command.TEST.value, help="Run pre-commit hooks on all files")
    subs.add_parser(
        Command.REVIEW.value, help="Request a code review on staged changes"
    )

    blame_p: argparse.ArgumentParser = subs.add_parser(
        Command.BLAME.value, help="Explain a line change"
    )
    blame_p.add_argument("file", help="Path to the file")
    blame_p.add_argument("line", help="Line number")

    config_p: argparse.ArgumentParser = subs.add_parser(
        Command.CONFIG.value, help="Set configuration for aig"
    )
    config_p.add_argument(
        "--branch-prefix",
        help="Set a prefix for new branches created with `aig checkout -b`",
    )

    args: argparse.Namespace
    extra_args: list[str]
    args, extra_args = parser.parse_known_args()

    handlers: dict[Command, Callable[..., None]] = {
        Command.COMMIT: _handle_commit,
        Command.STASH: _handle_stash,
        Command.LOG: _handle_log,
        Command.BLAME: _handle_blame,
        Command.CONFIG: _handle_config,
        Command.TEST: _handle_test,
        Command.REVIEW: _handle_review,
    }
    if args.command in (
        Command.COMMIT,
        Command.LOG,
        Command.BLAME,
        Command.STASH,
        Command.REVIEW,
    ):
        handlers[args.command](args, extra_args)
    elif args.command in (Command.TEST,):
        handlers[args.command]()
    else:
        handlers[args.command](args)
