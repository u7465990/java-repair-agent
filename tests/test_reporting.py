from pathlib import Path

from java_agent.reporting import collect_rows, render_markdown


def _write_report(root: Path, bug: str, model: str, result: str, tokens: int) -> None:
    directory = root / f"Lang-{bug}"
    directory.mkdir(parents=True)
    (directory / "report.md").write_text(
        f"""# Lang-{bug} repair report

- model: {model}
- result: {result}
- attempts: 2
- duration: 7.5 min
- tokens: input {tokens}, output 100, total {tokens + 100}
- failure kind: passed
""",
        encoding="utf-8",
    )


def test_collects_reports(tmp_path: Path) -> None:
    _write_report(tmp_path, "1", "openai:kimi-k3", "fixed", 1000)
    _write_report(tmp_path, "3", "openai:kimi-k3", "not fixed", 2000)

    rows = collect_rows([tmp_path])
    assert len(rows) == 2
    assert rows[0].bug == "Lang-1"
    assert rows[0].minutes == 7.5
    assert rows[1].kind == "passed"


def test_csv_fills_missing_rows(tmp_path: Path) -> None:
    bench = tmp_path / "bench"
    bench.mkdir()
    (bench / "summary.csv").write_text(
        "model,bug,result,input_tokens,output_tokens,minutes\n"
        "openai:qwen3.8-flash,1,failed,500,50,1.5\n",
        encoding="utf-8",
    )
    rows = collect_rows([tmp_path])
    assert len(rows) == 1
    assert rows[0].input_tokens == 500


def test_render_table() -> None:
    from java_agent.reporting import ResultRow

    table = render_markdown(
        [ResultRow(model="m", bug="Lang-1", result="fixed", attempts=1, input_tokens=10)]
    )
    assert "| m | Lang-1 | fixed | 1 | 10 |" in table
