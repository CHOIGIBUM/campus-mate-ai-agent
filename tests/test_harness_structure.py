from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

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


def test_claude_harness_structure() -> None:
    assert not (ROOT / ".pi").exists()
    agent_dir = ROOT / ".claude" / "agents"
    skill_dir = ROOT / ".claude" / "skills"
    assert agent_dir.is_dir()
    assert skill_dir.is_dir()
    assert {path.stem for path in agent_dir.glob("*.md")} == EXPECTED_AGENTS
    assert {path.parent.name for path in skill_dir.glob("*/SKILL.md")} == EXPECTED_SKILLS


def test_settings_json_is_valid() -> None:
    payload = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert "hooks" in payload
