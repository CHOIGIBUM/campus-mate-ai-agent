from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / ".claude" / "agents"
SKILLS = ROOT / ".claude" / "skills"

errors: list[str] = []

required_root = ["CLAUDE.md", "spec.md", "workflow.md", "role-table.md"]
for name in required_root:
    if not (ROOT / name).exists():
        errors.append(f"missing root contract: {name}")

agent_names: set[str] = set()
for path in sorted(AGENTS.glob("*.md")):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.append(f"agent missing frontmatter: {path}")
        continue
    match = re.search(r"^name:\s*([^\n]+)", text, re.M)
    desc = re.search(r"^description:\s*(?:>-)?", text, re.M)
    if not match:
        errors.append(f"agent missing name: {path}")
    else:
        name = match.group(1).strip()
        if name in agent_names:
            errors.append(f"duplicate agent name: {name}")
        agent_names.add(name)
    if not desc:
        errors.append(f"agent missing description: {path}")

skill_names: set[str] = set()
for path in sorted(SKILLS.glob("*/SKILL.md")):
    name = path.parent.name
    skill_names.add(name)
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.append(f"skill missing frontmatter: {path}")
    if "description:" not in text.split("---", 2)[1]:
        errors.append(f"skill missing description: {path}")

for path in sorted(AGENTS.glob("*.md")):
    text = path.read_text(encoding="utf-8")
    block = re.search(r"^skills:\n((?:\s+-\s+[^\n]+\n?)*)", text, re.M)
    if block:
        for item in re.findall(r"^\s+-\s+([^\n]+)", block.group(1), re.M):
            if item.strip() not in skill_names:
                errors.append(f"{path.name} references missing skill {item.strip()}")

settings = ROOT / ".claude" / "settings.json"
try:
    json.loads(settings.read_text(encoding="utf-8"))
except Exception as exc:
    errors.append(f"invalid settings.json: {exc}")

if (ROOT / ".pi").exists():
    errors.append("legacy .pi directory must not be present in final Claude Code harness")

if errors:
    print("Harness validation failed:")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print(f"Harness validation passed: {len(agent_names)} agents, {len(skill_names)} skills")
