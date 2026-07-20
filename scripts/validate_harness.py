from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / ".claude" / "agents"
SKILLS = ROOT / ".claude" / "skills"

EXPECTED_AGENTS = {
    "profile-manager",
    "source-collector",
    "multipass-parser",
    "fit-priority",
    "notion-dashboard",
    "schedule-notification",
}
EXPECTED_SKILLS = {
    "campus-mate-orchestrator",
    "profile-build",
    "source-watchlist-crawl",
    "html-opportunity-parse",
    "rendered-page-ocr",
    "poster-vision-extract",
    "schema-merge-and-validate",
    "recommendation-rank",
    "notion-dashboard-sync",
    "slack-brief-generate",
    "calendar-sync",
    "qa-audit",
}

errors: list[str] = []

for name in ["README.md", "CLAUDE.md", "spec.md", "workflow.md", "role-table.md"]:
    if not (ROOT / name).exists():
        errors.append(f"missing root contract: {name}")

agent_names: set[str] = set()
for path in sorted(AGENTS.glob("*.md")):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.append(f"agent missing frontmatter: {path}")
        continue
    match = re.search(r"^name:\s*([^\n]+)", text, re.M)
    if not match:
        errors.append(f"agent missing name: {path}")
    else:
        name = match.group(1).strip()
        if name in agent_names:
            errors.append(f"duplicate agent name: {name}")
        agent_names.add(name)
    if not re.search(r"^description:\s*(?:>-)?", text, re.M):
        errors.append(f"agent missing description: {path}")

skill_names: set[str] = set()
for path in sorted(SKILLS.glob("*/SKILL.md")):
    name = path.parent.name
    skill_names.add(name)
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.append(f"skill missing frontmatter: {path}")
    frontmatter = text.split("---", 2)[1] if text.count("---") >= 2 else ""
    if "description:" not in frontmatter:
        errors.append(f"skill missing description: {path}")

for path in sorted(AGENTS.glob("*.md")):
    text = path.read_text(encoding="utf-8")
    block = re.search(r"^skills:\n((?:\s+-\s+[^\n]+\n?)*)", text, re.M)
    if block:
        for item in re.findall(r"^\s+-\s+([^\n]+)", block.group(1), re.M):
            if item.strip() not in skill_names:
                errors.append(f"{path.name} references missing skill {item.strip()}")

if agent_names != EXPECTED_AGENTS:
    errors.append(f"agent set mismatch: expected {sorted(EXPECTED_AGENTS)}, got {sorted(agent_names)}")
if skill_names != EXPECTED_SKILLS:
    errors.append(f"skill set mismatch: expected {sorted(EXPECTED_SKILLS)}, got {sorted(skill_names)}")

try:
    json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
except Exception as exc:
    errors.append(f"invalid settings.json: {exc}")

if (ROOT / ".pi").exists():
    errors.append("legacy .pi directory must not be present")

for forbidden in ("materials",):
    if (ROOT / forbidden).exists():
        errors.append(f"forbidden public repository directory present: {forbidden}")

if errors:
    print("Harness validation failed:")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print(f"Harness validation passed: {len(agent_names)} agents, {len(skill_names)} skills")
