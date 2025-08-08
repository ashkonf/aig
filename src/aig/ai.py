import sys
from typing import Callable
from . import google, openai, anthropic
from dotenv import load_dotenv


load_dotenv()


ask: Callable
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
        "You are an expert developer and git historian acting as the steward of long‑term project health. "
        "Write a concise, clear git commit message "
        "(imperative mood, ≤ 72 chars in the subject) for the following diff. "
        "Start the subject line with a single, relevant, positive emoji. The subject must state the user‑visible outcome or intent, not the implementation. "
        "Adopt multiple perspectives: future maintainers scanning history, release notes authors, and incident responders triaging regressions months later. "
        "Make the subject specific and outcome‑oriented; prefer verbs that describe what changes for users or systems (e.g., 'Speed up', 'Harden', 'Simplify'). "
        "If genuinely helpful, include a short body after a blank line: explain the motivation and rationale, the before/after behavior, notable trade‑offs, risks, and potential follow‑ups. "
        "Reference issue/PR IDs if present; note BREAKING CHANGE with migration guidance when applicable; call out config or schema changes explicitly. "
        "Prefer present tense, avoid redundant words, avoid restating file names or diffs, and avoid noisy boilerplate. "
        "If this is a revert, start with 'Revert:' and briefly state the cause. If it’s primarily tests or docs, say so up front. "
        "When scope is broad, summarize the theme and mention the most affected module/component. Optimize for skimmability and correctness.\n\n"
        f"<diff>\n{diff}\n</diff>"
    )
    return ask(prompt, max_tokens=60)


def stash_name_from_diff(diff: str) -> str:
    """Return a stash name from a diff."""
    prompt: str = (
        "You are an expert developer and release engineer curating a tidy local queue. Write a concise, clear stash message "
        "(imperative mood, ≤\u00a072 chars in the subject) for the following diff. "
        "Start the subject line with a single, relevant, positive emoji. The subject should be memorable and searchable, capturing intent and scope (component/module) rather than implementation details. "
        "Think from the perspectives of your future self and teammates scanning dozens of stashes: favor clarity, disambiguation, and quick recall. "
        "When helpful, include 2–4 terse tags in brackets like [refactor], [perf], [wip], [doc], [security], [migration] to aid retrieval, while staying within the overall length constraint. "
        "Avoid sensitive data and secrets; do not include stack traces or personally identifiable information. "
        "If the change is experimental or risky, hint at that in the subject via a tag (e.g., [exp], [spike]). \n\n"
        f"<diff>\n{diff}\n</diff>"
    )
    return ask(prompt, max_tokens=60)


def summarize_commit_log(log: str) -> str:
    """Return a summary of a commit log using the selected provider."""
    prompt: str = (
        "You are an expert developer and release notes editor. Summarize the following aig commit log into "
        "bullet points, using relevant, positive emojis. Focus on key changes and group related commits where sensible. "
        "Adopt multiple perspectives: product stakeholders, on‑call engineers, and future maintainers trying to understand the arc of the work. "
        "Merge duplicate/noisy commits (e.g., 'fix lint', 'update lockfile'); cluster by feature area or subsystem; call out breaking changes, migrations, deprecations, or configuration updates. "
        "Prefer 5–10 bullets, each ≤ 20 words, action‑led and past‑tense. Include notable PR/issue numbers when present, and explicitly mention user‑visible impact or risk when meaningful. "
        "End with one Overall bullet capturing the theme or narrative of the release window. If the log is empty or non‑informative, output a single bullet stating that. "
        "Be precise, remove noise, and optimize for quick scanning by humans.\n\n"
        f"<log>\n{log}\n</log>"
    )
    return ask(prompt, max_tokens=150)


def explain_blame_output(blame: str) -> str:
    """Return an explanation of a blame output using the selected provider."""
    prompt: str = (
        "You are an expert developer and code archeologist. Explain why this line was changed based on "
        "the git blame output and commit hash details. Start with a relevant, positive "
        "emoji and keep it under 120 words: Provide the likely motivation and the behavior before vs after; relate to the commit message and nearby context; "
        "note potential side effects/risks and how to mitigate; if ambiguous, give the most probable rationale and an alternative hypothesis. "
        "Adopt perspectives of a reviewer reading history, an on‑call engineer debugging, a maintainer planning refactors, a security engineer assessing risk, and a product engineer considering user impact. "
        "Consider signals such as linked issues/PRs, surrounding hunks and nearby functions, module ownership, test changes, deprecations/migrations, upstream API shifts, feature flags, telemetry, and performance characteristics. "
        "Reference the commit hash briefly and avoid restating the blame line verbatim. Offer one concrete follow‑up or validation step (e.g., targeted test, log/metrics check, rollout or rollback plan, alert).\n\n"
        f"<blame>\n{blame}\n</blame>"
    )
    return ask(prompt, max_tokens=100)


def code_review_from_diff(diff: str) -> str:
    """Return a code review from a diff."""
    prompt: str = (
        "You are an expert developer conducting a thoughtful, high‑leverage review. Review the following code changes and "
        "provide feedback. Focus on identifying potential bugs, performance "
        "issues, and areas for improvement. Use a positive and constructive "
        "tone, with relevant emojis. Adopt perspectives of: the author seeking guidance, a maintainer ensuring long‑term quality, and an SRE considering operability. "
        "Structure your review as: Must‑fix (correctness, security, error handling); Should‑fix (performance, memory, I/O, algorithmic complexity); "
        "Nice‑to‑have (readability, naming, style, docs); Tests (missing cases, property/fuzz, fixtures); DX (build steps, scripts, CI, dependency hygiene). "
        "Offer concrete, minimally invasive suggestions and quick wins; point to safer alternatives when risk is high. "
        "Note any regressions, edge cases, concurrency/ordering pitfalls, resource leaks, and backward‑compatibility concerns. "
        "If the diff is excellent, acknowledge strengths and explain why (design clarity, simplicity, invariants, tests, performance). "
        "Where helpful, reference principles (idempotency, single responsibility, fail‑fast, input validation) and suggest small refactors, not rewrites.\n\n"
        f"<diff>\n{diff}\n</diff>"
    )
    return ask(prompt, max_tokens=1000)
