"""Orchestrate baseline, agent attempts and independent verification."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from java_agent.agent.prompts import system_prompt, user_prompt
from java_agent.agent.react import build_react_agent
from java_agent.eval.runner import Case, run_baseline
from java_agent.sandbox.base import Sandbox
from java_agent.tools import ToolContext, build_tools
from java_agent.usage import Usage, usage_from_messages
from java_agent.verify import VerifyReport, verify


@dataclass
class RepairOutcome:
    """Result of a full repair run."""

    fixed: bool
    attempts: int
    patch: str = ""
    last: VerifyReport | None = None
    history: list[VerifyReport] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    duration_s: float = 0.0


def reset_workspace(sandbox: Sandbox, workdir: str) -> None:
    """Discard everything the agent changed, back to the buggy commit."""
    sandbox.exec(["git", "-C", workdir, "reset", "--hard", "HEAD"])
    sandbox.exec(["git", "-C", workdir, "clean", "-fd"])


def _record(message) -> dict:
    content = message.content
    if not isinstance(content, str):
        content = str(content)
    return {
        "role": getattr(message, "type", "unknown"),
        "content": content,
        "tool_calls": getattr(message, "tool_calls", None),
    }


def _write_trajectory(trace_dir: Path, attempt: int, messages: list) -> None:
    path = trace_dir / f"trajectory-{attempt}.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for message in messages:
            handle.write(json.dumps(_record(message), ensure_ascii=False, default=str))
            handle.write("\n")


def run_repair(
    sandbox: Sandbox,
    case: Case,
    model: BaseChatModel,
    *,
    workdir: str = "/workspace/repo",
    max_attempts: int = 3,
    max_steps: int = 40,
    trace_dir: Path | None = None,
) -> RepairOutcome:
    """Run prepare -> agent -> verify, retrying with feedback."""
    baseline = run_baseline(case, sandbox, workdir)
    if not baseline.compile_ok:
        raise RuntimeError(f"baseline for {case.key} does not compile")

    history: list[VerifyReport] = []
    usage = Usage()
    started = time.perf_counter()
    for attempt in range(1, max_attempts + 1):
        tools = build_tools(ToolContext(sandbox=sandbox, workdir=workdir))
        agent = build_react_agent(model, tools, system_prompt(workdir), max_steps=max_steps)
        result = agent.invoke(
            {
                "messages": [
                    HumanMessage(
                        user_prompt(case, baseline, attempt, history[-1] if history else None)
                    )
                ]
            },
            config={"recursion_limit": max_steps * 4 + 10},
        )
        usage.add(usage_from_messages(result["messages"]))
        if trace_dir is not None:
            _write_trajectory(trace_dir, attempt, result["messages"])

        report = verify(sandbox, workdir, baseline.report.failing, baseline.trigger)
        history.append(report)
        if report.ok:
            diff = sandbox.exec(["git", "-C", workdir, "--no-pager", "diff"]).stdout
            return RepairOutcome(
                True,
                attempt,
                diff,
                report,
                history,
                usage,
                time.perf_counter() - started,
            )

        if trace_dir is not None:
            diff = sandbox.exec(["git", "-C", workdir, "--no-pager", "diff"]).stdout
            (trace_dir / f"attempt-{attempt}.diff").write_text(diff, encoding="utf-8")
        reset_workspace(sandbox, workdir)

    return RepairOutcome(
        False,
        max_attempts,
        "",
        history[-1] if history else None,
        history,
        usage,
        time.perf_counter() - started,
    )
