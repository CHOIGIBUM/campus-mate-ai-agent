"""rendered-page-ocr Skill.

MVP implementation: consume provided OCR/rendered text when available and
return a conservative skipped result otherwise. This keeps multi-pass parser
attempt logs explicit before a real OCR engine is connected.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Tuple

KST = timezone(timedelta(hours=9))


class RenderedPageOcrSkill:
    def execute(self, input_data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        text = input_data.get("rendered_text") or input_data.get("ocr_text") or ""
        if not text:
            return True, "OCR 입력 없음: skipped", {
                "parse_method": "rendered_ocr",
                "status": "skipped",
                "reason": "OCR engine/text not provided",
                "source_url": input_data.get("opportunity_url") or input_data.get("source_url"),
                "extracted_fields": {},
                "parsed_at": datetime.now(KST).isoformat(timespec="seconds"),
            }
        fields = {
            "submission_deadline": self._deadline(text),
            "eligibility": self._line_field(text, "참가 대상|지원 자격|대상"),
            "contact": self._line_field(text, "문의|연락처|이메일"),
        }
        return True, "OCR 텍스트 파싱 완료", {
            "parse_method": "rendered_ocr",
            "status": "success",
            "source_url": input_data.get("opportunity_url") or input_data.get("source_url"),
            "extracted_fields": fields,
            "parsed_at": datetime.now(KST).isoformat(timespec="seconds"),
        }

    def _deadline(self, text: str) -> Dict[str, Any]:
        match = re.search(r"(\d{4})[.\-/년 ]+(\d{1,2})[.\-/월 ]+(\d{1,2})", text)
        if not match:
            return {"value": "확인 필요", "evidence": "", "confidence": 0}
        year, month, day = [int(v) for v in match.groups()]
        return {
            "value": f"{year:04d}-{month:02d}-{day:02d}T23:59:00+09:00",
            "evidence": match.group(0),
            "confidence": 65,
        }

    def _line_field(self, text: str, label_pattern: str) -> Dict[str, Any]:
        match = re.search(rf"(?:{label_pattern})\s*[:：]\s*([^\n\r]{{2,100}})", text)
        if not match:
            return {"value": "확인 필요", "evidence": "", "confidence": 0}
        return {"value": match.group(1).strip(), "evidence": match.group(0), "confidence": 60}


if __name__ == "__main__":
    import sys

    stdin_text = sys.stdin.read()
    payload = json.loads(stdin_text) if stdin_text.strip() else {}
    ok, message, output = RenderedPageOcrSkill().execute(payload)
    print(message)
    print(json.dumps(output, ensure_ascii=False, indent=2))
