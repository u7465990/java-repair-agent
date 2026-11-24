"""Command line interface."""

from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from java_agent import __version__
from java_agent.agent.orchestrator import run_repair
from java_agent.eval.runner import Case, run_baseline
from java_agent.sandbox.docker import DockerSandbox

app = typer.Typer(no_args_is_help=True, add_completion=False, help="Java repair agent CLI.")
d4j_app = typer.Typer(no_args_is_help=True, help="Defects4J commands.")
app.add_typer(d4j_app, name="d4j")

console = Console()
DEFAULT_IMAGE = "d4j-runner:2.0"
DEFAULT_WORKDIR = Path("work")


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False
    )


def _docker_ready() -> bool:
    return shutil.which("docker") is not None and _run(["docker", "info"]).returncode == 0


@app.command()
def version() -> None:
    """Show the installed version."""
    console.print(f"java-agent {__version__}")


@app.command()
def doctor() -> None:
    """Check local prerequisites."""
    table = Table(title="Environment check")
    table.add_column("check")
    table.add_column("status")
    table.add_column("detail")

    table.add_row("python", "ok", platform.python_version())
    for name in ("uv", "git"):
        path = shutil.which(name)
        table.add_row(name, "ok" if path else "missing", path or "not on PATH")

    if shutil.which("docker") is None:
        table.add_row("docker", "missing", "not on PATH")
        table.add_row("image", "unknown", DEFAULT_IMAGE)
    else:
        daemon = _run(["docker", "info"]).returncode == 0
        table.add_row(
            "docker",
            "ok" if daemon else "error",
            "daemon reachable" if daemon else "daemon not running: start Docker Desktop",
        )
        image_ok = _run(["docker", "image", "inspect", DEFAULT_IMAGE]).returncode == 0
        table.add_row("image", "ok" if image_ok else "missing", DEFAULT_IMAGE)

    console.print(table)


@d4j_app.command("smoke")
def smoke(
    project: Annotated[str, typer.Option("--project", "-p", help="Defects4J project id.")] = "Lang",
    bug: Annotated[int, typer.Option("--bug", "-b", help="Bug number.")] = 1,
    workdir: Annotated[Path, typer.Option("--workdir", help="Host directory.")] = DEFAULT_WORKDIR,
    image: Annotated[str, typer.Option("--image", help="Sandbox image.")] = DEFAULT_IMAGE,
) -> None:
    """Checkout one bug, compile it and print baseline failing tests."""
    if not _docker_ready():
        console.print("[red]Docker is not available.[/red] Start Docker Desktop and retry.")
        raise typer.Exit(code=1)

    case_dir = (workdir / f"{project}-{bug}").resolve()
    case_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"workspace: {case_dir}")

    sandbox = DockerSandbox(
        image=image,
        host_dir=case_dir,
        name=f"java-agent-{project}-{bug}".lower(),
    )
    try:
        with sandbox:
            console.print(f"checkout {project}-{bug} (this may take a minute)")
            result = run_baseline(Case(project, bug), sandbox, "/workspace/repo")
    except Exception as exc:  # noqa: BLE001 - surface a readable message in the CLI
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    (case_dir / "compile.log").write_text(result.compile_output, encoding="utf-8")
    (case_dir / "baseline-test.log").write_text(result.report.output, encoding="utf-8")

    console.print(f"compile: {'ok' if result.compile_ok else 'failed'}")
    console.print(f"trigger tests: {len(result.trigger)}")
    console.print(f"baseline failing: {len(result.report.failing)}")
    for test_name in sorted(result.report.failing)[:10]:
        console.print(f"  - {test_name}")
    if not result.report.failing:
        console.print("[yellow]No failing tests at baseline; check the bug id.[/yellow]")
        tail = "\n".join(result.report.output.splitlines()[-15:])
        console.print(f"[dim]{tail}[/dim]")

def _load_model(spec: str):
    """Build a chat model, honouring OpenAI-compatible endpoints from env."""
    import os

    from langchain.chat_models import init_chat_model

    if ":" not in spec:
        spec = f"openai:{spec}"
    kwargs = {
        "temperature": float(os.getenv("JAVA_AGENT_TEMPERATURE", "0.1")),
        "max_tokens": int(os.getenv("JAVA_AGENT_MAX_TOKENS", "4096")),
    }
    base_url = os.getenv("JAVA_AGENT_BASE_URL") or os.getenv("LLM_BASE_URL")
    api_key = os.getenv("JAVA_AGENT_API_KEY") or os.getenv("LLM_API_KEY")
    if base_url:
        kwargs["base_url"] = base_url
    if api_key:
        kwargs["api_key"] = api_key
    return init_chat_model(spec, **kwargs)


@app.command()
def run(
    project: Annotated[str, typer.Option("--project", "-p", help="Defects4J project id.")] = "Lang",
    bug: Annotated[int, typer.Option("--bug", "-b", help="Bug number.")] = 1,
    model: Annotated[
        str,
        typer.Option("--model", envvar="JAVA_AGENT_MODEL", help="LangChain model spec."),
    ] = "",
    attempts: Annotated[int, typer.Option("--attempts", help="Agent attempts.")] = 3,
    max_steps: Annotated[int, typer.Option("--max-steps", help="Tool calls per attempt.")] = 40,
    workdir: Annotated[Path, typer.Option("--workdir", help="Host directory.")] = DEFAULT_WORKDIR,
    image: Annotated[str, typer.Option("--image", help="Sandbox image.")] = DEFAULT_IMAGE,
) -> None:
    """Let the agent fix one bug, then verify the result independently."""
    if not model:
        console.print("[red]--model is required[/red] (or set JAVA_AGENT_MODEL).")
        raise typer.Exit(code=1)
    if not _docker_ready():
        console.print("[red]Docker is not available.[/red] Start Docker Desktop and retry.")
        raise typer.Exit(code=1)

    case_dir = (workdir / f"{project}-{bug}").resolve()
    case_dir.mkdir(parents=True, exist_ok=True)
    sandbox = DockerSandbox(
        image=image,
        host_dir=case_dir,
        name=f"java-agent-{project}-{bug}".lower(),
    )
    try:
        with sandbox:
            chat = _load_model(model)
            outcome = run_repair(
                sandbox,
                Case(project, bug),
                chat,
                max_attempts=attempts,
                max_steps=max_steps,
            )
    except Exception as exc:  # noqa: BLE001 - surface a readable message in the CLI
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    (case_dir / "patch.diff").write_text(outcome.patch, encoding="utf-8")
    if outcome.last is not None:
        (case_dir / "verify.log").write_text(outcome.last.output, encoding="utf-8")

    if outcome.fixed:
        console.print(f"[green]fixed in {outcome.attempts} attempt(s)[/green]")
    else:
        console.print(f"[red]not fixed after {outcome.attempts} attempt(s)[/red]")
    if outcome.last is not None:
        console.print(outcome.last.summary())
    console.print(f"patch: {case_dir / 'patch.diff'}")

