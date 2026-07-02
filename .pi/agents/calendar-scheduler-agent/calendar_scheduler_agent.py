"""Calendar Scheduler Agent runner."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[3]
for skill_name in [
    "notion-dashboard-sync",
    "accept-state-sync",
    "calendar-freebusy-check",
    "calendar-event-create",
]:
    sys.path.insert(0, str(ROOT / ".pi" / "skills" / skill_name))

from accept_state_sync import AcceptStateSyncSkill  # noqa: E402
from calendar_event_create import CalendarEventCreateSkill  # noqa: E402
from calendar_freebusy_check import CalendarFreebusyCheckSkill  # noqa: E402
from notion_dashboard_sync import NotionDashboardSyncSkill  # noqa: E402


class CalendarSchedulerAgent:
    def __init__(self) -> None:
        self.notion_skill = NotionDashboardSyncSkill()
        self.accept_skill = AcceptStateSyncSkill()
        self.freebusy_skill = CalendarFreebusyCheckSkill()
        self.create_skill = CalendarEventCreateSkill()

    def run(self, input_data: Dict[str, Any] | None = None) -> Tuple[bool, str, Dict[str, Any]]:
        input_data = input_data or {}
        changes = input_data.get("accepted_changes")
        if changes is None:
            _, _, monitor = self.notion_skill.execute({"action": "monitor", "target_status": "Accept"})
            changes = monitor.get("changes", [])
        scheduled = []
        blocked = []
        for change in changes:
            opportunity = change.get("opportunity") or input_data.get("opportunity")
            if not opportunity:
                blocked.append({"change": change, "reason": "opportunity 누락"})
                continue
            _, _, sync = self.accept_skill.execute({
                "opportunity_id": opportunity.get("opportunity_id"),
                "notion_page_id": change.get("notion_page_id"),
                "status_old": change.get("status_old"),
                "status_new": "Accept",
            })
            events = self._build_events(opportunity, input_data.get("user_id"))
            if not events:
                blocked.append({"opportunity_id": opportunity.get("opportunity_id"), "reason": "일정 생성에 필요한 날짜 없음"})
                continue
            _, _, freebusy = self.freebusy_skill.execute({"events_to_check": events, "busy_events": input_data.get("busy_events", [])})
            if freebusy["conflict_status"] == "conflict":
                blocked.append({"opportunity_id": opportunity.get("opportunity_id"), "reason": "calendar_conflict", "details": freebusy})
                continue
            _, _, created = self.create_skill.execute({
                "opportunity_id": opportunity.get("opportunity_id"),
                "opportunity_title": opportunity.get("basic_info", {}).get("title"),
                "user_id": input_data.get("user_id") or opportunity.get("personalization", {}).get("user_id"),
                "events": events,
                "conflict_status": freebusy["conflict_status"],
            })
            self.notion_skill.execute({"opportunity": opportunity, "status": "Scheduled"})
            scheduled.append({"sync": sync, "calendar": created})
        return True, f"Calendar 일정화 완료: {len(scheduled)}건, 보류 {len(blocked)}건", {"scheduled": scheduled, "blocked": blocked}

    def _build_events(self, opportunity: Dict[str, Any], user_id: str | None) -> List[Dict[str, Any]]:
        title = opportunity.get("basic_info", {}).get("title", "공고")
        deadline = self._parse_dt(opportunity.get("schedule", {}).get("submission_deadline"))
        if not deadline:
            return []
        events = [{
            "event_type": "deadline",
            "event_name": f"{title} - 마감",
            "start": deadline.isoformat(),
            "end": (deadline + timedelta(minutes=1)).isoformat(),
            "description": opportunity.get("raw_source", {}).get("source_url"),
        }]
        for days, name, hour in [(5, "팀원 모집 및 아이디어 회의", 19), (3, "기획서 작성", 19), (1, "제출물 최종 점검", 21)]:
            start = (deadline - timedelta(days=days)).replace(hour=hour, minute=0, second=0)
            events.append({
                "event_type": "prep",
                "event_name": f"{title} - {name}",
                "start": start.isoformat(),
                "end": (start + timedelta(hours=2)).isoformat(),
                "description": f"D-{days}: {name}",
            })
        return events

    def _parse_dt(self, value: Any) -> Any:
        if not value or value == "확인 필요":
            return None
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


if __name__ == "__main__":
    stdin_text = sys.stdin.read()
    payload = json.loads(stdin_text) if stdin_text.strip() else {}
    ok, message, output = CalendarSchedulerAgent().run(payload)
    print(message)
    print(json.dumps(output, ensure_ascii=False, indent=2))
