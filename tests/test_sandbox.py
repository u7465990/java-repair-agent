import sys

from java_agent.sandbox.local import LocalSandbox


def test_local_sandbox_captures_stdout() -> None:
    result = LocalSandbox().exec([sys.executable, "-c", "print('hello')"])
    assert result.ok
    assert "hello" in result.stdout


def test_local_sandbox_captures_exit_code() -> None:
    result = LocalSandbox().exec([sys.executable, "-c", "raise SystemExit(3)"])
    assert result.exit_code == 3
    assert not result.ok
