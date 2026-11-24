"""Check agent trajectories for tool/infrastructure errors."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("patterns", nargs="+", help="Glob patterns for trajectory files.")
    args = parser.parse_args()

    files = sorted({path for pattern in args.patterns for path in Path().glob(pattern)})
    calls = 0
    errors = 0
    samples: list[str] = []

    for path in files:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            calls += len(message.get("tool_calls") or [])
            if message.get("role") != "tool":
                continue
            content = str(message.get("content") or "")
            if (
                content.startswith("ERROR")
                or "command not found" in content
                or "No such file" in content
            ):
                errors += 1
                if len(samples) < 5:
                    samples.append(content.splitlines()[0][:160])

    print(f"files={len(files)} tool_calls={calls} tool_errors={errors}")
    for sample in samples:
        print(f"  - {sample}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
