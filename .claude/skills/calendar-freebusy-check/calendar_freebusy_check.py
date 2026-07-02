"""calendar-freebusy-check Skill."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


class CalendarFreebusyCheckSkill:
    """Check proposed events against local busy blocks."""

    def __init__(self, busy_path: str = "./data/calendar/busy_events.json") -> None:
        self.busy_path = Path(busy_path)

    def execute(self, input_data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        events = input_data.get("events_to_check") or []
        busy_events = input_data.get("busy_events")
        if busy_events is None:
            busy_events = self._load_busy_events()
        min_overlap = int(input_data.get("min_overlap_duration", 3600))
        conflicts = []
        for event in events:
            for busy in busy_events:
                overlap = self._overlap_seconds(event, busy)
                if overlap >= min_overlap:
                    conflicts.append({"event": event, "busy_event": busy, "overlap_seconds": overlap})
        status = "conflict" if conflicts else "no_conflict"
        output = {
            "conflict_status": status,
            "busy_events": [c["busy_event"] for c in conflicts],
            "conflicts": conflicts,
        }
        return True, f"Calendar 충돌 검사 완료: {status}", output

    def _load_busy_events(self) -> List[Dict[str, Any]]:
        if not self.busy_path.exists():
            return []
        try:
            return json.loads(self.busy_path.read_text(encoding="utf-8")).get("busy_events", [])
        except json.JSONDecodeError:
            return []

    def _overlap_seconds(self, event: Dict[str, Any], busy: Dict[str, Any]) -> int:
        start = self._parse_dt(event.get("start_time") or event.get("start"))
        end = self._parse_dt(event.get("end_time") or event.get("end"))
        busy_start = self._parse_dt(busy.get("start_time") or busy.get("start"))
        busy_end = self._parse_dt(busy.get("end_time") or busy.get("end"))
        if not all([start, end, busy_start, busy_end]):
            return 0
        overlap_start = max(start, busy_start)
        overlap_end = min(end, busy_end)
        return max(0, int((overlap_end - overlap_start).total_seconds()))

    def _parse_dt(self, value: Any) -> Any:
        if not value or value == "확인 필요":
            return None
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


if __name__ == "__main__":
    import sys

    stdin_text = sys.stdin.read()
    payload = json.loads(stdin_text) if stdin_text.strip() else {}
    ok, message, output = CalendarFreebusyCheckSkill().execute(payload)
    print(message)
    print(json.dumps(output, ensure_ascii=False, indent=2))
