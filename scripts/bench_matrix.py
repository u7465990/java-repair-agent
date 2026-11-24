"""Run the repair agent across a model x bug matrix and summarise the results."""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
from pathlib import Path

TOKENS = re.compile(r"tokens: in (\d+) / out (\d+) \| ([\d.]+) min")
ERROR_MARKERS = ("Error code:", "Access denied", "Unpurchased", "Arrearage")


def parse_list(text: str) -> list[str]:
    return [item.strip() for item in text.split(",") if item.strip()]


def read_usage(log: str, report: Path) -> tuple[int, int, float]:
    match = TOKENS.search(log)
    if match:
        return int(match.group(1)), int(match.group(2)), float(match.group(3))
    if report.exists():
        text = report.read_text(encoding="utf-8", errors="replace")
        tokens = re.search(r"input (\d+), output (\d+)", text)
        duration = re.search(r"duration: ([\d.]+) min", text)
        if tokens:
            return (
                int(tokens.group(1)),
                int(tokens.group(2)),
                float(duration.group(1)) if duration else 0.0,
            )
    return 0, 0, 0.0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", required=True, help="Comma separated model specs.")
    parser.add_argument("--bugs", default="1", help="Comma separated bug numbers.")
    parser.add_argument("--attempts", type=int, default=2)
    parser.add_argument("--max-steps", type=int, default=25)
    parser.add_argument("--out", default="bench")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []

    for model in parse_list(args.models):
        for bug in parse_list(args.bugs):
            report = Path("work") / f"Lang-{bug}" / "report.md"
            report.unlink(missing_ok=True)

            command = [
                "uv",
                "run",
                "java-agent",
                "run",
                "-p",
                "Lang",
                "-b",
                bug,
                "--model",
                model,
                "--attempts",
                str(args.attempts),
                "--max-steps",
                str(args.max_steps),
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            log = result.stdout + result.stderr
            slug = model.replace("/", "_").replace(":", "_")
            (out / f"{slug}-Lang-{bug}.log").write_text(log, encoding="utf-8")

            input_tokens, output_tokens, minutes = read_usage(log, report)
            if result.returncode != 0 or any(marker in log for marker in ERROR_MARKERS):
                status = "error"
            elif "fixed in" in log and "not fixed" not in log:
                status = "fixed"
            else:
                status = "failed"
            rows.append(
                {
                    "model": model,
                    "bug": bug,
                    "result": status,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "minutes": minutes,
                }
            )

    csv_path = out / "summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "| model | bug | result | input tokens | output tokens | minutes |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['model']} | {row['bug']} | {row['result']} | "
            f"{row['input_tokens']} | {row['output_tokens']} | {row['minutes']:.1f} |"
        )
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
