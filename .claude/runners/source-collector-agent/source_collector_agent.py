"""Source Collector Agent runner."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "source-watchlist-crawl"))

from source_watchlist_crawl import SourceWatchlistCrawlSkill  # noqa: E402


class SourceCollectorAgent:
    def __init__(self) -> None:
        self.skill = SourceWatchlistCrawlSkill()

    def run(self, input_data: Dict[str, Any] | None = None) -> Tuple[bool, str, Dict[str, Any]]:
        return self.skill.execute(input_data or {})


if __name__ == "__main__":
    stdin_text = sys.stdin.read()
    payload = json.loads(stdin_text) if stdin_text.strip() else {}
    ok, message, output = SourceCollectorAgent().run(payload)
    print(message)
    print(json.dumps(output, ensure_ascii=False, indent=2))
