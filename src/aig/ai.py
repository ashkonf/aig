import sys
from typing import Callable
from . import google, openai, anthropic


ask: Callable[[str, int], str]

if google.is_available():
    google.init()
    ask = google.ask_gemini
elif openai.is_available():
    openai.init()
    ask = openai.ask_openai
elif anthropic.is_available():
    anthropic.init()
    ask = anthropic.ask_anthropic
else:
    sys.exit("❌ No API keys found in environment variables.")


def commit_message_from_diff(diff: str) -> str:
    """Return a commit message from a diff using the selected provider."""
    prompt: str = (
        "You are an expert developer. Write a concise, clear git commit message "
        "(imperative mood, ≤ 72 chars in the subject) for the following diff. "
        "Start the subject line with a single, relevant, positive emoji.\n\n"
        f"<diff>\n{diff}\n</diff>"
    )
    return ask(prompt, max_tokens=60)


def stash_name_from_diff(diff: str) -> str:
    """Return a stash name from a diff."""
    prompt: str = (
        "You are an expert developer. Write a concise, clear stash message "
        "(imperative mood, ≤\u00a072 chars in the subject) for the following diff. "
        "Start the subject line with a single, relevant, positive emoji.\n\n"
        f"<diff>\n{diff}\n</diff>"
    )
    return ask(prompt, max_tokens=60)


def summarize_commit_log(log: str) -> str:
    """Return a summary of a commit log using the selected provider."""
    prompt: str = (
        "You are an expert developer. Summarize the following aig commit log into "
        "bullet points, using relevant, positive emojis. Focus on key changes and group "
        "related commits where sensible:\n\n"
        f"<log>\n{log}\n</log>"
    )
    return ask(prompt, max_tokens=150)


def explain_blame_output(blame: str) -> str:
    """Return an explanation of a blame output using the selected provider."""
    prompt: str = (
        "You are an expert developer. Explain why this line was changed based on "
        "the git blame output and commit hash details. Start with a relevant, positive "
        "emoji and keep it under 120 words:\n\n"
        f"<blame>\n{blame}\n</blame>"
    )
    return ask(prompt, max_tokens=100)


def code_review_from_diff(diff: str) -> str:
    """Return a code review from a diff."""
    prompt: str = (
        "You are an expert developer. Review the following code changes and "
        "provide feedback. Focus on identifying potential bugs, performance "
        "issues, and areas for improvement. Use a positive and constructive "
        "tone, with relevant emojis:\n\n"
        f"<diff>\n{diff}\n</diff>"
    )
    return ask(prompt, max_tokens=1000)
