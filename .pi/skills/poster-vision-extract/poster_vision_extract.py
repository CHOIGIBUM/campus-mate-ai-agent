"""poster-vision-extract Skill.

MVP implementation: parse supplied poster_text if a vision/OCR service has
already produced it, otherwise return skipped with an explicit reason.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Tuple

KST = timezone(timedelta(hours=9))


class PosterVisionExtractSkill:
    def execute(self, input_data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        text = input_data.get("poster_text") or input_data.get("vision_text") or ""
        if not text:
            return True, "포스터 Vision 입력 없음: skipped", {
                "parse_method": "poster_vision",
                "status": "skipped",
                "reason": "Vision engine/text not provided",
                "source_url": input_data.get("opportunity_url") or input_data.get("source_url"),
                "image_urls": input_data.get("image_urls", []),
                "extracted_fields": {},
                "parsed_at": datetime.now(KST).isoformat(timespec="seconds"),
            }
        fields = {
            "organizer": self._line_field(text, "주최|주관|운영"),
            "submission_deadline": self._deadline(text),
            "award": self._line_field(text, "시상|상금|혜택"),
            "contact": self._line_field(text, "문의|연락처|이메일"),
        }
        return True, "포스터 텍스트 파싱 완료", {
            "parse_method": "poster_vision",
            "status": "success",
            "source_url": input_data.get("opportunity_url") or input_data.get("source_url"),
            "image_urls": input_data.get("image_urls", []),
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
            "confidence": 68,
        }

    def _line_field(self, text: str, label_pattern: str) -> Dict[str, Any]:
        match = re.search(rf"(?:{label_pattern})\s*[:：]\s*([^\n\r]{{2,100}})", text)
        if not match:
            return {"value": "확인 필요", "evidence": "", "confidence": 0}
        return {"value": match.group(1).strip(), "evidence": match.group(0), "confidence": 64}


if __name__ == "__main__":
    import sys

    stdin_text = sys.stdin.read()
    payload = json.loads(stdin_text) if stdin_text.strip() else {}
    ok, message, output = PosterVisionExtractSkill().execute(payload)
    print(message)
    print(json.dumps(output, ensure_ascii=False, indent=2))
