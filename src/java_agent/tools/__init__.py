"""LangChain tools backed by a sandbox."""

from __future__ import annotations

import base64
import posixpath
import shlex
from dataclasses import dataclass

from langchain_core.tools import BaseTool, tool

from java_agent.d4j import parse_failing_tests
from java_agent.sandbox.base import Sandbox


@dataclass(frozen=True)
class ToolContext:
    """Everything a tool needs: a sandbox and the project root inside it."""

    sandbox: Sandbox
    workdir: str


def _resolve(ctx: ToolContext, path: str) -> str:
    root = ctx.workdir.rstrip("/")
    full = posixpath.normpath(path if path.startswith("/") else posixpath.join(root, path))
    if full != root and not full.startswith(root + "/"):
        raise ValueError(f"path escapes the workspace: {path}")
    return full


def _run(ctx: ToolContext, argv: list[str], timeout: int = 600) -> str:
    result = ctx.sandbox.exec(argv, cwd=ctx.workdir, timeout=timeout)
    output = result.output.strip()
    if len(output) > 8000:
        output = output[:4000] + "\n...[truncated]...\n" + output[-4000:]
    if not result.ok:
        return f"ERROR (exit {result.exit_code}):\n{output[-8000:]}"
    return output if output else "(no output)"


def build_tools(ctx: ToolContext) -> list[BaseTool]:
    """Create the tool set bound to one sandbox workspace."""

    @tool
    def read_file(path: str, start: int = 1, end: int = 120) -> str:
        """Read a text file with line numbers. Path is relative to the repo root."""
        try:
            full = _resolve(ctx, path)
        except ValueError as exc:
            return f"ERROR: {exc}"
        if start < 1 or end < start:
            return "ERROR: invalid line range"
        return _run(
            ctx,
            ["bash", "-lc", f"nl -ba {shlex.quote(full)} | sed -n '{start},{end}p'"],
        )

    @tool
    def write_file(path: str, content: str) -> str:
        """Create or overwrite a text file with the given content."""
        try:
            full = _resolve(ctx, path)
        except ValueError as exc:
            return f"ERROR: {exc}"
        payload = base64.b64encode(content.encode("utf-8")).decode("ascii")
        parent = posixpath.dirname(full) or ctx.workdir
        cmd = (
            f"mkdir -p {shlex.quote(parent)} && "
            f"printf '%s' {shlex.quote(payload)} | base64 -d > {shlex.quote(full)}"
        )
        return _run(ctx, ["bash", "-lc", cmd])

    @tool
    def edit_file(path: str, old: str, new: str) -> str:
        """Replace the first occurrence of old with new in a file."""
        try:
            full = _resolve(ctx, path)
        except ValueError as exc:
            return f"ERROR: {exc}"
        script = (
            "import pathlib, sys\n"
            "p = pathlib.Path(sys.argv[1])\n"
            "text = p.read_text(encoding='utf-8')\n"
            "old, new = sys.argv[2], sys.argv[3]\n"
            "if old not in text:\n"
            "    print('ERROR: old text not found')\n"
            "    sys.exit(2)\n"
            "p.write_text(text.replace(old, new, 1), encoding='utf-8')\n"
            "print('ok')\n"
        )
        return _run(ctx, ["python3", "-c", script, full, old, new])

    @tool
    def list_files(pattern: str = "**/*.java", limit: int = 200) -> str:
        """List files matching a glob pattern (e.g. src/**/*.java)."""
        cmd = (
            f"rg --files -g {shlex.quote(pattern)} {shlex.quote(ctx.workdir)} "
            f"| head -n {max(1, min(limit, 500))}"
        )
        return _run(ctx, ["bash", "-lc", cmd])

    @tool
    def search_code(pattern: str, path: str = ".", max_hits: int = 80) -> str:
        """Search file contents with a regular expression. Returns file:line:text."""
        try:
            full = _resolve(ctx, path)
        except ValueError as exc:
            return f"ERROR: {exc}"
        cmd = (
            f"rg -n --no-heading --color never -e {shlex.quote(pattern)} "
            f"{shlex.quote(full)} | head -n {max(1, min(max_hits, 200))}"
        )
        return _run(ctx, ["bash", "-lc", cmd])

    @tool
    def run_tests(timeout_seconds: int = 600) -> str:
        """Compile and run the project's test suite; returns failing test names."""
        result = ctx.sandbox.exec(
            ["defects4j", "test", "-w", ctx.workdir], timeout=timeout_seconds
        )
        failing = sorted(parse_failing_tests(result.output))
        lines = [f"exit_code={result.exit_code}", f"failing={len(failing)}"]
        lines += [f"  - {name}" for name in failing[:20]]
        if not failing and not result.ok:
            lines.append(result.output[-3000:])
        return "\n".join(lines)

    @tool
    def bash(command: str, timeout_seconds: int = 300) -> str:
        """Run a shell command inside the workspace (cwd is the repo root)."""
        return _run(ctx, ["bash", "-lc", command], timeout=timeout_seconds)

    @tool
    def git_diff() -> str:
        """Show the current uncommitted diff."""
        return _run(ctx, ["git", "-C", ctx.workdir, "--no-pager", "diff", "--no-color"])

    @tool
    def finish(summary: str) -> str:
        """Call when the fix is complete. Summarise the root cause and the change."""
        return f"TASK_COMPLETE: {summary}"

    return [
        read_file,
        write_file,
        edit_file,
        list_files,
        search_code,
        run_tests,
        bash,
        git_diff,
        finish,
    ]
