"""Orchestrate baseline, agent attempts and independent verification."""

from __future__ import annotations

from dataclasses import dataclass, field

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from java_agent.agent.prompts import system_prompt, user_prompt
from java_agent.agent.react import build_react_agent
from java_agent.eval.runner import Case, run_baseline
from java_agent.sandbox.base import Sandbox
from java_agent.tools import ToolContext, build_tools
from java_agent.verify import VerifyReport, verify


@dataclass
class RepairOutcome:
    """Result of a full repair run."""

    fixed: bool
    attempts: int
    patch: str = ""
    last: VerifyReport | None = None
    history: list[VerifyReport] = field(default_factory=list)


def reset_workspace(sandbox: Sandbox, workdir: str) -> None:
    """Discard everything the agent changed, back to the buggy commit."""
    sandbox.exec(["git", "-C", workdir, "reset", "--hard", "HEAD"])
    sandbox.exec(["git", "-C", workdir, "clean", "-fd"])


def run_repair(
    sandbox: Sandbox,
    case: Case,
    model: BaseChatModel,
    *,
    workdir: str = "/workspace/repo",
    max_attempts: int = 3,
    max_steps: int = 40,
) -> RepairOutcome:
    """Run prepare -> agent -> verify, retrying with feedback."""
    baseline = run_baseline(case, sandbox, workdir)
    if not baseline.compile_ok:
        raise RuntimeError(f"baseline for {case.key} does not compile")

    history: list[VerifyReport] = []
    for attempt in range(1, max_attempts + 1):
        tools = build_tools(ToolContext(sandbox=sandbox, workdir=workdir))
        agent = build_react_agent(model, tools, system_prompt(workdir), max_steps=max_steps)
        agent.invoke(
            {
                "messages": [
                    HumanMessage(
                        user_prompt(case, baseline, attempt, history[-1] if history else None)
                    )
                ]
            },
            config={"recursion_limit": max_steps * 4 + 10},
        )

        report = verify(sandbox, workdir, baseline.report.failing, baseline.trigger)
        history.append(report)
        if report.ok:
            diff = sandbox.exec(["git", "-C", workdir, "--no-pager", "diff"]).stdout
            return RepairOutcome(True, attempt, diff, report, history)
        reset_workspace(sandbox, workdir)

    return RepairOutcome(False, max_attempts, "", history[-1] if history else None, history)
