"""Fit & Priority Agent runner."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[3]
for skill_name in ["interest-keyword-expand", "fit-score-rank", "deadline-priority-rank"]:
    sys.path.insert(0, str(ROOT / ".claude" / "skills" / skill_name))

from deadline_priority_rank import DeadlinePriorityRankSkill  # noqa: E402
from fit_score_rank import FitScoreRankSkill  # noqa: E402
from interest_keyword_expand import InterestKeywordExpandSkill  # noqa: E402


class FitPriorityAgent:
    def __init__(self) -> None:
        self.profiles_dir = ROOT / "data" / "profiles"
        self.parsed_dir = ROOT / "data" / "parsed"
        self.recommended_dir = ROOT / "data" / "recommended"
        self.recommended_dir.mkdir(parents=True, exist_ok=True)
        self.keyword_skill = InterestKeywordExpandSkill()
        self.fit_skill = FitScoreRankSkill()
        self.priority_skill = DeadlinePriorityRankSkill()

    def run(self, input_data: Dict[str, Any] | None = None) -> Tuple[bool, str, Dict[str, Any]]:
        input_data = input_data or {}
        profile = input_data.get("user_profile") or self._load_profile(input_data.get("profile_path"))
        opportunities = input_data.get("opportunities") or self._load_parsed(input_data.get("parsed_paths"))
        if not profile:
            return False, "사용자 프로필이 없습니다.", {}
        _, _, keywords = self.keyword_skill.execute({"user_profile": profile})
        recommended = []
        for opportunity in opportunities:
            _, _, fit = self.fit_skill.execute({
                "user_profile": profile,
                "opportunity": opportunity,
                "expanded_keywords": keywords,
            })
            _, _, priority = self.priority_skill.execute({
                "fit_score": fit["fit_score"],
                "submission_deadline": opportunity.get("schedule", {}).get("submission_deadline"),
                "direct_interest": fit["fit_score"] >= 70,
            })
            merged = dict(opportunity)
            merged["personalization"] = {
                "user_id": profile.get("user_id"),
                **fit,
                **priority,
                "calendar_conflict_status": "needs_check",
            }
            merged.setdefault("workflow", {})["notion_status"] = "recommended"
            self._save_recommended(merged)
            recommended.append(merged)
        output = {"recommended_count": len(recommended), "recommended": recommended}
        return True, f"추천 계산 완료: {len(recommended)}건", output

    def _load_profile(self, profile_path: str | None) -> Dict[str, Any]:
        path = Path(profile_path) if profile_path else self._latest_file(self.profiles_dir, "user_profile_*.json")
        if not path:
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _load_parsed(self, parsed_paths: List[str] | None) -> List[Dict[str, Any]]:
        paths = [Path(p) for p in parsed_paths] if parsed_paths else sorted(self.parsed_dir.glob("parsed_opportunity_*.json"))
        items = []
        for path in paths:
            try:
                items.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
        return items

    def _latest_file(self, directory: Path, pattern: str) -> Path | None:
        paths = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
        return paths[0] if paths else None

    def _save_recommended(self, opportunity: Dict[str, Any]) -> None:
        opportunity_id = opportunity.get("opportunity_id", "unknown").replace("opp_", "")
        path = self.recommended_dir / f"recommended_opportunity_{opportunity_id}.json"
        path.write_text(json.dumps(opportunity, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    stdin_text = sys.stdin.read()
    payload = json.loads(stdin_text) if stdin_text.strip() else {}
    ok, message, output = FitPriorityAgent().run(payload)
    print(message)
    print(json.dumps(output, ensure_ascii=False, indent=2))
