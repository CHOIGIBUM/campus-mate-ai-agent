from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

try:
    payload = json.load(sys.stdin)
except Exception:
    raise SystemExit(0) from None

root = Path(os.environ.get("CLAUDE_PROJECT_DIR", payload.get("cwd", ".")))
log = root / "_workspace" / "logs" / "subagents.jsonl"
log.parent.mkdir(parents=True, exist_ok=True)
record = {
    "logged_at": datetime.now(UTC).isoformat(),
    "session_id": payload.get("session_id"),
    "agent_type": payload.get("agent_type") or payload.get("subagent_type"),
    "hook_event_name": payload.get("hook_event_name"),
}
with log.open("a", encoding="utf-8") as fh:
    fh.write(json.dumps(record, ensure_ascii=False) + "\n")
