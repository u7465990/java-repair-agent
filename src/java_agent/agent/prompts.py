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
- Every attempt must edit at least one file under src/main; reading alone does not count.
- Do not call finish before you have edited at least one source file.
- Verification rejects changes outside src/main, any test/build file, more than
  5 files, or more than 400 changed lines.
- Call finish(summary) only when the target tests pass and you have not introduced regressions.
- If a test fails after your change, inspect the failure instead of guessing.
"""


def next_action_hint(previous: VerifyReport) -> str:
    """Turn the previous failure kind into one concrete instruction."""
    if previous.kind == "no_changes":
        return (
            "You did not modify any file under src/main. This round you MUST edit at least "
            "one production source file before calling finish."
        )
    if previous.kind == "audit_violation":
        violations = "; ".join(previous.audit.violations) or "diff rejected"
        return (
            f"Your diff was rejected by verification: {violations}. "
            "Only change files under src/main; never touch tests, build files, or scratch data."
        )
    if previous.kind == "compile_error":
        return (
            "The project does not compile. Fix the exact compile error shown above first; "
            "do not rewrite unrelated code."
        )
    if previous.kind == "trigger_failing":
        names = ", ".join(sorted(previous.failing & previous.trigger))
        return (
            f"These triggering tests still fail: {names}. "
            "Read their stack traces and change the code that produces the failure."
        )
    if previous.kind == "new_failure":
        names = ", ".join(sorted(previous.new_failures))
        return (
            f"Your change broke previously passing tests: {names}. "
            "Revert or adjust the change so those tests pass again."
        )
    return ""


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
        hint = next_action_hint(previous)
        previous_block = f"""
Previous attempt failed verification:
{previous.summary()}

Required next action:
{hint}

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
