from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

try:
    payload = json.load(sys.stdin)
except Exception:
    payload = {}
root = Path(os.environ.get("CLAUDE_PROJECT_DIR", payload.get("cwd", ".")))
runs_dir = root / "_workspace" / "runs"
report = {
    "checked_at": datetime.now(UTC).isoformat(),
    "runs_directory_exists": runs_dir.exists(),
    "latest_run": None,
    "warnings": [],
}
if runs_dir.exists():
    runs = sorted((p for p in runs_dir.iterdir() if p.is_dir()), key=lambda p: p.name)
    if runs:
        latest = runs[-1]
        report["latest_run"] = latest.name
        if not (latest / "manifest.json").exists():
            report["warnings"].append("latest run has no manifest.json")
        if not (latest / "handoffs").exists():
            report["warnings"].append("latest run has no handoffs directory")
log = root / "_workspace" / "logs" / "validation-last.json"
log.parent.mkdir(parents=True, exist_ok=True)
log.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
if report["warnings"]:
    print("Campus Mate workspace warnings: " + "; ".join(report["warnings"]))
