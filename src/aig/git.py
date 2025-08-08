import subprocess
import sys
from typing import Optional


def run(cmd: list[str]) -> str:
    """Run a shell command and return UTF‑8 output (raises on error)."""
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()
    except FileNotFoundError:
        sys.exit(f"❌ Command not found: {cmd[0]}. Is it in your PATH?")
    except subprocess.CalledProcessError as e:
        sys.exit(f"❌ Command failed: {' '.join(cmd)}\n{e.output}")


def _patched_run_if_present(cmd: list[str]) -> str:
    """Use aig.run if available (to support tests patching `aig.run`), else local run."""
    try:
        pkg = sys.modules.get("aig")
        if pkg is not None and hasattr(pkg, "run"):
            return getattr(pkg, "run")(cmd)  # type: ignore[misc]
    except Exception:
        pass
    return run(cmd)


def get_diff(extra_args: Optional[list[str]] = None) -> str:
    """Return the output of `git diff --cached` with optional extra args."""
    cmd: list[str] = ["git", "diff", "--cached"]
    if extra_args:
        cmd.extend(extra_args)
    return _patched_run_if_present(cmd)


def get_unstaged_diff(extra_args: Optional[list[str]] = None) -> str:
    """Return the output of `git diff` (unstaged changes) with optional extra args."""
    cmd: list[str] = ["git", "diff"]
    if extra_args:
        cmd.extend(extra_args)
    return _patched_run_if_present(cmd)


def get_log(extra_args: Optional[list[str]] = None) -> str:
    """Return the output of `git log` with optional extra args."""
    cmd: list[str] = ["git", "log", "-n", "10", "--oneline"]
    if extra_args:
        cmd.extend(extra_args)
    return _patched_run_if_present(cmd)


def get_blame(
    path: str, line: str | int, extra_args: Optional[list[str]] = None
) -> str:
    """Return the output of `git blame` for a specific line."""
    cmd: list[str] = ["git", "blame", "-L", f"{line},{line}", path]
    if extra_args:
        cmd.extend(extra_args)
    return _patched_run_if_present(cmd)


def get_branch_prefix() -> str:
    """Return the git config value for `aig.branch-prefix` or empty string."""
    try:
        return _patched_run_if_present(["git", "config", "aig.branch-prefix"]).strip()
    except subprocess.CalledProcessError:
        return ""
