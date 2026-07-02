"""Notion Dashboard Agent runner."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".pi" / "skills" / "notion-dashboard-sync"))

from notion_dashboard_sync import NotionDashboardSyncSkill  # noqa: E402


class NotionDashboardAgent:
    def __init__(self) -> None:
        self.recommended_dir = ROOT / "data" / "recommended"
        self.skill = NotionDashboardSyncSkill()

    def run(self, input_data: Dict[str, Any] | None = None) -> Tuple[bool, str, Dict[str, Any]]:
        input_data = input_data or {}
        if input_data.get("action") == "monitor":
            return self.skill.execute(input_data)
        opportunities = input_data.get("opportunities") or self._load_recommended()
        results = []
        for opportunity in opportunities:
            _, _, result = self.skill.execute({
                "opportunity": opportunity,
                "status": input_data.get("status", "Recommended"),
            })
            results.append(result)
        return True, f"Notion 로컬 대시보드 동기화 완료: {len(results)}건", {"results": results}

    def _load_recommended(self) -> List[Dict[str, Any]]:
        items = []
        for path in sorted(self.recommended_dir.glob("recommended_opportunity_*.json")):
            try:
                items.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
        return items


if __name__ == "__main__":
    stdin_text = sys.stdin.read()
    payload = json.loads(stdin_text) if stdin_text.strip() else {}
    ok, message, output = NotionDashboardAgent().run(payload)
    print(message)
    print(json.dumps(output, ensure_ascii=False, indent=2))
