from fakes import ScriptedChatModel
from langchain_core.messages import AIMessage

from java_agent.agent.orchestrator import run_repair
from java_agent.eval.runner import Case
from java_agent.sandbox.base import ExecResult


class RepairSandbox:
    """Simulates Defects4J: one failing test at baseline, green after the fix."""

    def __init__(self, still_failing: bool = False) -> None:
        self.calls: list[list[str]] = []
        self.test_calls = 0
        self.still_failing = still_failing

    def exec(self, args, cwd=None, timeout=600) -> ExecResult:
        self.calls.append(list(args))
        command = " ".join(str(arg) for arg in args)
        if "defects4j test" in command:
            self.test_calls += 1
            failing = self.test_calls == 1 or self.still_failing
            if failing:
                body = "Failing tests: 1\n\t- org.example.FooTest::bar\n"
            else:
                body = "Failing tests: 0\n"
            return ExecResult(1 if failing else 0, body, "")
        if "defects4j export" in command:
            return ExecResult(0, "org.example.FooTest::bar\n", "")
        if "diff" in command:
            return ExecResult(0, "diff --git a/Foo.java b/Foo.java\n", "")
        return ExecResult(0, "", "")

    def close(self) -> None:
        return None


def _finish() -> ScriptedChatModel:
    return ScriptedChatModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "finish",
                        "args": {"summary": "fixed"},
                        "id": "c1",
                        "type": "tool_call",
                    }
                ],
            )
        ]
    )


def test_repair_succeeds_when_verification_passes() -> None:
    sandbox = RepairSandbox()
    outcome = run_repair(sandbox, Case("Lang", 1), _finish(), max_attempts=1, max_steps=3)

    assert outcome.fixed
    assert outcome.attempts == 1
    assert outcome.patch
    assert sandbox.test_calls == 2


def test_repair_resets_and_reports_failure() -> None:
    sandbox = RepairSandbox(still_failing=True)
    outcome = run_repair(sandbox, Case("Lang", 1), _finish(), max_attempts=1, max_steps=3)

    assert not outcome.fixed
    assert outcome.last is not None and not outcome.last.ok
    assert any("reset" in " ".join(call) for call in sandbox.calls)
