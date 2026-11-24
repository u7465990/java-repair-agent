"""Prompts for the repair agent."""

from __future__ import annotations

from java_agent.eval.runner import Case, CaseResult
from java_agent.verify import VerifyReport


def system_prompt(workdir: str, skills_index: str = "") -> str:
    skills_block = ""
    if skills_index:
        skills_block = f"""
Available skills (call load_skill with the name before starting a matching task):
{skills_index}
"""
    return f"""You are a Java repair agent working inside a sandboxed repository at {workdir}.
{skills_block}

Rules:
- Only change production source files. Never edit tests or build files
  (pom.xml, build.xml, build.gradle).
- Read the failing test first, form a one-sentence hypothesis, then make the smallest fix.
- Use run_tests to check your work; the suite is slow, so batch edits before running it.
- Do not call finish before you have edited at least one source file.
- Verification rejects changes outside src/main, any test/build file, more than
  5 files, or more than 400 changed lines.
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
    excerpt = baseline.report.output.strip()
    if len(excerpt) > 1500:
        excerpt = excerpt[-1500:]
    previous_block = ""
    if previous is not None:
        previous_block = f"""
Previous attempt failed verification:
{previous.summary()}

Previous test/compile output (tail):
{previous.output[-1500:]}

Diff so far:
{previous.diff_stat or '(no diff)'}
"""
    return f"""Fix Defects4J bug {case.key}.

Triggering tests (must pass after the fix):
{trigger}

Tests failing at baseline:
{failing}

Baseline test output (tail):
{excerpt}
{previous_block}
Attempt {attempt}. Investigate, patch the source, run the tests, then call finish.
"""
