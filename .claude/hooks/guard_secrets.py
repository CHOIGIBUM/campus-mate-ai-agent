from __future__ import annotations

import json
import re
import sys

PATTERNS = [
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"(?:ntn_|secret_)[A-Za-z0-9_-]{12,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}", re.I),
]

try:
    payload = json.load(sys.stdin)
except Exception:
    raise SystemExit(0) from None

tool_input = payload.get("tool_input") or {}
text = "\n".join(str(tool_input.get(k, "")) for k in ("content", "new_string", "old_string"))
if any(pattern.search(text) for pattern in PATTERNS):
    print(json.dumps({
        "decision": "block",
        "reason": "Potential live credential detected. Use environment variables or Timely Secrets and write only placeholder values."
    }))
