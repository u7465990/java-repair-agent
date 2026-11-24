from java_agent.sandbox.base import ExecResult
from java_agent.tools import ToolContext, build_tools


class FakeSandbox:
    def __init__(self, output: str = "1\tclass X {}", exit_code: int = 0) -> None:
        self.calls: list[list[str]] = []
        self.output = output
        self.exit_code = exit_code

    def exec(self, args, cwd=None, timeout=600) -> ExecResult:
        self.calls.append(list(args))
        return ExecResult(self.exit_code, self.output, "")

    def close(self) -> None:
        return None


def _tools(sandbox: FakeSandbox):
    return {t.name: t for t in build_tools(ToolContext(sandbox, "/workspace/repo"))}


def test_read_file_rejects_escape() -> None:
    tools = _tools(FakeSandbox())
    assert tools["read_file"].invoke({"path": "../etc/passwd"}).startswith("ERROR")


def test_write_file_rejects_absolute_outside_path() -> None:
    tools = _tools(FakeSandbox())
    result = tools["write_file"].invoke({"path": "/tmp/evil", "content": "x"})
    assert result.startswith("ERROR")


def test_read_file_runs_numbered_read() -> None:
    sandbox = FakeSandbox("1\tclass X {}")
    tools = _tools(sandbox)
    out = tools["read_file"].invoke({"path": "src/X.java", "start": 1, "end": 20})
    assert "class X" in out
    assert "nl -ba" in " ".join(sandbox.calls[0])


def test_run_tests_reports_failures() -> None:
    output = "Failing tests: 1\n\t- org.example.FooTest::bar\n"
    sandbox = FakeSandbox(output, exit_code=1)
    tools = _tools(sandbox)
    result = tools["run_tests"].invoke({})
    assert "failing=1" in result
    assert "FooTest::bar" in result
