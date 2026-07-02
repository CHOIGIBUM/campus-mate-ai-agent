"""accept-state-sync Skill."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Tuple

KST = timezone(timedelta(hours=9))


class AcceptStateSyncSkill:
    """Convert a Notion Accept status change into internal workflow state."""

    def __init__(self, state_dir: str = "./data/state") -> None:
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.state_dir / "workflow_state.json"

    def execute(self, input_data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        opportunity_id = input_data.get("opportunity_id")
        status_new = input_data.get("status_new") or input_data.get("status")
        if not opportunity_id or not status_new:
            return False, "opportunity_id와 status_new가 필요합니다.", {}
        state = self._load_state()
        workflow_status = "pending_calendar_creation" if status_new == "Accept" else f"user_{status_new.lower()}"
        record = {
            "opportunity_id": opportunity_id,
            "notion_page_id": input_data.get("notion_page_id"),
            "status_old": input_data.get("status_old"),
            "status_new": status_new,
            "workflow_status": workflow_status,
            "trigger_calendar_scheduler": status_new == "Accept",
            "updated_at": datetime.now(KST).isoformat(timespec="seconds"),
        }
        state.setdefault("opportunities", {})[opportunity_id] = record
        self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        return True, f"상태 동기화 완료: {opportunity_id} -> {workflow_status}", {
            "sync_status": "success",
            "internal_state_updated": True,
            **record,
        }

    def _load_state(self) -> Dict[str, Any]:
        if not self.state_path.exists():
            return {"opportunities": {}}
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"opportunities": {}}


if __name__ == "__main__":
    import sys

    stdin_text = sys.stdin.read()
    payload = json.loads(stdin_text) if stdin_text.strip() else {}
    ok, message, output = AcceptStateSyncSkill().execute(payload)
    print(message)
    print(json.dumps(output, ensure_ascii=False, indent=2))
