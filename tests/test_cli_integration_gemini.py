import os
import subprocess
import sys
from pathlib import Path

import pytest


pytestmark = pytest.mark.integration


skip_if_no_key = pytest.mark.skipif(
    os.getenv("GOOGLE_API_KEY") is None and os.getenv("GEMINI_API_KEY") is None,
    reason="GOOGLE_API_KEY/GEMINI_API_KEY not set; skipping CLI Gemini E2E tests",
)


def _project_src_dir() -> str:
    # Resolve to absolute path of this repo's src directory
    return str(Path(__file__).resolve().parents[2] / "src")


def _base_env_with_gemini() -> dict[str, str]:
    env = os.environ.copy()
    # Ensure the aig module is importable when running from a temp repo
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{_project_src_dir()}:{existing_pythonpath}" if existing_pythonpath else _project_src_dir()
    )
    # Prefer a faster/cheaper model for live tests
    env.setdefault("MODEL_NAME", "gemini-1.5-flash-latest")
    return env


def _run(cmd: list[str], cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), env=env, text=True, capture_output=True)


def _init_git_repo(repo_dir: Path) -> None:
    _run(["git", "init"], cwd=repo_dir, env=os.environ.copy())
    _run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, env=os.environ.copy())
    _run(["git", "config", "user.name", "Test User"], cwd=repo_dir, env=os.environ.copy())


@skip_if_no_key
def test_cli_commit_log_blame_with_gemini_e2e(tmp_path: Path):
    env = _base_env_with_gemini()

    # Set up a new git repo with one staged file
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    file_path = repo / "hello.txt"
    file_path.write_text("hello world\n")

    # Stage the file
    res = _run(["git", "add", "hello.txt"], cwd=repo, env=env)
    assert res.returncode == 0, res.stderr

    # Commit using aig with Gemini-generated message
    res = _run([sys.executable, "-m", "aig", "commit", "-y"], cwd=repo, env=env)
    assert res.returncode == 0, res.stderr
    assert "Commit successful" in res.stdout

    # Verify a commit exists
    res = _run(["git", "rev-parse", "HEAD"], cwd=repo, env=env)
    assert res.returncode == 0, res.stderr
    assert res.stdout.strip()

    # Run aig log (summarization uses Gemini)
    res = _run([sys.executable, "-m", "aig", "log"], cwd=repo, env=env)
    assert res.returncode == 0, res.stderr
    assert "Recent commits:" in res.stdout
    assert "▶ Summary:" in res.stdout

    # Blame the first line and get an explanation (uses Gemini)
    res = _run([sys.executable, "-m", "aig", "blame", "hello.txt", "1"], cwd=repo, env=env)
    assert res.returncode == 0, res.stderr
    assert "Blame output:" in res.stdout
    assert "▶ Explanation:" in res.stdout


