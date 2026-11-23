# Architecture

## Principles

1. **Strategy belongs to the model; constraints belong to infrastructure.** Budgets, permissions
   and sandboxes are code. Reading order, hypotheses and edit strategy are the model's job.
2. **Use ecosystem standards.** LangChain tools, Agent Skills (`SKILL.md`), MCP.
3. **Verification is independent of the model's claims.** Only `verify` can mark a fix as done.

## Layers

| Layer | Contents | Deterministic |
|---|---|---|
| Runtime | LangGraph graph, checkpointer, interrupts, budgets | yes |
| Capability | tool registry, skills loader, MCP client, subagents | partly |
| Execution | Docker sandbox, command policy, git worktree | yes |

## Runtime graph (target)

```text
START -> prepare -> agent -> verify -> deliver -> END
                      ^         |
                      +-- fail -+
```

- `prepare`: worktree, dependency warm-up, repo map, baseline test run.
- `agent`: free ReAct loop with tools and subagents.
- `verify`: independent rebuild, target tests, regression tests, diff audit.
- `deliver`: patch, report, optional pull request.

The agent stops when it calls `finish`, when it stops issuing tool calls, or when the budget
is exhausted. A failing verification returns a structured report to the agent instead of
ending the run.

## Tools

`bash`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`, `java_symbols`,
`find_references`, `diagnostics`, `run_tests`, `git_diff`, `load_skill`, `task`,
`write_todos`, `finish`, `ask_user`, plus `mcp__<server>__<tool>`.

Rules: Pydantic arguments, structured errors instead of exceptions, explicit idempotency,
audit fields for every call, truncated output.

## Skills

```text
skills/java-repair/
  SKILL.md            # frontmatter: name, description, allowed-tools
  resources/
  scripts/
```

Only `name` and `description` are always in context; the body is loaded on demand by
`load_skill`. `allowed-tools` narrows the visible tool set when strict mode is on.

## MCP

- **Client:** GitHub, Jira, Sentry via `MultiServerMCPClient`; per-server allowlists,
  read-only tools bypass approval, write tools require it.
- **Server:** expose `run_tests`, `java_symbols`, `find_references`, `diagnostics`,
  `apply_patch` so IDEs and other agents reuse the same Java tooling.

## Sandbox

One container per task, `--network none`, mounted worktree, CPU/memory/PID limits.
Dependencies are warmed at build time (Defects4J `init.sh`), so runtime can stay offline.
A `policy.yaml` decides which commands are denied, allowed or need approval.

## Verification

A patch is accepted only if:

1. the build succeeds with the same command used at baseline;
2. every trigger test (F2P) passes;
3. no previously passing test fails;
4. the diff does not touch tests or build files and stays under the size limit.

## Evaluation

Defects4J cases are described as `Case(project, bug)`. `run_baseline` records the failing
set; after the agent runs, the same commands are re-executed and compared. Reports include
resolve rate, cost, verify attempts and regression rate.
