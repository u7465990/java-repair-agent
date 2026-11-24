from pathlib import Path

from java_agent.skills import SkillRegistry, build_skill_tools, parse_skill


def _write_skill(root: Path, name: str, description: str, body: str) -> None:
    directory = root / name
    directory.mkdir(parents=True)
    (directory / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n{body}\n",
        encoding="utf-8",
    )


def test_parse_and_discover(tmp_path: Path) -> None:
    _write_skill(tmp_path, "java-repair", "Fix Java bugs", "# Steps\n1. reproduce")
    registry = SkillRegistry.discover([tmp_path])

    skill = registry.load("java-repair")
    assert skill is not None
    assert "reproduce" in skill.body
    assert "java-repair" in registry.index()


def test_load_skill_tool(tmp_path: Path) -> None:
    _write_skill(tmp_path, "junit5", "Write JUnit 5 tests", "Use @Test.")
    tools = {tool.name: tool for tool in build_skill_tools(SkillRegistry.discover([tmp_path]))}

    assert "Use @Test." in tools["load_skill"].invoke({"name": "junit5"})
    assert tools["load_skill"].invoke({"name": "missing"}).startswith("ERROR")


def test_malformed_skill_is_skipped(tmp_path: Path) -> None:
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "SKILL.md").write_text("no frontmatter", encoding="utf-8")
    assert SkillRegistry.discover([tmp_path]).skills == {}


def test_parse_with_allowed_tools(tmp_path: Path) -> None:
    directory = tmp_path / "demo"
    directory.mkdir()
    path = directory / "SKILL.md"
    path.write_text(
        "---\nname: demo\ndescription: demo skill\nallowed-tools: [read_file, bash]\n---\nbody\n",
        encoding="utf-8",
    )
    skill = parse_skill(path)
    assert skill.allowed_tools == ["read_file", "bash"]
