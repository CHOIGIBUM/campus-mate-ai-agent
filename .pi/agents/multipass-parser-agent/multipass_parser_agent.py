"""Multi-pass Parser Agent runner."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[3]
for skill_name in [
    "html-opportunity-parse",
    "rendered-page-ocr",
    "poster-vision-extract",
    "schema-merge-and-validate",
]:
    sys.path.insert(0, str(ROOT / ".pi" / "skills" / skill_name))

from html_opportunity_parse import HtmlOpportunityParseSkill  # noqa: E402
from poster_vision_extract import PosterVisionExtractSkill  # noqa: E402
from rendered_page_ocr import RenderedPageOcrSkill  # noqa: E402
from schema_merge_and_validate import SchemaMergeAndValidateSkill  # noqa: E402


class MultipassParserAgent:
    def __init__(self) -> None:
        self.collections_dir = ROOT / "data" / "collections"
        self.html_skill = HtmlOpportunityParseSkill()
        self.ocr_skill = RenderedPageOcrSkill()
        self.vision_skill = PosterVisionExtractSkill()
        self.merge_skill = SchemaMergeAndValidateSkill()

    def run(self, input_data: Dict[str, Any] | None = None) -> Tuple[bool, str, Dict[str, Any]]:
        input_data = input_data or {}
        urls = input_data.get("urls") or self._load_urls(input_data.get("collection_path"))
        parsed: List[Dict[str, Any]] = []
        failures: List[Dict[str, Any]] = []
        for index, item in enumerate(urls, 1):
            source_url = item.get("source_url") or item.get("opportunity_url")
            if not source_url and not item.get("html"):
                failures.append({"item": item, "reason": "source_url/html 누락"})
                continue
            html_ok, _, html_result = self.html_skill.execute({
                "opportunity_url": source_url,
                "site_name": item.get("site_name"),
                "title_hint": item.get("title_hint"),
                "html": item.get("html"),
            })
            _, _, ocr_result = self.ocr_skill.execute({
                "opportunity_url": source_url,
                "rendered_text": item.get("rendered_text"),
                "ocr_text": item.get("ocr_text"),
            })
            _, _, vision_result = self.vision_skill.execute({
                "opportunity_url": source_url,
                "image_urls": html_result.get("image_urls", []),
                "poster_text": item.get("poster_text"),
            })
            merge_ok, merge_message, merged = self.merge_skill.execute({
                "opportunity_id": item.get("opportunity_id"),
                "source_url": source_url,
                "source_name": item.get("site_name"),
                "collected_at": item.get("collected_at"),
                "html_result": html_result,
                "ocr_result": ocr_result,
                "vision_result": vision_result,
            })
            if html_ok and merge_ok:
                parsed.append(merged)
            else:
                failures.append({"item": item, "reason": merge_message})
        output = {"parsed_count": len(parsed), "failure_count": len(failures), "parsed": parsed, "failures": failures}
        return True, f"멀티패스 파싱 완료: {len(parsed)}건", output

    def _load_urls(self, collection_path: str | None) -> List[Dict[str, Any]]:
        path = Path(collection_path) if collection_path else self._latest_collection()
        if not path or not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("new_urls", [])

    def _latest_collection(self) -> Path | None:
        paths = sorted(self.collections_dir.glob("daily_collection_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        return paths[0] if paths else None


if __name__ == "__main__":
    stdin_text = sys.stdin.read()
    payload = json.loads(stdin_text) if stdin_text.strip() else {}
    ok, message, output = MultipassParserAgent().run(payload)
    print(message)
    print(json.dumps(output, ensure_ascii=False, indent=2))
