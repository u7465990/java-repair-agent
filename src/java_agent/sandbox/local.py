"""Run commands on the host machine (development and tests)."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence

from java_agent.sandbox.base import ExecResult


class LocalSandbox:
    """Thin wrapper around subprocess, with no isolation."""

    def exec(self, args: Sequence[str], cwd: str | None = None, timeout: int = 600) -> ExecResult:
        completed = subprocess.run(
            list(args),
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return ExecResult(completed.returncode, completed.stdout, completed.stderr)

    def close(self) -> None:
        return None

    def __enter__(self) -> LocalSandbox:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
