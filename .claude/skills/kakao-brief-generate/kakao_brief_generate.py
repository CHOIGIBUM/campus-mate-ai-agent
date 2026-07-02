"""kakao-brief-generate Skill."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

KST = timezone(timedelta(hours=9))


class KakaoBriefGenerateSkill:
    """Generate a Kakao-ready daily brief as Markdown plus a send log."""

    def __init__(self, kakao_dir: str = "./data/kakao") -> None:
        self.kakao_dir = Path(kakao_dir)
        self.kakao_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, input_data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        now = datetime.now(KST)
        report_date = input_data.get("report_date") or now.date().isoformat()
        user_name = input_data.get("user_name") or "사용자"
        notion_url = input_data.get("notion_url") or ""
        recommendations = sorted(input_data.get("new_recommendations") or [], key=lambda x: x.get("fit_score", 0), reverse=True)
        urgent = input_data.get("urgent_deadlines") or [
            item for item in recommendations if item.get("priority") == "긴급" or (item.get("d_day") is not None and item.get("d_day") <= 7)
        ]
        conflicts = input_data.get("conflicts") or []
        needs_review = input_data.get("needs_review") or [
            item for item in recommendations if item.get("validation_status", {}).get("needs_review")
        ]
        markdown = self._build_markdown(user_name, urgent, recommendations[:5], conflicts, needs_review, notion_url)
        brief_path = self.kakao_dir / f"kakao_brief_{report_date}.md"
        log_path = self.kakao_dir / f"kakao_send_log_{report_date}.json"
        brief_path.write_text(markdown, encoding="utf-8")
        log = {
            "date": report_date,
            "actual_generated_time": now.isoformat(timespec="seconds"),
            "user_id": input_data.get("user_id"),
            "recipient_name": user_name,
            "status": "generated",
            "send_method": "file_save",
            "file_path": str(brief_path),
            "message_length": len(markdown),
            "urgent_count": len(urgent),
            "new_recommendation_count": len(recommendations[:5]),
            "conflict_count": len(conflicts),
            "review_needed_count": len(needs_review),
            "note": "MVP: 메시지 파일 저장. 향후 Kakao API 연동",
        }
        log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
        output = {"brief_path": str(brief_path), "log_path": str(log_path), "message": markdown, "log": log}
        return True, f"Kakao 브리프 생성 완료: {brief_path.name}", output

    def _build_markdown(
        self,
        user_name: str,
        urgent: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]],
        conflicts: List[Dict[str, Any]],
        needs_review: List[Dict[str, Any]],
        notion_url: str,
    ) -> str:
        lines = [f"# [Campus Career AI] {user_name}님 기준 오늘의 공모전 브리핑", ""]
        lines.extend(["## 긴급 마감", *self._items(urgent, "긴급 항목이 없습니다."), ""])
        lines.extend(["## 신규 추천", *self._items(recommendations, "신규 추천이 없습니다."), ""])
        lines.extend(["## 일정 충돌", *self._items(conflicts, "감지된 충돌이 없습니다."), ""])
        lines.extend(["## 확인 필요", *self._items(needs_review, "확인 필요 항목이 없습니다."), ""])
        if notion_url:
            lines.extend(["---", f"[Notion 현황판에서 Accept/Hold/Reject 선택]({notion_url})"])
        return "\n".join(lines).strip() + "\n"

    def _items(self, items: List[Dict[str, Any]], empty: str) -> List[str]:
        if not items:
            return [f"- {empty}"]
        lines = []
        for idx, item in enumerate(items, 1):
            title = item.get("title") or item.get("basic_info", {}).get("title") or "제목 확인 필요"
            score = item.get("fit_score") or item.get("personalization", {}).get("fit_score")
            priority = item.get("priority") or item.get("personalization", {}).get("priority")
            d_day = item.get("d_day") or item.get("personalization", {}).get("d_day")
            reason = item.get("reason") or ", ".join(item.get("recommendation_reason") or item.get("personalization", {}).get("recommendation_reason", [])[:2])
            meta = []
            if priority:
                meta.append(str(priority))
            if score is not None:
                meta.append(f"{score}점")
            if d_day is not None:
                meta.append(f"D-{d_day}" if d_day >= 0 else f"D+{abs(d_day)}")
            suffix = f" ({' / '.join(meta)})" if meta else ""
            reason_text = f" - {reason}" if reason else ""
            lines.append(f"{idx}. {title}{suffix}{reason_text}")
        return lines


if __name__ == "__main__":
    import sys

    stdin_text = sys.stdin.read()
    payload = json.loads(stdin_text) if stdin_text.strip() else {}
    ok, message, output = KakaoBriefGenerateSkill().execute(payload)
    print(message)
    print(json.dumps(output, ensure_ascii=False, indent=2))
