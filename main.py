#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
from enum import Enum
from typing import Callable
import google.generativeai as genai
from dotenv import load_dotenv

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

load_dotenv()

API_KEY: str | None = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    sys.exit("❌ Set GEMINI_API_KEY or GOOGLE_API_KEY in your environment.")

genai.configure(api_key=API_KEY)
MODEL_NAME: str = os.getenv("MODEL_NAME") or "gemini-2.5-pro-latest"  # use a current, valid model
_model: genai.GenerativeModel = genai.GenerativeModel(MODEL_NAME)


class Command(str, Enum):
    COMMIT = "commit"
    LOG = "log"
    BLAME = "blame"


# ──────────────────────────────────────────────────────────────────────────────
# Helper: shell
# ──────────────────────────────────────────────────────────────────────────────


def run(cmd: list[str]) -> str:
    """Run a shell command and return UTF‑8 output (raises on error)."""
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()
    except FileNotFoundError:
        sys.exit(f"❌ Command not found: {cmd[0]}. Is it in your PATH?")
    except subprocess.CalledProcessError as e:
        sys.exit(f"❌ Command failed: {' '.join(cmd)}\n{e.output.decode()}")


# ──────────────────────────────────────────────────────────────────────────────
# Git plumbing
# ──────────────────────────────────────────────────────────────────────────────


def get_diff(extra_args: list[str] | None = None) -> str:
    """Return the output of `git diff --cached` with optional extra args."""
    cmd = ["git", "diff", "--cached"]
    if extra_args:
        cmd.extend(extra_args)
    return run(cmd)


def get_log(extra_args: list[str] | None = None) -> str:
    """Return the output of `git log` with optional extra args."""
    cmd = ["git", "log", "-n", "10", "--oneline"]
    if extra_args:
        cmd.extend(extra_args)
    return run(cmd)


def get_blame(path: str, line: str | int, extra_args: list[str] | None = None) -> str:
    """Return the output of `git blame` for a specific line."""
    cmd = ["git", "blame", "-L", f"{line},{line}", path]
    if extra_args:
        cmd.extend(extra_args)
    return run(cmd)


def get_branch_prefix() -> str:
    """Return the git config value for `git.branch-prefix` or empty string."""
    try:
        return run(["git", "config", "git.branch-prefix"]).strip()
    except subprocess.CalledProcessError:
        return ""


# ──────────────────────────────────────────────────────────────────────────────
# Gemini wrappers
# ──────────────────────────────────────────────────────────────────────────────


def ask_gemini(prompt: str, max_tokens: int = 400) -> str:
    """Single‑shot prompt to Gemini, returns trimmed text."""
    try:
        response = _model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": max_tokens,
            },
        )
        return response.text.strip()
    except Exception as e:
        if "API key not valid" in str(e):
            sys.exit("❌ Gemini API key is not valid. Please check your .env file.")
        sys.exit(f"❌ Gemini API error: {e}")


def commit_message_from_diff(diff: str) -> str:
    """Return a commit message from a diff using Gemini."""
    prompt = (
        "You are an expert developer. Write a concise, clear gai commit message "
        "(imperative mood, ≤ 72 chars in the subject) for the following diff. "
        "Start the subject line with a single, relevant, positive emoji.\n\n"
        f"<diff>\n{diff}\n</diff>"
    )
    return ask_gemini(prompt, max_tokens=60)


def summarize_commit_log(log: str) -> str:
    """Return a summary of a commit log using Gemini."""
    prompt = (
        "You are an expert developer. Summarize the following gai commit log into "
        "bullet points, using relevant, positive emojis. Focus on key changes and group "
        "related commits where sensible:\n\n"
        f"<log>\n{log}\n</log>"
    )
    return ask_gemini(prompt, max_tokens=150)


def explain_blame_output(blame: str) -> str:
    """Return an explanation of a blame output using Gemini."""
    prompt = (
        "You are an expert developer. Explain why this line was changed based on "
        "the gai blame output and commit hash details. Start with a relevant, positive "
        "emoji and keep it under 120 words:\n\n"
        f"<blame>\n{blame}\n</blame>"
    )
    return ask_gemini(prompt, max_tokens=100)


