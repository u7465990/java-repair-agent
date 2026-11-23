"""Shared sandbox protocol."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


class SandboxError(RuntimeError):
    """Raised when a sandbox cannot be created or used."""


@dataclass(frozen=True)
class ExecResult:
    """Result of a command executed inside a sandbox."""

    exit_code: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.exit_code == 0

    @property
    def output(self) -> str:
        return self.stdout + self.stderr


class Sandbox(Protocol):
    """Anything that can execute a command and be cleaned up."""

    def exec(
        self, args: Sequence[str], cwd: str | None = None, timeout: int = 600
    ) -> ExecResult: ...

    def close(self) -> None: ...
