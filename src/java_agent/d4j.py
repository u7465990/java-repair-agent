"""Defects4J command wrapper and output parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from java_agent.sandbox.base import ExecResult, Sandbox

_FAILING_HEADER = re.compile(r"^failing tests:\s*(\d+)?", re.IGNORECASE)


@dataclass
class TestReport:
    """Parsed result of one defects4j test run."""

    failing: set[str] = field(default_factory=set)
    exit_code: int = 0
    output: str = ""

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.failing


def parse_failing_tests(output: str) -> set[str]:
    """Extract test names from the 'Failing tests:' block printed by defects4j."""
    failing: set[str] = set()
    collecting = False
    for raw in output.splitlines():
        line = raw.strip()
        if _FAILING_HEADER.match(line):
            collecting = True
            continue
        if not collecting:
            continue
        if line.startswith("- "):
            failing.add(line[2:].strip())
        elif line:
            collecting = False
    return failing


class D4J:
    """Thin wrapper over the defects4j CLI, executed through a sandbox."""

    def __init__(self, sandbox: Sandbox) -> None:
        self.sandbox = sandbox

    def checkout(self, project: str, bug: int, dest: str) -> ExecResult:
        return self.sandbox.exec(
            ["defects4j", "checkout", "-p", project, "-v", f"{bug}b", "-w", dest],
            timeout=600,
        )

    def compile(self, workdir: str) -> ExecResult:
        return self.sandbox.exec(["defects4j", "compile", "-w", workdir], timeout=900)

    def test(self, workdir: str, timeout: int = 900) -> TestReport:
        result = self.sandbox.exec(["defects4j", "test", "-w", workdir], timeout=timeout)
        return TestReport(parse_failing_tests(result.output), result.exit_code, result.output)

    def export(self, prop: str, workdir: str) -> list[str]:
        result = self.sandbox.exec(
            ["defects4j", "export", "-p", prop, "-w", workdir], timeout=120
        )
        if not result.ok:
            return []
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
