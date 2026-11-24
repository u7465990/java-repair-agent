"""Prompts for the repair agent."""

from __future__ import annotations

from java_agent.eval.runner import Case, CaseResult
from java_agent.verify import VerifyReport


def system_prompt(workdir: str) -> str:
    return f"""You are a Java repair agent working inside a sandboxed repository at {workdir}.

Rules:
- Only change production source files. Never edit tests or build files
  (pom.xml, build.xml, build.gradle).
- Read the failing test first, form a one-sentence hypothesis, then make the smallest fix.
- Use run_tests to check your work; the suite is slow, so batch edits before running it.
- Call finish(summary) only when the target tests pass and you have not introduced regressions.
- If a test fails after your change, inspect the failure instead of guessing.
"""


def user_prompt(
    case: Case,
    baseline: CaseResult,
    attempt: int,
    previous: VerifyReport | None,
) -> str:
    trigger = "\n".join(sorted(baseline.trigger)) or "(unknown)"
    failing = "\n".join(sorted(baseline.report.failing)[:20]) or "(none)"
    previous_block = ""
    if previous is not None:
        previous_block = f"""
Previous attempt failed verification:
{previous.summary()}

Diff so far:
{previous.diff_stat or '(no diff)'}
"""
    return f"""Fix Defects4J bug {case.key}.

Triggering tests (must pass after the fix):
{trigger}

Tests failing at baseline:
{failing}
{previous_block}
Attempt {attempt}. Investigate, patch the source, run the tests, then call finish.
"""
