"""Independent verification of a candidate fix."""

from __future__ import annotations

from dataclasses import dataclass, field

from java_agent.audit import DiffAudit, audit_workspace
from java_agent.d4j import D4J, parse_failing_tests
from java_agent.sandbox.base import Sandbox


@dataclass
class VerifyReport:
    """Outcome of rebuilding and retesting the workspace."""

    ok: bool
    compile_ok: bool
    failing: set[str] = field(default_factory=set)
    new_failures: set[str] = field(default_factory=set)
    trigger: set[str] = field(default_factory=set)
    output: str = ""
    diff_stat: str = ""
    audit: DiffAudit = field(default_factory=lambda: DiffAudit(ok=True))

    def summary(self) -> str:
        lines = [
            f"compile_ok={self.compile_ok}",
            f"failing={len(self.failing)}",
            f"new_failures={sorted(self.new_failures)}",
            f"trigger_failing={sorted(self.failing & self.trigger)}",
            f"audit_ok={self.audit.ok}",
        ]
        if self.audit.violations:
            lines.append(f"violations={self.audit.violations}")
        return "\n".join(lines)


def verify(
    sandbox: Sandbox,
    workdir: str,
    baseline_failing: set[str],
    trigger: set[str],
    timeout: int = 900,
) -> VerifyReport:
    """Rebuild, retest and audit the workspace against the baseline."""
    audit = audit_workspace(sandbox, workdir)
    d4j = D4J(sandbox)
    compile_result = d4j.compile(workdir)

    if compile_result.ok:
        test_result = d4j.test(workdir, timeout=timeout)
        failing = test_result.failing or parse_failing_tests(test_result.output)
        output = test_result.output
    else:
        failing = set()
        output = compile_result.output

    new_failures = failing - baseline_failing
    trigger_failing = failing & trigger
    ok = (
        compile_result.ok
        and not new_failures
        and not trigger_failing
        and audit.ok
    )

    diff = sandbox.exec(["git", "-C", workdir, "--no-pager", "diff", "HEAD", "--stat"])
    return VerifyReport(
        ok=ok,
        compile_ok=compile_result.ok,
        failing=failing,
        new_failures=new_failures,
        trigger=trigger,
        output=output,
        diff_stat=diff.output.strip(),
        audit=audit,
    )
