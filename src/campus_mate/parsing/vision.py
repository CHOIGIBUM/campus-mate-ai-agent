from __future__ import annotations

import base64
import json
import logging
import re
from typing import Any

from campus_mate.config import Settings
from campus_mate.models import ParseCandidate
from campus_mate.utils import compact_text, parse_date

LOGGER = logging.getLogger(__name__)


class PosterVisionParser:
    """Optional poster-image extraction through an OpenAI-compatible vision endpoint."""

    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def available(self) -> bool:
        return bool(
            self.settings.enable_vision
            and self.settings.vision_api_key
            and self.settings.vision_model
        )

    def extract(self, image_bytes: bytes, *, mime_type: str = "image/jpeg") -> ParseCandidate:
        if not self.available:
            return ParseCandidate(warnings=["vision_not_configured"])
        try:
            from openai import OpenAI
        except ImportError:
            return ParseCandidate(warnings=["openai_not_installed"])

        assert self.settings.vision_api_key is not None
        assert self.settings.vision_model is not None
        client = OpenAI(
            api_key=self.settings.vision_api_key.get_secret_value(),
            base_url=self.settings.vision_base_url,
            timeout=self.settings.request_timeout,
        )
        encoded = base64.b64encode(image_bytes).decode("ascii")
        prompt = """
이 이미지는 대학생 대상 공모전·해커톤·대외활동 포스터입니다.
보이는 정보만 사용해 아래 JSON 객체를 반환하세요. 추정하거나 없는 내용을 만들지 마세요.
날짜는 YYYY-MM-DD 형식으로 정규화하고, 확인되지 않으면 null 또는 빈 문자열로 두세요.

{
  "title": "",
  "organization": "",
  "opportunity_type": "공모전|해커톤|대외활동|교육|기타",
  "summary": "",
  "eligibility": "",
  "submission": "",
  "benefits": "",
  "recruit_start_date": null,
  "deadline": null,
  "event_date": null,
  "confidence": 0.0
}

설명 문장이나 Markdown 없이 JSON만 출력하세요.
""".strip()
        try:
            response = client.chat.completions.create(
                model=self.settings.vision_model,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{mime_type};base64,{encoded}"},
                            },
                        ],
                    }
                ],
            )
            content = response.choices[0].message.content or ""
            payload = self._parse_json(content)
        except Exception as exc:
            LOGGER.warning("Poster vision extraction failed: %s", exc)
            return ParseCandidate(warnings=[f"vision_failed:{type(exc).__name__}"])
        confidence = self._confidence(payload.get("confidence"))
        candidate = ParseCandidate()
        for field in (
            "title",
            "organization",
            "opportunity_type",
            "summary",
            "eligibility",
            "submission",
            "benefits",
        ):
            candidate.add(
                field,
                compact_text(str(payload.get(field) or ""), 1900),
                source="vision",
                confidence=confidence,
            )
        for field in ("recruit_start_date", "deadline", "event_date"):
            candidate.add(
                field,
                parse_date(payload.get(field)),
                source="vision",
                confidence=confidence,
            )
        return candidate

    def _parse_json(self, content: str) -> dict[str, Any]:
        stripped = content.strip()
        if stripped.startswith("```"):
            stripped = re.sub(r"^```(?:json)?\s*|\s*```$", "", stripped, flags=re.IGNORECASE)
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", stripped, re.DOTALL)
            if not match:
                raise
            payload = json.loads(match.group(0))
        if not isinstance(payload, dict):
            raise ValueError("Vision response is not a JSON object")
        return payload

    def _confidence(self, value: Any) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = 0.72
        return max(0.35, min(number, 0.90))
