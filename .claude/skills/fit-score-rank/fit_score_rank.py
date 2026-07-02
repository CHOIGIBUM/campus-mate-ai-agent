"""fit-score-rank Skill."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Tuple

KST = timezone(timedelta(hours=9))


class FitScoreRankSkill:
    """Calculate an explainable 0-100 fit score for a user and opportunity."""

    def execute(self, input_data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        profile = input_data.get("user_profile") or {}
        opportunity = input_data.get("opportunity") or input_data.get("parsed_opportunity") or {}
        expanded_keywords = input_data.get("expanded_keywords") or {}
        opp_text = self._opportunity_text(opportunity)

        breakdown = [
            self._major_score(profile, opp_text),
            self._interest_score(profile, opp_text, expanded_keywords),
            self._position_score(profile, opp_text),
            self._eligibility_score(profile, opp_text, opportunity),
            self._schedule_score(opportunity),
            self._region_score(profile, opp_text, opportunity),
        ]
        total = sum(item["earned"] for item in breakdown)
        recommendation_reason = [item["reason"] for item in breakdown if item["earned"] > 0][:3]
        output = {
            "fit_score": max(0, min(100, total)),
            "fit_breakdown": breakdown,
            "recommendation_reason": recommendation_reason,
            "eligibility_status": self._eligibility_status(breakdown),
        }
        return True, f"적합도 계산 완료: {output['fit_score']}점", output

    def _major_score(self, profile: Dict[str, Any], opp_text: str) -> Dict[str, Any]:
        major = profile.get("basic_info", {}).get("major", "")
        major_tokens = self._tokens(major)
        tech_hit = bool(re.search(r"AI|인공지능|데이터|소프트웨어|해커톤|개발|머신러닝", opp_text, re.I))
        earned = 25 if ("AI" in major.upper() and tech_hit) else 15 if any(t in opp_text for t in major_tokens) else 5
        reason = f"{major or '전공 미입력'}와 공고 분야의 관련성"
        return {"category": "전공 적합도", "max_score": 25, "earned": earned, "reason": reason}

    def _interest_score(
        self,
        profile: Dict[str, Any],
        opp_text: str,
        expanded_keywords: Dict[str, Any],
    ) -> Dict[str, Any]:
        base = profile.get("interests", {}).get("fields", [])
        flat = expanded_keywords.get("all_keywords_flattened") or base
        hits = [kw for kw in flat if kw and kw.lower() in opp_text.lower()]
        earned = min(25, len(set(hits)) * 8)
        if not hits and base:
            earned = 5
        reason = "관심 키워드 일치: " + ", ".join(list(dict.fromkeys(hits))[:4]) if hits else "관심 분야 직접 일치 부족"
        return {"category": "관심 분야 적합도", "max_score": 25, "earned": earned, "reason": reason}

    def _position_score(self, profile: Dict[str, Any], opp_text: str) -> Dict[str, Any]:
        positions = profile.get("career_goal", {}).get("positions", [])
        hits = [pos for pos in positions if any(token.lower() in opp_text.lower() for token in self._tokens(pos))]
        earned = 20 if hits else 12 if re.search(r"개발|분석|기획|프로젝트|모델", opp_text) else 4
        reason = "희망 직무 관련 표현 발견" if hits else "일반 역량 개발 기회"
        return {"category": "희망 직무 적합도", "max_score": 20, "earned": earned, "reason": reason}

    def _eligibility_score(self, profile: Dict[str, Any], opp_text: str, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        year = profile.get("basic_info", {}).get("year", "")
        eligibility = opportunity.get("details", {}).get("eligibility") or opportunity.get("basic_info", {}).get("target_user", "")
        text = f"{opp_text} {eligibility}"
        if re.search(r"대학생|재학생|대학원생|청년|누구나", text):
            earned, reason = 15, "대학생/청년 대상 조건과 부합"
        elif "확인 필요" in text:
            earned, reason = 7, "참가 자격 확인 필요"
        else:
            earned, reason = 5, f"{year or '학년'} 기준 자격 직접 확인 필요"
        return {"category": "참가 자격 적합도", "max_score": 15, "earned": earned, "reason": reason}

    def _schedule_score(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        deadline = opportunity.get("schedule", {}).get("submission_deadline")
        d_day = self._d_day(deadline)
        if d_day is None:
            earned, reason = 3, "마감일 확인 필요"
        elif d_day < 0:
            earned, reason = 0, "이미 마감된 공고"
        elif d_day <= 7:
            earned, reason = 8, f"마감 D-{d_day}, 즉시 준비 필요"
        else:
            earned, reason = 10, f"마감 D-{d_day}, 준비 시간 확보 가능"
        return {"category": "일정 가능성", "max_score": 10, "earned": earned, "reason": reason}

    def _region_score(self, profile: Dict[str, Any], opp_text: str, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        regions = profile.get("preferences", {}).get("regions", [])
        location = opportunity.get("basic_info", {}).get("location", "")
        if "온라인" in location or "온라인" in opp_text:
            earned, reason = 5, "온라인 참여 가능"
        elif any(region and region in f"{location} {opp_text}" for region in regions):
            earned, reason = 5, "선호 지역과 일치"
        elif location == "확인 필요":
            earned, reason = 2, "활동 지역 확인 필요"
        else:
            earned, reason = 0, "선호 지역과 직접 일치하지 않음"
        return {"category": "지역/온오프라인 적합도", "max_score": 5, "earned": earned, "reason": reason}

    def _eligibility_status(self, breakdown: List[Dict[str, Any]]) -> str:
        item = next((b for b in breakdown if b["category"] == "참가 자격 적합도"), None)
        if not item:
            return "조건 확인 필요"
        if item["earned"] >= 15:
            return "가능"
        if item["earned"] >= 7:
            return "조건 확인 필요"
        return "불가능"

    def _opportunity_text(self, opportunity: Dict[str, Any]) -> str:
        parts = [
            opportunity.get("basic_info", {}),
            opportunity.get("details", {}),
            opportunity.get("schedule", {}),
        ]
        return json.dumps(parts, ensure_ascii=False)

    def _tokens(self, text: str) -> List[str]:
        return [token for token in re.split(r"[\s,/()·-]+", text or "") if len(token) >= 2]

    def _d_day(self, deadline: Any) -> Any:
        if not deadline or deadline == "확인 필요":
            return None
        match = re.search(r"\d{4}-\d{2}-\d{2}", str(deadline))
        if not match:
            return None
        target = datetime.fromisoformat(match.group(0)).date()
        return (target - datetime.now(KST).date()).days


if __name__ == "__main__":
    import sys

    stdin_text = sys.stdin.read()
    payload = json.loads(stdin_text) if stdin_text.strip() else {}
    ok, message, output = FitScoreRankSkill().execute(payload)
    print(message)
    print(json.dumps(output, ensure_ascii=False, indent=2))
