"""Audit the working tree before accepting a patch."""

from __future__ import annotations

from dataclasses import dataclass, field

from java_agent.sandbox.base import Sandbox

ALLOWED_PREFIXES = ("src/main/",)
IGNORED_PREFIXES = (
    "scratch/",
    ".agent/",
    "target/",
    "build/",
    "out/",
    ".gradle/",
    "all_tests",
    "failing_tests",
    ".defects4j.config",
    "defects4j.build.properties",
)
FORBIDDEN_NAMES = {
    "pom.xml",
    "build.xml",
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
    "gradle.properties",
}


@dataclass
class DiffAudit:
    ok: bool
    files: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    added: int = 0
    removed: int = 0


def _is_forbidden(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return path.startswith("src/test/") or name in FORBIDDEN_NAMES or path.startswith(".git/")


def audit_workspace(
    sandbox: Sandbox,
    workdir: str,
    max_files: int = 5,
    max_lines: int = 400,
) -> DiffAudit:
    """Stage new source files, then check paths and change size."""
    sandbox.exec(["git", "-C", workdir, "add", "-A", "--", "src/main"])

    status = sandbox.exec(
        ["git", "-C", workdir, "status", "--porcelain", "--untracked-files=all"]
    ).stdout
    numstat = sandbox.exec(["git", "-C", workdir, "diff", "HEAD", "--numstat"]).stdout

    violations: list[str] = []
    files: list[str] = []
    added = 0
    removed = 0

    for line in status.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ")[-1]
        if path.startswith(IGNORED_PREFIXES):
            continue
        if _is_forbidden(path):
            violations.append(f"forbidden path: {path}")
        elif not path.startswith(ALLOWED_PREFIXES):
            violations.append(f"outside src/main: {path}")

    for line in numstat.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        raw_added, raw_removed, path = parts
        files.append(path)
        added += int(raw_added) if raw_added.isdigit() else 0
        removed += int(raw_removed) if raw_removed.isdigit() else 0

    if not files:
        violations.append("no source changes")
    if len(files) > max_files:
        violations.append(f"too many files: {len(files)} > {max_files}")
    if added + removed > max_lines:
        violations.append(f"diff too large: {added + removed} > {max_lines} lines")

    return DiffAudit(
        ok=not violations,
        files=files,
        violations=violations,
        added=added,
        removed=removed,
    )
