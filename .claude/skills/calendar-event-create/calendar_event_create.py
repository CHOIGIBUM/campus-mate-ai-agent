"""calendar-event-create Skill."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

KST = timezone(timedelta(hours=9))


class CalendarEventCreateSkill:
    """Create local Calendar event records for accepted opportunities."""

    def __init__(self, calendar_dir: str = "./data/calendar") -> None:
        self.calendar_dir = Path(calendar_dir)
        self.calendar_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, input_data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        opportunity_id = input_data.get("opportunity_id")
        events = input_data.get("events") or []
        if not opportunity_id or not events:
            return False, "opportunity_id와 events가 필요합니다.", {}
        created = []
        for idx, event in enumerate(events, 1):
            created.append({
                "event_type": event.get("event_type", "event"),
                "event_name": event.get("event_name") or event.get("title"),
                "start_time": event.get("start") or event.get("start_time"),
                "end_time": event.get("end") or event.get("end_time"),
                "google_calendar_event_id": f"local_cal_{opportunity_id}_{idx:02d}",
                "calendar_status": "created",
                "description": event.get("description"),
                "location": event.get("location"),
            })
        output = {
            "opportunity_id": opportunity_id,
            "opportunity_title": input_data.get("opportunity_title"),
            "user_id": input_data.get("user_id"),
            "events_created": created,
            "created_events": created,
            "total_events_created": len(created),
            "conflict_status": input_data.get("conflict_status", "no_conflict"),
            "created_at": datetime.now(KST).isoformat(timespec="seconds"),
        }
        path = self.calendar_dir / f"calendar_event_created_{opportunity_id.replace('opp_', '')}.json"
        path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        return True, f"Calendar 이벤트 생성 완료: {len(created)}개", output


if __name__ == "__main__":
    import sys

    stdin_text = sys.stdin.read()
    payload = json.loads(stdin_text) if stdin_text.strip() else {}
    ok, message, output = CalendarEventCreateSkill().execute(payload)
    print(message)
    print(json.dumps(output, ensure_ascii=False, indent=2))
