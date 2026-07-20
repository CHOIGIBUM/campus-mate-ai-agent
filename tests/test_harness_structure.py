from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_claude_harness_structure() -> None:
    assert not (ROOT / ".pi").exists()
    assert (ROOT / ".claude" / "agents").is_dir()
    assert (ROOT / ".claude" / "skills" / "campus-mate-orchestrator" / "SKILL.md").exists()
    assert len(list((ROOT / ".claude" / "agents").glob("*.md"))) == 9
    assert len(list((ROOT / ".claude" / "skills").glob("*/SKILL.md"))) >= 18


def test_settings_json_is_valid() -> None:
    payload = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert "hooks" in payload
