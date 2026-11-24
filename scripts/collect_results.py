"""CLI: merge reports and benchmark CSVs into one markdown table."""

from __future__ import annotations

import argparse
from pathlib import Path

from java_agent.reporting import collect_rows, render_markdown


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", help="Directories to scan for reports.")
    parser.add_argument("--out", help="Write the table to this file.")
    args = parser.parse_args()

    rows = collect_rows([Path(item) for item in args.paths])
    table = render_markdown(rows)
    print(table)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(table, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
