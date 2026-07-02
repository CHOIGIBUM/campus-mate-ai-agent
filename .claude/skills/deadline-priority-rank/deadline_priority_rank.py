"""deadline-priority-rank Skill."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Tuple

KST = timezone(timedelta(hours=9))


class DeadlinePriorityRankSkill:
    """Classify opportunity priority from fit score and deadline."""

    def execute(self, input_data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        fit_score = int(input_data.get("fit_score", 0))
        deadline = input_data.get("submission_deadline") or input_data.get("deadline")
        today = self._parse_date(input_data.get("today")) or datetime.now(KST).date()
        d_day = self._d_day(deadline, today)
        direct_interest = bool(input_data.get("direct_interest", False))

        if d_day is not None and d_day >= 0 and d_day <= 7 and fit_score >= 75:
            priority = "긴급"
            category = "긴급 (D-7 이내 AND 적합도 75점 이상)"
        elif fit_score >= 70 or direct_interest:
            priority = "중요"
            category = "중요 (적합도 70점 이상 또는 관심 분야 직접 관련)"
        else:
            priority = "참고"
            category = "참고 (검토 가능)"

        output = {
            "priority": priority,
            "d_day": d_day,
            "priority_reason": self._reason(priority, d_day, fit_score),
            "priority_category": category,
            "timeline": self._timeline(deadline, today),
        }
        return True, f"우선순위 분류 완료: {priority}", output

    def _d_day(self, deadline: Any, today: Any) -> Any:
        target = self._parse_date(deadline)
        if not target:
            return None
        return (target - today).days

    def _parse_date(self, value: Any) -> Any:
        if not value or value == "확인 필요":
            return None
        match = re.search(r"\d{4}-\d{2}-\d{2}", str(value))
        if not match:
            return None
        return datetime.fromisoformat(match.group(0)).date()

    def _reason(self, priority: str, d_day: Any, fit_score: int) -> str:
        d_text = "마감일 확인 필요" if d_day is None else f"D-{d_day}" if d_day >= 0 else f"D+{abs(d_day)}"
        return f"{d_text}, fit_score {fit_score}점 기준 {priority} 분류"

    def _timeline(self, deadline: Any, today: Any) -> Dict[str, Any]:
        target = self._parse_date(deadline)
        if not target:
            return {"today": today.isoformat(), "d_day": None}
        return {
            "today": today.isoformat(),
            "d_minus_7": (target - timedelta(days=7)).isoformat(),
            "d_minus_5": (target - timedelta(days=5)).isoformat(),
            "d_day": target.isoformat(),
        }


if __name__ == "__main__":
    import sys

    stdin_text = sys.stdin.read()
    payload = json.loads(stdin_text) if stdin_text.strip() else {}
    ok, message, output = DeadlinePriorityRankSkill().execute(payload)
    print(message)
    print(json.dumps(output, ensure_ascii=False, indent=2))
