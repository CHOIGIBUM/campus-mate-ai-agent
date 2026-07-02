"""html-opportunity-parse Skill."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin
from urllib.request import Request, urlopen

KST = timezone(timedelta(hours=9))


class OpportunityHTMLParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.title_parts: List[str] = []
        self.h1_parts: List[str] = []
        self.body_parts: List[str] = []
        self.image_urls: List[str] = []
        self.meta_description = ""
        self._tag_stack: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        tag = tag.lower()
        self._tag_stack.append(tag)
        attr_map = {k.lower(): v for k, v in attrs if k}
        if tag == "img" and attr_map.get("src"):
            self.image_urls.append(urljoin(self.base_url, attr_map["src"]))
        if tag == "meta":
            name = (attr_map.get("name") or attr_map.get("property") or "").lower()
            if name in {"description", "og:description"} and attr_map.get("content"):
                self.meta_description = attr_map["content"] or ""

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self._tag_stack[::-1]:
            idx = len(self._tag_stack) - 1 - self._tag_stack[::-1].index(tag)
            self._tag_stack = self._tag_stack[:idx]

    def handle_data(self, data: str) -> None:
        text = re.sub(r"\s+", " ", data).strip()
        if not text:
            return
        active = self._tag_stack[-1] if self._tag_stack else ""
        if active == "title":
            self.title_parts.append(text)
        elif active == "h1":
            self.h1_parts.append(text)
        if active not in {"script", "style", "noscript"}:
            self.body_parts.append(text)


class HtmlOpportunityParseSkill:
    """Extract core opportunity fields from an HTML document."""

    FIELD_PATTERNS = {
        "organizer": [r"(?:주최|주관|운영|기관)\s*[:：]\s*([^\n\r|/]{2,60})"],
        "eligibility": [r"(?:참가\s*대상|지원\s*자격|대상)\s*[:：]\s*([^\n\r]{2,100})"],
        "application_method": [r"(?:신청\s*방법|접수\s*방법|지원\s*방법)\s*[:：]\s*([^\n\r]{2,100})"],
        "contact": [r"(?:문의|연락처|이메일)\s*[:：]\s*([^\n\r]{2,100})"],
    }

    CATEGORY_KEYWORDS = {
        "해커톤": ("해커톤", "hackathon"),
        "공모전": ("공모전", "contest", "competition"),
        "대외활동": ("대외활동", "서포터즈", "봉사단"),
        "교육": ("교육", "강좌", "부트캠프", "캠프"),
        "세미나": ("세미나", "컨퍼런스", "conference", "meetup"),
        "장학금": ("장학", "지원금"),
    }

    def execute(self, input_data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        url = input_data.get("opportunity_url") or input_data.get("source_url") or ""
        site_name = input_data.get("site_name") or "unknown"
        html = input_data.get("html")
        if not html:
            if not url:
                return False, "opportunity_url 또는 html이 필요합니다.", self._failed(url, site_name, "missing_input")
            try:
                html = self._fetch_html(url, int(input_data.get("timeout", 20)))
            except Exception as exc:
                return False, f"HTML 다운로드 실패: {exc}", self._failed(url, site_name, str(exc))

        parser = OpportunityHTMLParser(url)
        parser.feed(html)
        body_text = self._normalize_text(" ".join(parser.body_parts))
        title = self._pick_title(parser, input_data, body_text)
        fields = {
            "title": self._field(title, title, 90 if title != "확인 필요" else 0),
            "category": self._field(self._detect_category(body_text, title), title or body_text[:80], 70),
            "summary": self._field(self._summary(parser, body_text), parser.meta_description or body_text[:160], 70),
            "submission_deadline": self._extract_deadline(body_text),
            "organizer": self._regex_field("organizer", body_text),
            "eligibility": self._regex_field("eligibility", body_text),
            "application_method": self._regex_field("application_method", body_text),
            "contact": self._regex_field("contact", body_text),
            "location": self._field(self._detect_location(body_text), body_text[:120], 65),
            "online_offline": self._field("online" if "온라인" in body_text.lower() or "zoom" in body_text.lower() else "offline", body_text[:120], 60),
        }
        status = "success" if fields["title"]["value"] != "확인 필요" else "needs_review"
        result = {
            "parse_method": "html",
            "status": status,
            "source_url": url,
            "site_name": site_name,
            "parsed_at": datetime.now(KST).isoformat(timespec="seconds"),
            "extracted_fields": fields,
            "image_urls": list(dict.fromkeys(parser.image_urls)),
            "raw_text_excerpt": body_text[:1200],
        }
        return True, f"HTML 파싱 완료: {fields['title']['value']}", result

    def _fetch_html(self, url: str, timeout: int) -> str:
        request = Request(url, headers={"User-Agent": "CampusCareerAI/0.1"})
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")

    def _pick_title(self, parser: OpportunityHTMLParser, input_data: Dict[str, Any], body_text: str) -> str:
        for candidate in [input_data.get("title_hint"), " ".join(parser.h1_parts), " ".join(parser.title_parts)]:
            candidate = self._normalize_text(candidate or "")
            if candidate:
                return candidate[:120]
        lines = [part.strip() for part in re.split(r"[.!?\n\r]", body_text) if part.strip()]
        return lines[0][:120] if lines else "확인 필요"

    def _summary(self, parser: OpportunityHTMLParser, body_text: str) -> str:
        summary = self._normalize_text(parser.meta_description) or body_text
        return summary[:300] if summary else "확인 필요"

    def _detect_category(self, body_text: str, title: str) -> str:
        haystack = f"{title} {body_text}".lower()
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(keyword.lower() in haystack for keyword in keywords):
                return category
        return "확인 필요"

    def _detect_location(self, body_text: str) -> str:
        if re.search(r"온라인|zoom|webex|youtube|줌", body_text, re.I):
            return "온라인"
        match = re.search(r"(서울|강원|춘천|원주|부산|대구|대전|광주|인천|경기|제주)[^\s,.;]{0,20}", body_text)
        return match.group(0) if match else "확인 필요"

    def _extract_deadline(self, body_text: str) -> Dict[str, Any]:
        patterns = [
            r"(?:마감|접수\s*기간|신청\s*기간|제출\s*기한)[^\d]{0,20}(\d{4})[.\-/년 ]+(\d{1,2})[.\-/월 ]+(\d{1,2})",
            r"(\d{4})[.\-/년 ]+(\d{1,2})[.\-/월 ]+(\d{1,2})[^\n\r]{0,20}(?:마감|까지|접수)",
            r"(\d{4})[.\-/년 ]+(\d{1,2})[.\-/월 ]+(\d{1,2})",
        ]
        for pattern in patterns:
            match = re.search(pattern, body_text)
            if match:
                year, month, day = [int(v) for v in match.groups()[:3]]
                value = f"{year:04d}-{month:02d}-{day:02d}T23:59:00+09:00"
                return self._field(value, match.group(0), 82)
        return self._field("확인 필요", "", 0)

    def _regex_field(self, field_name: str, body_text: str) -> Dict[str, Any]:
        for pattern in self.FIELD_PATTERNS[field_name]:
            match = re.search(pattern, body_text)
            if match:
                value = self._normalize_text(match.group(1)).strip(" -:：")
                return self._field(value[:140], match.group(0), 72)
        return self._field("확인 필요", "", 0)

    def _field(self, value: str, evidence: str, confidence: int) -> Dict[str, Any]:
        return {
            "value": value or "확인 필요",
            "evidence": self._normalize_text(evidence)[:300],
            "confidence": confidence,
        }

    def _failed(self, url: str, site_name: str, reason: str) -> Dict[str, Any]:
        return {
            "parse_method": "html",
            "status": "failed",
            "source_url": url,
            "site_name": site_name,
            "failure_reason": reason,
            "extracted_fields": {},
        }

    def _normalize_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()


if __name__ == "__main__":
    import sys

    stdin_text = sys.stdin.read()
    payload = {"opportunity_url": sys.argv[1]} if len(sys.argv) > 1 else (json.loads(stdin_text) if stdin_text.strip() else {})
    ok, message, output = HtmlOpportunityParseSkill().execute(payload)
    print(message)
    print(json.dumps(output, ensure_ascii=False, indent=2))
