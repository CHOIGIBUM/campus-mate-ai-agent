"""schema-merge-and-validate Skill."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

KST = timezone(timedelta(hours=9))


class SchemaMergeAndValidateSkill:
    """Merge parser outputs into the Campus Career AI opportunity schema."""

    BASIC_FIELDS = {
        "title": ("basic_info", "title"),
        "category": ("basic_info", "category"),
        "organizer": ("basic_info", "organizer"),
        "eligibility": ("basic_info", "target_user"),
        "location": ("basic_info", "location"),
        "online_offline": ("basic_info", "online_offline"),
    }
    SCHEDULE_FIELDS = {
        "submission_deadline": ("schedule", "submission_deadline"),
    }
    DETAIL_FIELDS = {
        "summary": ("details", "summary"),
        "eligibility": ("details", "eligibility"),
        "application_method": ("details", "application_method"),
        "contact": ("details", "contact"),
    }
    METHOD_ORDER = {"html": 0, "rendered_ocr": 1, "rendered_pdf_ocr": 1, "poster_vision": 2, "vision": 2}

    def __init__(self, parsed_dir: str = "./data/parsed") -> None:
        self.parsed_dir = Path(parsed_dir)
        self.parsed_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, input_data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        now = datetime.now(KST)
        opportunity_id = input_data.get("opportunity_id") or self._generate_opportunity_id(now)
        parser_results = self._collect_parser_results(input_data)
        source_url = input_data.get("source_url") or self._first_value(parser_results, "source_url") or ""
        source_name = input_data.get("source_name") or self._first_value(parser_results, "site_name") or "unknown"

        extracted_by_field = self._group_fields(parser_results)
        final_values: Dict[str, Any] = {}
        metadata: Dict[str, Any] = {}
        conflict_fields: List[str] = []

        all_fields = set(self.BASIC_FIELDS) | set(self.SCHEDULE_FIELDS) | set(self.DETAIL_FIELDS)
        for field_name in sorted(all_fields):
            selected, conflict = self._select_field(field_name, extracted_by_field.get(field_name, []))
            final_values[field_name] = selected["value"]
            metadata[field_name] = selected
            if conflict:
                metadata[field_name]["conflict"] = conflict
                conflict_fields.append(field_name)

        output = {
            "opportunity_id": opportunity_id,
            "raw_source": {
                "source_name": source_name,
                "source_type": input_data.get("source_type", "contest_site"),
                "source_url": source_url,
                "collected_at": input_data.get("collected_at") or now.isoformat(timespec="seconds"),
                "parse_methods_used": [r.get("parse_method") for r in parser_results if r.get("parse_method")],
            },
            "basic_info": {
                "title": final_values.get("title", "확인 필요"),
                "category": final_values.get("category", "확인 필요"),
                "organizer": final_values.get("organizer", "확인 필요"),
                "target_user": final_values.get("eligibility", "확인 필요"),
                "location": final_values.get("location", "확인 필요"),
                "online_offline": final_values.get("online_offline", "확인 필요"),
            },
            "schedule": {
                "recruitment_start": "확인 필요",
                "recruitment_end": final_values.get("submission_deadline", "확인 필요"),
                "submission_deadline": final_values.get("submission_deadline", "확인 필요"),
                "result_announcement": "확인 필요",
                "event_start": "확인 필요",
                "event_end": "확인 필요",
            },
            "details": {
                "summary": final_values.get("summary", "확인 필요"),
                "eligibility": final_values.get("eligibility", "확인 필요"),
                "required_materials": [],
                "benefits": [],
                "award": "확인 필요",
                "application_method": final_values.get("application_method", "확인 필요"),
                "contact": final_values.get("contact", "확인 필요"),
            },
            "extraction_metadata": metadata,
            "validation_status": self._validation_status(final_values, conflict_fields),
            "workflow": {
                "notion_status": "new",
                "user_decision": "pending",
                "timely_status": "stored",
                "calendar_status": "not_created",
                "kakao_report_status": "queued",
            },
        }
        self._save(output, opportunity_id)
        return True, f"스키마 병합 완료: {opportunity_id}", output

    def _collect_parser_results(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for key in ("html_result", "ocr_result", "vision_result"):
            value = input_data.get(key)
            if value:
                results.append(value)
        results.extend(input_data.get("parser_results") or [])
        return results

    def _group_fields(self, parser_results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for result in parser_results:
            method = result.get("parse_method", "unknown")
            if result.get("status") not in {"success", "needs_review"}:
                continue
            for field_name, field_data in (result.get("extracted_fields") or {}).items():
                value = field_data.get("value") if isinstance(field_data, dict) else field_data
                if not value:
                    continue
                grouped.setdefault(field_name, []).append({
                    "value": value,
                    "source_method": method,
                    "evidence": field_data.get("evidence", "") if isinstance(field_data, dict) else "",
                    "confidence": int(field_data.get("confidence", 0)) if isinstance(field_data, dict) else 0,
                })
        return grouped

    def _select_field(self, field_name: str, candidates: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        valid = [c for c in candidates if c.get("value") and c.get("value") != "확인 필요"]
        if not valid:
            return {
                "value": "확인 필요",
                "source_method": None,
                "evidence": "",
                "confidence": 0,
            }, None

        valid.sort(key=lambda c: (self.METHOD_ORDER.get(c.get("source_method"), 9), -int(c.get("confidence", 0))))
        selected = dict(valid[0])
        normalized_values = {self._normalize_value(c["value"]) for c in valid}
        conflict = None
        if len(normalized_values) > 1:
            conflict = {
                "status": "needs_review",
                "candidates": [
                    {
                        "source_method": c.get("source_method"),
                        "value": c.get("value"),
                        "confidence": c.get("confidence"),
                    }
                    for c in valid
                ],
            }
        return selected, conflict

    def _validation_status(self, final_values: Dict[str, Any], conflict_fields: List[str]) -> Dict[str, Any]:
        required = ["title", "submission_deadline", "eligibility"]
        missing = [field for field in required if final_values.get(field) in {None, "", "확인 필요"}]
        return {
            "conflict": bool(conflict_fields),
            "needs_review": bool(conflict_fields or missing),
            "review_note": self._review_note(conflict_fields, missing),
            "conflict_fields": conflict_fields,
            "missing_required_fields": missing,
        }

    def _review_note(self, conflict_fields: List[str], missing: List[str]) -> Optional[str]:
        notes = []
        if conflict_fields:
            notes.append("충돌 필드: " + ", ".join(conflict_fields))
        if missing:
            notes.append("확인 필요 필드: " + ", ".join(missing))
        return " / ".join(notes) if notes else None

    def _normalize_value(self, value: Any) -> str:
        text = re.sub(r"\s+", " ", str(value)).strip().lower()
        return text.replace(".", "-").replace("/", "-")

    def _first_value(self, results: List[Dict[str, Any]], key: str) -> Optional[str]:
        for result in results:
            if result.get(key):
                return result[key]
        return None

    def _generate_opportunity_id(self, now: datetime) -> str:
        today = now.strftime("%Y%m%d")
        existing = list(self.parsed_dir.glob(f"parsed_opportunity_{today}_*.json"))
        return f"opp_{today}_{len(existing) + 1:03d}"

    def _save(self, output: Dict[str, Any], opportunity_id: str) -> None:
        path = self.parsed_dir / f"parsed_opportunity_{opportunity_id.replace('opp_', '')}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import sys

    stdin_text = sys.stdin.read()
    payload = json.loads(stdin_text) if stdin_text.strip() else {}
    ok, message, output = SchemaMergeAndValidateSkill().execute(payload)
    print(message)
    print(json.dumps(output, ensure_ascii=False, indent=2))
