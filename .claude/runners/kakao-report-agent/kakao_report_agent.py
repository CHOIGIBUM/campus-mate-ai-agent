"""Kakao Report Agent runner."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "kakao-brief-generate"))

from kakao_brief_generate import KakaoBriefGenerateSkill  # noqa: E402


class KakaoReportAgent:
    def __init__(self) -> None:
        self.profiles_dir = ROOT / "data" / "profiles"
        self.recommended_dir = ROOT / "data" / "recommended"
        self.skill = KakaoBriefGenerateSkill()

    def run(self, input_data: Dict[str, Any] | None = None) -> Tuple[bool, str, Dict[str, Any]]:
        input_data = input_data or {}
        profile = input_data.get("user_profile") or self._load_profile()
        recommendations = input_data.get("recommendations") or self._load_recommended()
        user_name = input_data.get("user_name") or profile.get("basic_info", {}).get("name") or "사용자"
        brief_items = [self._brief_item(item) for item in recommendations]
        payload = {
            "user_id": profile.get("user_id"),
            "user_name": user_name,
            "new_recommendations": brief_items,
            "needs_review": [self._brief_item(item) for item in recommendations if item.get("validation_status", {}).get("needs_review")],
            "conflicts": input_data.get("conflicts", []),
            "notion_url": input_data.get("notion_url", "local://data/notion/dashboard.json"),
        }
        return self.skill.execute(payload)

    def _brief_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        personalization = item.get("personalization", {})
        return {
            "opportunity_id": item.get("opportunity_id"),
            "title": item.get("basic_info", {}).get("title"),
            "fit_score": personalization.get("fit_score"),
            "priority": personalization.get("priority"),
            "d_day": personalization.get("d_day"),
            "reason": " / ".join(personalization.get("recommendation_reason", [])[:2]),
            "validation_status": item.get("validation_status", {}),
        }

    def _load_profile(self) -> Dict[str, Any]:
        paths = sorted(self.profiles_dir.glob("user_profile_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not paths:
            return {}
        return json.loads(paths[0].read_text(encoding="utf-8"))

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
    ok, message, output = KakaoReportAgent().run(payload)
    print(message)
    print(json.dumps(output, ensure_ascii=False, indent=2))
