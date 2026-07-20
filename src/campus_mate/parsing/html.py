from __future__ import annotations

import json
import re
from collections.abc import Iterable
from typing import Any

from bs4 import BeautifulSoup

from campus_mate.models import ParseCandidate, SourcePage
from campus_mate.utils import compact_text, parse_date


class HtmlOpportunityParser:
    """Extract a notice from semantic HTML, JSON-LD, and Linkareer Next.js state."""

    def parse(self, page: SourcePage) -> ParseCandidate:
        soup = BeautifulSoup(page.html, "html.parser")
        candidate = ParseCandidate()
        self._parse_meta(soup, candidate)
        self._parse_jsonld(soup, candidate)
        self._parse_next_data(soup, candidate)
        self._parse_visible_text(soup, candidate)
        if page.poster_url:
            candidate.add("poster_url", page.poster_url, source="html", confidence=0.98)
        return candidate

    def _parse_meta(self, soup: BeautifulSoup, candidate: ParseCandidate) -> None:
        title = self._meta(soup, "property", "og:title") or self._meta(soup, "name", "title")
        if not title:
            heading = soup.find("h1")
            title = heading.get_text(" ", strip=True) if heading else ""
        description = self._meta(soup, "property", "og:description") or self._meta(
            soup, "name", "description"
        )
        image = self._meta(soup, "property", "og:image")
        candidate.add("title", self._clean_title(title), source="html", confidence=0.82, raw_excerpt=title)
        candidate.add("summary", description, source="html", confidence=0.70, raw_excerpt=description)
        candidate.add("poster_url", image, source="html", confidence=0.98)

    def _parse_jsonld(self, soup: BeautifulSoup, candidate: ParseCandidate) -> None:
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            raw = script.string or script.get_text()
            try:
                payload = json.loads(raw)
            except (TypeError, json.JSONDecodeError):
                continue
            for item in self._flatten_jsonld(payload):
                kind = str(item.get("@type", "")).lower()
                if kind not in {"event", "educationevent", "jobposting", "creativework"}:
                    continue
                candidate.add(
                    "title", item.get("name") or item.get("headline"), source="jsonld", confidence=0.92
                )
                candidate.add(
                    "summary", item.get("description"), source="jsonld", confidence=0.82
                )
                candidate.add(
                    "recruit_start_date",
                    parse_date(item.get("validFrom") or item.get("startDate")),
                    source="jsonld",
                    confidence=0.87,
                )
                candidate.add(
                    "deadline",
                    parse_date(item.get("validThrough") or item.get("endDate")),
                    source="jsonld",
                    confidence=0.87,
                )
                candidate.add(
                    "event_date",
                    parse_date(item.get("startDate")),
                    source="jsonld",
                    confidence=0.78,
                )
                organization = item.get("hiringOrganization") or item.get("organizer")
                if isinstance(organization, dict):
                    organization = organization.get("name")
                candidate.add("organization", organization, source="jsonld", confidence=0.85)
                image = item.get("image")
                if isinstance(image, list):
                    image = image[0] if image else None
                if isinstance(image, dict):
                    image = image.get("url")
                candidate.add("poster_url", image, source="jsonld", confidence=0.90)

    def _parse_next_data(self, soup: BeautifulSoup, candidate: ParseCandidate) -> None:
        script = soup.find("script", id="__NEXT_DATA__")
        if not script:
            return
        try:
            payload = json.loads(script.string or script.get_text())
        except json.JSONDecodeError:
            candidate.warnings.append("invalid_next_data")
            return
        apollo = (
            payload.get("props", {})
            .get("pageProps", {})
            .get("__APOLLO_STATE__", {})
        )
        if not isinstance(apollo, dict):
            apollo = {}
        selected = self._select_notice_object(payload, apollo)
        if not selected:
            return

        resolve = lambda value: self._resolve_apollo(value, apollo)  # noqa: E731
        candidate.add("title", selected.get("title") or selected.get("name"), source="next_data", confidence=0.97)
        candidate.add(
            "organization",
            selected.get("organizationName") or self._name(selected.get("organizer"), resolve),
            source="next_data",
            confidence=0.96,
        )
        candidate.add(
            "recruit_start_date",
            parse_date(selected.get("recruitStartAt") or selected.get("startAt")),
            source="next_data",
            confidence=0.98,
        )
        candidate.add(
            "deadline",
            parse_date(selected.get("recruitCloseAt") or selected.get("endAt")),
            source="next_data",
            confidence=0.98,
        )
        candidate.add(
            "event_date",
            parse_date(selected.get("activityStartAt") or selected.get("eventStartAt")),
            source="next_data",
            confidence=0.90,
        )
        targets = [self._name(item, resolve) for item in selected.get("targets", []) or []]
        candidate.add(
            "eligibility",
            ", ".join(filter(None, targets)),
            source="next_data",
            confidence=0.94,
        )
        benefits = [self._name(item, resolve) for item in selected.get("benefits", []) or []]
        reward = selected.get("tenThousandUnitOfReward")
        benefit_parts: list[str] = []
        if reward not in (None, "", 0):
            try:
                benefit_parts.append(f"총 상금 {int(reward):,}만원")
            except (TypeError, ValueError):
                benefit_parts.append(str(reward))
        benefit_parts.extend(filter(None, benefits))
        candidate.add(
            "benefits", " / ".join(benefit_parts), source="next_data", confidence=0.93
        )
        apply_types = [self._name(item, resolve) for item in selected.get("applyTypes", []) or []]
        categories = [self._name(item, resolve) for item in selected.get("categories", []) or []]
        submission_parts: list[str] = []
        if apply_types:
            submission_parts.append("지원방식: " + ", ".join(filter(None, apply_types)))
        if categories:
            submission_parts.append("분야: " + ", ".join(filter(None, categories)))
        candidate.add(
            "submission", " / ".join(submission_parts), source="next_data", confidence=0.88
        )
        candidate.add(
            "summary",
            selected.get("shortDescription") or selected.get("description"),
            source="next_data",
            confidence=0.86,
        )
        image = selected.get("imageUrl") or selected.get("thumbnailUrl") or selected.get("posterUrl")
        candidate.add("poster_url", image, source="next_data", confidence=0.95)

    def _parse_visible_text(self, soup: BeautifulSoup, candidate: ParseCandidate) -> None:
        text = compact_text(soup.get_text("\n", strip=True), 20000)
        label_patterns = {
            "organization": [r"(?:주최|주관|기관)\s*[:：]\s*([^\n|]{2,100})"],
            "eligibility": [r"(?:참가\s*자격|지원\s*자격|대상)\s*[:：]\s*([^\n]{2,300})"],
            "submission": [r"(?:제출물|제출\s*서류|지원\s*방법)\s*[:：]\s*([^\n]{2,300})"],
            "benefits": [r"(?:시상|혜택|상금)\s*[:：]\s*([^\n]{2,300})"],
        }
        for field, patterns in label_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    candidate.add(
                        field,
                        match.group(1),
                        source="html",
                        confidence=0.58,
                        raw_excerpt=match.group(0),
                    )
                    break
        for field, labels in {
            "deadline": ("접수 마감", "모집 마감", "마감일", "신청 마감"),
            "recruit_start_date": ("접수 시작", "모집 시작", "신청 시작"),
            "event_date": ("행사일", "대회일", "발표일", "본선일"),
        }.items():
            value, excerpt = self._find_labeled_date(text, labels)
            candidate.add(field, value, source="html", confidence=0.62, raw_excerpt=excerpt)

    def _find_labeled_date(self, text: str, labels: tuple[str, ...]) -> tuple[Any, str]:
        label = "|".join(re.escape(item) for item in labels)
        patterns = [
            rf"(?:{label})\s*[:：]?\s*((?:20\d{{2}}[./-])?\d{{1,2}}[./-]\d{{1,2}})",
            rf"(?:{label})\s*[:：]?\s*((?:20\d{{2}}년\s*)?\d{{1,2}}월\s*\d{{1,2}}일)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return parse_date(match.group(1)), match.group(0)
        return None, ""

    def _select_notice_object(self, payload: dict[str, Any], apollo: dict[str, Any]) -> dict[str, Any] | None:
        candidates = []
        for item in self._walk(payload):
            if not isinstance(item, dict):
                continue
            score = sum(
                key in item
                for key in (
                    "recruitCloseAt",
                    "recruitStartAt",
                    "organizationName",
                    "targets",
                    "benefits",
                    "applyTypes",
                    "categories",
                )
            )
            if score >= 2:
                candidates.append((score, item))
        for item in apollo.values():
            if isinstance(item, dict):
                score = sum(
                    key in item
                    for key in (
                        "recruitCloseAt",
                        "recruitStartAt",
                        "organizationName",
                        "targets",
                        "benefits",
                        "applyTypes",
                        "categories",
                    )
                )
                if score >= 2:
                    candidates.append((score + 1, item))
        return max(candidates, key=lambda pair: pair[0])[1] if candidates else None

    def _walk(self, value: Any) -> Iterable[Any]:
        yield value
        if isinstance(value, dict):
            for child in value.values():
                yield from self._walk(child)
        elif isinstance(value, list):
            for child in value:
                yield from self._walk(child)

    def _resolve_apollo(self, value: Any, apollo: dict[str, Any]) -> Any:
        if isinstance(value, dict) and "__ref" in value:
            return apollo.get(value["__ref"], {})
        return value or {}

    def _name(self, value: Any, resolver: Any) -> str:
        resolved = resolver(value)
        if isinstance(resolved, str):
            return resolved
        if isinstance(resolved, dict):
            return str(resolved.get("name") or resolved.get("title") or "")
        return ""

    def _flatten_jsonld(self, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, dict):
            graph = payload.get("@graph")
            if isinstance(graph, list):
                return [item for item in graph if isinstance(item, dict)]
            return [payload]
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        return []

    def _meta(self, soup: BeautifulSoup, attribute: str, value: str) -> str:
        node = soup.find("meta", attrs={attribute: value})
        return str(node.get("content", "")).strip() if node else ""

    def _clean_title(self, title: str) -> str:
        return re.sub(r"\s*[-|]\s*링커리어.*$", "", compact_text(title, 300), flags=re.IGNORECASE)
