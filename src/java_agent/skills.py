"""Load SKILL.md files and expose them as on-demand tools."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from langchain_core.tools import BaseTool, tool

_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


@dataclass
class Skill:
    name: str
    description: str
    body: str
    path: Path
    allowed_tools: list[str] = field(default_factory=list)


def parse_skill(path: Path) -> Skill:
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER.match(text)
    if not match:
        raise ValueError(f"{path} has no YAML frontmatter")
    meta = yaml.safe_load(match.group(1)) or {}
    name = str(meta.get("name") or path.parent.name)
    description = str(meta.get("description") or "").strip()
    if not description:
        raise ValueError(f"{path} has no description")
    allowed = meta.get("allowed-tools") or []
    if isinstance(allowed, str):
        allowed = [item.strip() for item in allowed.split(",") if item.strip()]
    return Skill(
        name=name,
        description=description,
        body=text[match.end() :].strip(),
        path=path,
        allowed_tools=list(allowed),
    )


@dataclass
class SkillRegistry:
    skills: dict[str, Skill] = field(default_factory=dict)

    @classmethod
    def discover(cls, roots: list[Path]) -> SkillRegistry:
        registry = cls()
        for root in roots:
            if not root.exists():
                continue
            for path in sorted(root.glob("*/SKILL.md")):
                try:
                    skill = parse_skill(path)
                except (OSError, ValueError):
                    continue
                registry.skills[skill.name] = skill
        return registry

    def index(self) -> str:
        if not self.skills:
            return ""
        return "\n".join(
            f"- {skill.name}: {skill.description}" for skill in self.skills.values()
        )

    def load(self, name: str) -> Skill | None:
        return self.skills.get(name)


def build_skill_tools(registry: SkillRegistry) -> list[BaseTool]:
    """Tools that let the model pull a skill body into context on demand."""

    @tool
    def load_skill(name: str) -> str:
        """Load the full instructions of a skill by name."""
        skill = registry.load(name)
        if skill is None:
            available = ", ".join(sorted(registry.skills)) or "(none)"
            return f"ERROR: unknown skill {name}; available: {available}"
        return skill.body

    @tool
    def list_skills() -> str:
        """List available skills with their one-line descriptions."""
        return registry.index() or "(no skills installed)"

    return [load_skill, list_skills]
