"""Docker-backed sandbox: one container per task."""

from __future__ import annotations

import subprocess
import uuid
from collections.abc import Sequence
from pathlib import Path

from java_agent.sandbox.base import ExecResult, SandboxError


class DockerSandbox:
    """Runs commands inside a long-lived container with a mounted workspace."""

    def __init__(
        self,
        image: str,
        host_dir: str | Path,
        container_dir: str = "/workspace",
        name: str | None = None,
        network: str = "none",
    ) -> None:
        self.image = image
        self.host_dir = Path(host_dir).resolve()
        self.container_dir = container_dir
        self.name = name or f"java-agent-{uuid.uuid4().hex[:8]}"
        self.network = network
        self._started = False

    def start(self) -> None:
        self.host_dir.mkdir(parents=True, exist_ok=True)
        args = [
            "docker",
            "run",
            "-d",
            "--init",
            "--name",
            self.name,
            "--network",
            self.network,
            "-v",
            f"{self.host_dir}:{self.container_dir}",
            "-w",
            self.container_dir,
            self.image,
            "sleep",
            "infinity",
        ]
        completed = subprocess.run(
            args, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False
        )
        if completed.returncode != 0:
            raise SandboxError(completed.stderr.strip() or "docker run failed")
        self._started = True

    def exec(self, args: Sequence[str], cwd: str | None = None, timeout: int = 600) -> ExecResult:
        if not self._started:
            raise SandboxError("sandbox is not running; call start() first")
        cmd = ["docker", "exec"]
        if cwd is not None:
            cmd += ["-w", cwd]
        cmd += [self.name, *args]
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return ExecResult(completed.returncode, completed.stdout, completed.stderr)

    def close(self) -> None:
        if self._started:
            subprocess.run(
                ["docker", "rm", "-f", self.name],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self._started = False

    def __enter__(self) -> DockerSandbox:
        self.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
