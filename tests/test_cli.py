from typer.testing import CliRunner

from java_agent.cli import app

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "java-agent" in result.stdout


def test_help_lists_d4j_group() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "d4j" in result.stdout
