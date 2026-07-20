from __future__ import annotations

import logging
from typing import Any

import requests

from campus_mate.config import Settings
from campus_mate.models import Opportunity, OpportunityStatus, ParseCandidate, SourcePage
from campus_mate.parsing.html import HtmlOpportunityParser
from campus_mate.parsing.ocr import OcrOpportunityParser
from campus_mate.parsing.vision import PosterVisionParser
from campus_mate.utils import build_retry_session, compact_text, now_in_timezone, parse_date

LOGGER = logging.getLogger(__name__)


class MultiPassParser:
    REQUIRED_FOR_CONFIDENCE = ("title", "deadline", "organization", "eligibility")

    def __init__(
        self,
        settings: Settings,
        *,
        html_parser: HtmlOpportunityParser | None = None,
        ocr_parser: OcrOpportunityParser | None = None,
        vision_parser: PosterVisionParser | None = None,
        session: requests.Session | None = None,
    ):
        self.settings = settings
        self.html_parser = html_parser or HtmlOpportunityParser()
        self.ocr_parser = ocr_parser or OcrOpportunityParser(settings)
        self.vision_parser = vision_parser or PosterVisionParser(settings)
        self.session = session or build_retry_session(settings.max_retries)

    def parse(self, page: SourcePage, *, force_all_passes: bool = False) -> Opportunity:
        candidates: list[ParseCandidate] = [self.html_parser.parse(page)]
        poster_url = self._best_value(candidates, "poster_url") or page.poster_url
        poster_bytes: bytes | None = None
        poster_mime = "image/jpeg"

        if poster_url and (force_all_passes or self._needs_enrichment(candidates)):
            poster_bytes, poster_mime = self._download_image(str(poster_url))
            if poster_bytes and self.settings.enable_ocr:
                candidates.append(self.ocr_parser.extract_image(poster_bytes))

        if force_all_passes or self._needs_enrichment(candidates):
            if self.settings.enable_ocr and not poster_bytes:
                rendered_candidate, screenshot = self.ocr_parser.extract_rendered_page(page.url)
                candidates.append(rendered_candidate)
                if screenshot and not poster_bytes:
                    poster_bytes, poster_mime = screenshot, "image/png"

        if (
            poster_bytes
            and self.settings.enable_vision
            and (force_all_passes or self._needs_enrichment(candidates))
        ):
            candidates.append(self.vision_parser.extract(poster_bytes, mime_type=poster_mime))

        values, evidence, warnings = self._merge(candidates)
        title = compact_text(str(values.get("title") or ""), 300)
        if not title:
            title = "제목 확인 필요"
            warnings.append("missing_title")
        deadline = parse_date(values.get("deadline"))
        if not deadline:
            warnings.append("missing_deadline")
        confidence = self._confidence(values, evidence)
        status = (
            OpportunityStatus.NEEDS_REVIEW
            if title == "제목 확인 필요" or not deadline or confidence < 0.50
            else OpportunityStatus.NEW
        )
        return Opportunity(
            source=page.source,
            source_url=page.url,
            title=title,
            organization=str(values.get("organization") or ""),
            opportunity_type=str(values.get("opportunity_type") or "공모전"),
            summary=str(values.get("summary") or ""),
            eligibility=str(values.get("eligibility") or ""),
            submission=str(values.get("submission") or ""),
            benefits=str(values.get("benefits") or ""),
            recruit_start_date=parse_date(values.get("recruit_start_date")),
            deadline=deadline,
            event_date=parse_date(values.get("event_date")),
            poster_url=str(values.get("poster_url") or poster_url or "") or None,
            parse_confidence=confidence,
            parse_evidence=evidence,
            parse_warnings=sorted(set(warnings)),
            status=status,
            last_collected_at=now_in_timezone(self.settings.timezone),
        )

    def _download_image(self, url: str) -> tuple[bytes | None, str]:
        try:
            response = self.session.get(url, timeout=self.settings.request_timeout)
            if response.status_code >= 400:
                return None, "image/jpeg"
            mime = response.headers.get("Content-Type", "image/jpeg").split(";", 1)[0]
            return response.content, mime
        except requests.RequestException as exc:
            LOGGER.warning("Poster download failed: %s", exc)
            return None, "image/jpeg"

    def _needs_enrichment(self, candidates: list[ParseCandidate]) -> bool:
        values, _, _ = self._merge(candidates)
        return any(not values.get(field) for field in self.REQUIRED_FOR_CONFIDENCE)

    def _best_value(self, candidates: list[ParseCandidate], field: str) -> Any:
        best: tuple[float, Any] | None = None
        for candidate in candidates:
            value = candidate.values.get(field)
            if value in (None, "", [], {}):
                continue
            confidence = max(
                (item.confidence for item in candidate.evidence.get(field, [])), default=0.0
            )
            if best is None or confidence > best[0]:
                best = (confidence, value)
        return best[1] if best else None

    def _merge(
        self, candidates: list[ParseCandidate]
    ) -> tuple[dict[str, Any], dict[str, list[Any]], list[str]]:
        fields: set[str] = set()
        warnings: list[str] = []
        for candidate in candidates:
            fields.update(candidate.values)
            warnings.extend(candidate.warnings)
        values: dict[str, Any] = {}
        evidence: dict[str, list[Any]] = {}
        for field in fields:
            best: tuple[float, Any] | None = None
            all_evidence = []
            for candidate in candidates:
                all_evidence.extend(candidate.evidence.get(field, []))
                value = candidate.values.get(field)
                if value in (None, "", [], {}):
                    continue
                confidence = max(
                    (item.confidence for item in candidate.evidence.get(field, [])), default=0.0
                )
                if best is None or confidence > best[0]:
                    best = (confidence, value)
            if best is not None:
                values[field] = best[1]
            if all_evidence:
                evidence[field] = sorted(all_evidence, key=lambda item: item.confidence, reverse=True)
        self._validate_dates(values, warnings)
        return values, evidence, warnings

    def _validate_dates(self, values: dict[str, Any], warnings: list[str]) -> None:
        start = parse_date(values.get("recruit_start_date"))
        deadline = parse_date(values.get("deadline"))
        event = parse_date(values.get("event_date"))
        if start and deadline and deadline < start:
            warnings.append("deadline_before_start")
        if deadline and deadline.year < 2000:
            warnings.append("implausible_deadline")
        if event and event.year < 2000:
            warnings.append("implausible_event_date")

    def _confidence(self, values: dict[str, Any], evidence: dict[str, list[Any]]) -> float:
        weights = {"title": 0.35, "deadline": 0.30, "organization": 0.15, "eligibility": 0.10, "poster_url": 0.10}
        score = 0.0
        for field, weight in weights.items():
            if not values.get(field):
                continue
            score += weight * max((item.confidence for item in evidence.get(field, [])), default=0.35)
        return round(max(0.0, min(score, 1.0)), 3)
