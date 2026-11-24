"""Collect benchmark and per-run reports into one table."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

_TITLE = re.compile(r"^#\s+(\S+)\s+repair report", re.MULTILINE)
_MODEL = re.compile(r"^- model:\s*(.+)$", re.MULTILINE)
_RESULT = re.compile(r"^- result:\s*(\S+)", re.MULTILINE)
_ATTEMPTS = re.compile(r"^- attempts:\s*(\d+)", re.MULTILINE)
_MINUTES = re.compile(r"^- duration:\s*([\d.]+)", re.MULTILINE)
_TOKENS = re.compile(r"^- tokens: input (\d+), output (\d+)", re.MULTILINE)
_KIND = re.compile(r"^- failure kind:\s*(\S+)", re.MULTILINE)


@dataclass
class ResultRow:
    model: str
    bug: str
    result: str
    attempts: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    minutes: float = 0.0
    kind: str = ""
    source: str = ""


def _parse_report(path: Path) -> ResultRow | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    title = _TITLE.search(text)
    model = _MODEL.search(text)
    result = _RESULT.search(text)
    if not (title and model and result):
        return None
    row = ResultRow(
        model=model.group(1).strip(),
        bug=title.group(1).strip(),
        result=result.group(1).strip(),
        source=str(path),
    )
    attempts = _ATTEMPTS.search(text)
    minutes = _MINUTES.search(text)
    tokens = _TOKENS.search(text)
    kind = _KIND.search(text)
    row.attempts = int(attempts.group(1)) if attempts else 0
    row.minutes = float(minutes.group(1)) if minutes else 0.0
    if tokens:
        row.input_tokens = int(tokens.group(1))
        row.output_tokens = int(tokens.group(2))
    row.kind = kind.group(1) if kind else ""
    return row


def _parse_csv(path: Path) -> list[ResultRow]:
    rows: list[ResultRow] = []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        for item in csv.DictReader(handle):
            try:
                rows.append(
                    ResultRow(
                        model=str(item.get("model", "")),
                        bug=str(item.get("bug", "")),
                        result=str(item.get("result", "")),
                        input_tokens=int(item.get("input_tokens") or 0),
                        output_tokens=int(item.get("output_tokens") or 0),
                        minutes=float(item.get("minutes") or 0),
                        source=str(path),
                    )
                )
            except (TypeError, ValueError):
                continue
    return rows


def collect_rows(paths: list[Path]) -> list[ResultRow]:
    """Reports win over CSV rows for the same (model, bug)."""
    collected: dict[tuple[str, str], ResultRow] = {}
    for root in paths:
        if not root.exists():
            continue
        for path in sorted(root.rglob("report.md")):
            row = _parse_report(path)
            if row is not None:
                collected[(row.model, row.bug)] = row
    for root in paths:
        if not root.exists():
            continue
        for path in sorted(root.rglob("summary.csv")):
            for row in _parse_csv(path):
                collected.setdefault((row.model, row.bug), row)
    return sorted(collected.values(), key=lambda r: (r.model, r.bug))


def render_markdown(rows: list[ResultRow]) -> str:
    lines = [
        "| model | bug | result | attempts | input | output | minutes | kind |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.model} | {row.bug} | {row.result} | {row.attempts} | "
            f"{row.input_tokens} | {row.output_tokens} | {row.minutes:.1f} | {row.kind} |"
        )
    return "\n".join(lines) + "\n"
