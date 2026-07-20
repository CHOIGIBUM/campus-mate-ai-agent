from __future__ import annotations

import io
import logging
import re
from typing import Any

from campus_mate.config import Settings
from campus_mate.models import ParseCandidate
from campus_mate.utils import compact_text, parse_date

LOGGER = logging.getLogger(__name__)


class OcrOpportunityParser:
    """Rendered-page and poster OCR pass.

    Playwright and Tesseract are optional dependencies. Missing system language packs are
    reported as warnings instead of aborting the whole collection run.
    """

    def __init__(self, settings: Settings):
        self.settings = settings

    def extract_rendered_page(self, url: str) -> tuple[ParseCandidate, bytes | None]:
        candidate = ParseCandidate()
        if not self.settings.enable_ocr:
            return candidate, None
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            candidate.warnings.append("playwright_not_installed")
            return candidate, None
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 1440, "height": 1000})
                page.goto(url, wait_until="networkidle", timeout=int(self.settings.request_timeout * 1000))
                screenshot = page.screenshot(full_page=True)
                browser.close()
            text = self.image_to_text(screenshot)
            return self.parse_text(text), screenshot
        except Exception as exc:  # browser/runtime-specific failures should not kill the run
            LOGGER.warning("Rendered OCR failed for %s: %s", url, exc)
            candidate.warnings.append(f"rendered_ocr_failed:{type(exc).__name__}")
            return candidate, None

    def extract_image(self, image_bytes: bytes) -> ParseCandidate:
        if not self.settings.enable_ocr:
            return ParseCandidate()
        try:
            return self.parse_text(self.image_to_text(image_bytes))
        except Exception as exc:
            LOGGER.warning("Image OCR failed: %s", exc)
            return ParseCandidate(warnings=[f"image_ocr_failed:{type(exc).__name__}"])

    def image_to_text(self, image_bytes: bytes) -> str:
        try:
            import pytesseract
            from PIL import Image, ImageEnhance, ImageOps
        except ImportError as exc:
            raise RuntimeError("Install the 'ocr' optional dependencies") from exc
        if self.settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.settings.tesseract_cmd
        image = Image.open(io.BytesIO(image_bytes)).convert("L")
        image = ImageOps.autocontrast(image)
        image = ImageEnhance.Contrast(image).enhance(1.35)
        return pytesseract.image_to_string(image, lang=self.settings.ocr_languages)

    def parse_text(self, text: str) -> ParseCandidate:
        candidate = ParseCandidate()
        normalized = self._normalize(text)
        if not normalized:
            candidate.warnings.append("empty_ocr_text")
            return candidate

        title = self._title_candidate(normalized)
        candidate.add("title", title, source="ocr", confidence=0.58, raw_excerpt=title)
        for field, labels in {
            "organization": ("주최", "주관", "기관", "운영"),
            "eligibility": ("참가 자격", "지원 자격", "응모 자격", "대상"),
            "submission": ("제출물", "제출 서류", "지원 방법", "접수 방법"),
            "benefits": ("시상", "혜택", "상금", "수상 혜택"),
        }.items():
            value, excerpt = self._find_labeled_text(normalized, labels)
            candidate.add(field, value, source="ocr", confidence=0.55, raw_excerpt=excerpt)

        for field, labels in {
            "recruit_start_date": ("접수 시작", "모집 시작", "신청 시작"),
            "deadline": ("접수 마감", "모집 마감", "신청 마감", "마감일", "접수 기간"),
            "event_date": ("행사일", "대회일", "본선", "발표일", "시상식"),
        }.items():
            value, excerpt = self._find_labeled_date(normalized, labels, prefer_last=field == "deadline")
            candidate.add(field, value, source="ocr", confidence=0.62, raw_excerpt=excerpt)

        candidate.add(
            "summary",
            compact_text(normalized, 1200),
            source="ocr",
            confidence=0.38,
            raw_excerpt=normalized[:500],
        )
        return candidate

    def _normalize(self, text: str) -> str:
        lines = [compact_text(line, 1000) for line in text.replace("\r", "\n").split("\n")]
        return "\n".join(line for line in lines if line)

    def _title_candidate(self, text: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        blocked = ("접수", "기간", "주최", "주관", "참가", "지원", "대상", "시상", "문의", "홈페이지")
        candidates = [
            line
            for line in lines[:15]
            if 4 <= len(line) <= 120 and not any(line.startswith(token) for token in blocked)
        ]
        if not candidates:
            return ""
        return max(candidates, key=lambda value: (len(re.findall(r"[가-힣A-Za-z]", value)), len(value)))

    def _find_labeled_text(self, text: str, labels: tuple[str, ...]) -> tuple[str, str]:
        label_pattern = "|".join(re.escape(item) for item in labels)
        pattern = rf"(?:{label_pattern})\s*[:：]?\s*([^\n]{{2,300}})"
        match = re.search(pattern, text, re.IGNORECASE)
        return (compact_text(match.group(1), 500), match.group(0)) if match else ("", "")

    def _find_labeled_date(
        self, text: str, labels: tuple[str, ...], *, prefer_last: bool = False
    ) -> tuple[Any, str]:
        label_pattern = "|".join(re.escape(item) for item in labels)
        window_pattern = rf"(?:{label_pattern})[^\n]{{0,160}}"
        for window in re.findall(window_pattern, text, re.IGNORECASE):
            dates = self._dates_in(window)
            if dates:
                return (dates[-1] if prefer_last else dates[0]), window
        return None, ""

    def _dates_in(self, text: str) -> list[Any]:
        patterns = [
            r"20\d{2}[./-]\d{1,2}[./-]\d{1,2}",
            r"20\d{2}년\s*\d{1,2}월\s*\d{1,2}일",
            r"\d{1,2}월\s*\d{1,2}일",
        ]
        values: list[Any] = []
        for pattern in patterns:
            for raw in re.findall(pattern, text):
                parsed = parse_date(raw)
                if parsed and parsed not in values:
                    values.append(parsed)
        return values
