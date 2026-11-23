"""Baseline runner: checkout a bug, compile it and record failing tests."""

from __future__ import annotations

from dataclasses import dataclass, field

from java_agent.d4j import D4J, TestReport
from java_agent.sandbox.base import Sandbox


@dataclass(frozen=True)
class Case:
    """One Defects4J bug."""

    project: str
    bug: int

    @property
    def key(self) -> str:
        return f"{self.project}-{self.bug}"


@dataclass
class CaseResult:
    """What the baseline run observed."""

    case: Case
    compile_ok: bool
    report: TestReport
    trigger: set[str] = field(default_factory=set)

    @property
    def target_fixed(self) -> bool:
        return bool(self.trigger) and self.report.failing.isdisjoint(self.trigger)


def run_baseline(case: Case, sandbox: Sandbox, dest: str) -> CaseResult:
    """Prepare a buggy checkout and record its failing tests."""
    d4j = D4J(sandbox)
    checkout = d4j.checkout(case.project, case.bug, dest)
    if not checkout.ok:
        raise RuntimeError(f"checkout failed for {case.key}: {checkout.output[-2000:]}")
    compile_result = d4j.compile(dest)
    report = d4j.test(dest)
    trigger = set(d4j.export("tests.trigger", dest))
    return CaseResult(case=case, compile_ok=compile_result.ok, report=report, trigger=trigger)
