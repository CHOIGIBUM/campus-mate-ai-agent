"""notion-dashboard-sync Skill.

MVP mode stores Notion-like cards in a local JSON database. The shape mirrors
the real Notion properties so the agent workflow can be tested before API
credentials are available.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Tuple

KST = timezone(timedelta(hours=9))


class NotionDashboardSyncSkill:
    """Create/update/read local dashboard cards for opportunities."""

    def __init__(self, logs_dir: str = "./data/logs", dashboard_path: str = "./data/notion/dashboard.json") -> None:
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.dashboard_path = Path(dashboard_path)
        self.dashboard_path.parent.mkdir(parents=True, exist_ok=True)

    def execute(self, input_data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        action = input_data.get("action", "upsert")
        if action == "monitor":
            return self._monitor(input_data)
        opportunity = input_data.get("opportunity")
        if not opportunity:
            return False, "opportunity 입력이 필요합니다.", {}
        dashboard = self._load_dashboard()
        opportunity_id = opportunity.get("opportunity_id")
        if not opportunity_id:
            return False, "opportunity_id가 필요합니다.", {}

        now = datetime.now(KST).isoformat(timespec="seconds")
        pages = dashboard.setdefault("pages", {})
        existing = pages.get(opportunity_id)
        status = input_data.get("status") or (existing or {}).get("status") or "New"
        page = {
            "notion_page_id": (existing or {}).get("notion_page_id") or f"local_notion_{opportunity_id}",
            "opportunity_id": opportunity_id,
            "status": status,
            "properties": self._properties(opportunity, status),
            "opportunity": opportunity,
            "created_at": (existing or {}).get("created_at") or now,
            "updated_at": now,
        }
        pages[opportunity_id] = page
        self._save_dashboard(dashboard)
        self._append_log("upsert" if existing else "create", page)
        result = {
            "action": "updated" if existing else "created",
            "notion_page_id": page["notion_page_id"],
            "status": status,
            "timestamp": now,
            "properties": page["properties"],
        }
        return True, f"로컬 Notion 카드 {result['action']}: {opportunity_id}", result

    def _monitor(self, input_data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        dashboard = self._load_dashboard()
        target_status = input_data.get("target_status", "Accept")
        changes = [
            {
                "opportunity_id": opp_id,
                "notion_page_id": page.get("notion_page_id"),
                "status_new": page.get("status"),
                "opportunity": page.get("opportunity"),
            }
            for opp_id, page in dashboard.get("pages", {}).items()
            if page.get("status") == target_status
        ]
        return True, f"{target_status} 상태 {len(changes)}건 감지", {"changes": changes}

    def _properties(self, opportunity: Dict[str, Any], status: str) -> Dict[str, Any]:
        basic = opportunity.get("basic_info", {})
        schedule = opportunity.get("schedule", {})
        details = opportunity.get("details", {})
        personalization = opportunity.get("personalization", {})
        return {
            "프로그램명": basic.get("title"),
            "원문 링크": opportunity.get("raw_source", {}).get("source_url"),
            "유형": basic.get("category"),
            "출처": opportunity.get("raw_source", {}).get("source_name"),
            "적합도": personalization.get("fit_score"),
            "우선순위": personalization.get("priority"),
            "마감일": schedule.get("submission_deadline"),
            "행사일": schedule.get("event_start"),
            "참가 가능 여부": personalization.get("eligibility_status"),
            "일정 충돌": personalization.get("calendar_conflict_status", "needs_check"),
            "상태": status,
            "추천 이유": " / ".join(personalization.get("recommendation_reason", [])),
            "해야 할 일": self._todo_text(details),
            "Timely ID": opportunity.get("opportunity_id"),
        }

    def _todo_text(self, details: Dict[str, Any]) -> str:
        materials = details.get("required_materials") or []
        if materials:
            return " / ".join(f"{item} 준비" for item in materials)
        return "공고 확인 / 팀원 필요 여부 판단 / 제출물 확인"

    def _load_dashboard(self) -> Dict[str, Any]:
        if not self.dashboard_path.exists():
            return {"database_name": "Campus Career AI - 공모전 현황판", "pages": {}}
        try:
            return json.loads(self.dashboard_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"database_name": "Campus Career AI - 공모전 현황판", "pages": {}}

    def _save_dashboard(self, dashboard: Dict[str, Any]) -> None:
        self.dashboard_path.write_text(json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8")

    def _append_log(self, sync_type: str, page: Dict[str, Any]) -> None:
        today = datetime.now(KST).date().isoformat()
        path = self.logs_dir / f"notion_sync_log_{today}.json"
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                data = {"date": today, "syncs": []}
        else:
            data = {"date": today, "syncs": []}
        data["syncs"].append({
            "timestamp": datetime.now(KST).isoformat(timespec="seconds"),
            "sync_type": sync_type,
            "opportunity_id": page.get("opportunity_id"),
            "notion_page_id": page.get("notion_page_id"),
            "status": page.get("status"),
        })
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    import sys

    stdin_text = sys.stdin.read()
    payload = json.loads(stdin_text) if stdin_text.strip() else {}
    ok, message, output = NotionDashboardSyncSkill().execute(payload)
    print(message)
    print(json.dumps(output, ensure_ascii=False, indent=2))