def _install_pre_commit_hooks_if_needed():
    """Install pre-commit hooks if they are not already installed."""
    if not os.path.exists(os.path.join(".git", "hooks", "pre-commit")):
        print("▶ pre-commit hooks not found. Installing...")
        try:
            subprocess.run(
                ["uv", "run", "pre-commit", "install"],
                check=True,
                capture_output=True,
                text=True,
            )
            print("✅ pre-commit hooks installed successfully.")
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            error_message = e.stderr if hasattr(e, "stderr") else str(e)
            print(f"⚠️ Could not install pre-commit hooks: {error_message}", file=sys.stderr)


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────


def _replace_git_with_gai(text: str) -> str:
    """Replace 'git' with 'gai' in the text."""
    return text.replace("git", "gai").replace("Git", "gai")


def _handle_commit(args: argparse.Namespace, extra_args: list[str]) -> None:
    """Handle the 'commit' command."""
    _install_pre_commit_hooks_if_needed()

    diff = get_diff(extra_args)
    if not diff.strip():
        print("⚠️ No staged changes found.")
        return
    msg = commit_message_from_diff(diff)
    print("\nSuggested commit message:\n")
    print(msg)

    should_commit = args.yes or input(
        "\nUse this commit message? [Y/n] "
    ).strip().lower() in ("", "y", "yes")
    if should_commit:
        result = subprocess.run(
            ["git", "commit", "-m", msg],
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(_replace_git_with_gai(result.stdout))
        if result.stderr:
            print(_replace_git_with_gai(result.stderr), file=sys.stderr)
        print("✅ Commit successful.")


def _handle_log(args: argparse.Namespace, extra_args: list[str]) -> None:
    """Handle the 'log' command."""
    log = get_log(extra_args)
    print("\nRecent commits:\n")
    print(_replace_git_with_gai(log))
    summary = summarize_commit_log(log)
    print("\n▶ Summary:\n")
    print(summary)


def _handle_blame(args: argparse.Namespace, extra_args: list[str]) -> None:
    """Handle the 'blame' command."""
    blame = get_blame(args.file, args.line, extra_args)
    print("\nBlame output:\n")
    print(_replace_git_with_gai(blame))
    explanation = explain_blame_output(blame)
    print("\n▶ Explanation:\n")
    print(explanation)


def _handle_git_passthrough():
    if sys.argv[1] in ("checkout", "branch"):
        # Branch prefix rewriting for `gai checkout -b` or `gai branch`
        prefix = get_branch_prefix()
        if prefix and len(sys.argv) >= 3:
            # `gai checkout -b <branch>`
            if sys.argv[1] == "checkout" and sys.argv[2] == "-b":
                if len(sys.argv) > 3:
                    sys.argv[3] = f"{prefix}/{sys.argv[3]}"
            # `gai branch <branch>`
            else:
                sys.argv[2] = f"{prefix}/{sys.argv[2]}"

    try:
        # Replace "git" with "gai" in the command's output
        result = subprocess.run(
            ["git"] + sys.argv[1:], capture_output=True, text=True, check=False
        )
        if result.stdout:
            print(_replace_git_with_gai(result.stdout))
        if result.stderr:
            print(
                _replace_git_with_gai(result.stderr),
                file=sys.stderr,
            )
        if result.returncode != 0:
            sys.exit(result.returncode)
    except FileNotFoundError:
        sys.exit("❌ git is not installed or not in your PATH.")


def main() -> None:
    """Main entry point for the CLI."""

    # If the first argument is not a special `gai` command, pass it through to git:
    if len(sys.argv) > 1 and sys.argv[1] not in {c.value for c in Command}:
        _handle_git_passthrough()
        return

    parser = argparse.ArgumentParser(
        prog="gai", description="AI‑enhanced git wrapper"
    )
    subs = parser.add_subparsers(dest="command", required=True)

    commit_p = subs.add_parser(
        Command.COMMIT, help="Generate a commit message from staged changes"
    )
    commit_p.add_argument(
        "-y", "--yes", action="store_true", help="Commit without confirmation"
    )
    commit_p.add_argument(
        "-m", "--message", help="Provide a commit message instead of generating one"
    )
    subs.add_parser(Command.LOG, help="Summarize the last 10 commits")

    blame_p = subs.add_parser(Command.BLAME, help="Explain a line change")
    blame_p.add_argument("file", help="Path to the file")
    blame_p.add_argument("line", help="Line number")

    args, extra_args = parser.parse_known_args()

    handlers: dict[Command, Callable[[argparse.Namespace, list[str]], None]] = {
        Command.COMMIT: _handle_commit,
        Command.LOG: _handle_log,
        Command.BLAME: _handle_blame,
    }
    handlers[args.command](args, extra_args)


if __name__ == "__main__":
    main()
