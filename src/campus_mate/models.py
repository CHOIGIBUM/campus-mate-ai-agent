from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator

from .utils import compact_text, normalize_url, stable_identifier


class OpportunityStatus(StrEnum):
    NEW = "New"
    RECOMMENDED = "Recommended"
    ACCEPT = "Accept"
    SCHEDULING = "Scheduling"
    SCHEDULED = "Scheduled"
    HOLD = "Hold"
    REJECT = "Reject"
    NEEDS_REVIEW = "NeedsReview"
    CALENDAR_ERROR = "CalendarError"


class Priority(StrEnum):
    URGENT = "긴급"
    IMPORTANT = "중요"
    REFERENCE = "참고"


class ConflictStatus(StrEnum):
    UNKNOWN = "미확인"
    NONE = "없음"
    EXISTS = "있음"


class FieldEvidence(BaseModel):
    source: Literal["html", "jsonld", "next_data", "ocr", "vision", "manual", "fallback"]
    confidence: float = Field(ge=0.0, le=1.0)
    raw_excerpt: str = ""

    @field_validator("raw_excerpt")
    @classmethod
    def trim_excerpt(cls, value: str) -> str:
        return compact_text(value, 500)


class ParseCandidate(BaseModel):
    values: dict[str, Any] = Field(default_factory=dict)
    evidence: dict[str, list[FieldEvidence]] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)

    def add(
        self,
        field_name: str,
        value: Any,
        *,
        source: Literal["html", "jsonld", "next_data", "ocr", "vision", "manual", "fallback"],
        confidence: float,
        raw_excerpt: str = "",
    ) -> None:
        if value in (None, "", [], {}):
            return
        existing = self.evidence.get(field_name, [])
        current_best = max((item.confidence for item in existing), default=-1.0)
        if confidence >= current_best:
            self.values[field_name] = value
        self.evidence.setdefault(field_name, []).append(
            FieldEvidence(
                source=source,
                confidence=confidence,
                raw_excerpt=raw_excerpt,
            )
        )


class UserProfile(BaseModel):
    name: str = ""
    school: str
    grade: str
    major: str
    interests: list[str] = Field(min_length=1)
    activity_types: list[str] = Field(default_factory=lambda: ["공모전", "해커톤"])
    career_goal: str = ""
    keywords: list[str] = Field(default_factory=list)
    preferred_regions: list[str] = Field(default_factory=list)
    available_times: list[str] = Field(default_factory=list)

    @field_validator(
        "interests", "activity_types", "keywords", "preferred_regions", "available_times", mode="before"
    )
    @classmethod
    def coerce_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            value = [piece.strip() for piece in value.split(",")]
        if not isinstance(value, list):
            raise TypeError("Expected a list or comma-separated string")
        seen: set[str] = set()
        result: list[str] = []
        for item in value:
            text = compact_text(str(item), 120)
            if text and text.lower() not in seen:
                seen.add(text.lower())
                result.append(text)
        return result

    @field_validator("school", "grade", "major")
    @classmethod
    def required_text(cls, value: str) -> str:
        value = compact_text(value, 120)
        if not value:
            raise ValueError("This profile field is required")
        return value

    @computed_field
    @property
    def search_terms(self) -> list[str]:
        values = [self.major, self.career_goal, *self.interests, *self.keywords]
        terms: list[str] = []
        for value in values:
            for token in value.replace("·", " ").replace("/", " ").replace("-", " ").split():
                token = token.strip().lower()
                if len(token) >= 2 and token not in terms:
                    terms.append(token)
        return terms


class SourcePage(BaseModel):
    source: str
    url: str
    html: str
    fetched_at: datetime
    poster_url: str | None = None


class Opportunity(BaseModel):
    opportunity_id: str = ""
    source: str
    source_url: str
    title: str
    organization: str = ""
    opportunity_type: str = "공모전"
    summary: str = ""
    eligibility: str = ""
    submission: str = ""
    benefits: str = ""
    recruit_start_date: date | None = None
    deadline: date | None = None
    event_date: date | None = None
    poster_url: str | None = None

    parse_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    parse_evidence: dict[str, list[FieldEvidence]] = Field(default_factory=dict)
    parse_warnings: list[str] = Field(default_factory=list)

    fit_score: int | None = Field(default=None, ge=0, le=100)
    priority: Priority | None = None
    recommendation_reasons: list[str] = Field(default_factory=list)

    status: OpportunityStatus = OpportunityStatus.NEW
    conflict_status: ConflictStatus = ConflictStatus.UNKNOWN
    notion_page_id: str | None = None
    calendar_event_ids: dict[str, str] = Field(default_factory=dict)
    sync_error: str = ""
    last_collected_at: datetime | None = None

    @model_validator(mode="after")
    def normalize(self) -> Opportunity:
        self.source_url = normalize_url(self.source_url)
        self.title = compact_text(self.title, 300)
        self.organization = compact_text(self.organization, 300)
        self.opportunity_type = compact_text(self.opportunity_type, 100) or "공모전"
        self.summary = compact_text(self.summary, 1900)
        self.eligibility = compact_text(self.eligibility, 1900)
        self.submission = compact_text(self.submission, 1900)
        self.benefits = compact_text(self.benefits, 1900)
        self.sync_error = compact_text(self.sync_error, 1900)
        if not self.opportunity_id:
            self.opportunity_id = stable_identifier(self.source, self.source_url)
        if self.deadline and self.recruit_start_date and self.deadline < self.recruit_start_date:
            self.parse_warnings.append("deadline_before_recruit_start")
        return self

    @property
    def searchable_text(self) -> str:
        return " ".join(
            filter(
                None,
                [
                    self.title,
                    self.organization,
                    self.opportunity_type,
                    self.summary,
                    self.eligibility,
                    self.submission,
                    self.benefits,
                ],
            )
        ).lower()


class Recommendation(BaseModel):
    score: int = Field(ge=0, le=100)
    priority: Priority
    reasons: list[str]
    breakdown: dict[str, int]
    days_until_deadline: int | None = None


class CalendarEventRequest(BaseModel):
    request_id: str
    opportunity_id: str
    notion_page_id: str | None = None
    kind: Literal["deadline", "preparation", "event"]
    summary: str
    start_datetime: datetime
    duration_minutes: int = Field(default=60, ge=1, le=1440)
    timezone: str = "Asia/Seoul"
    description: str = ""
    calendar_id: str = "primary"
    idempotency_key: str


class CalendarEventResult(BaseModel):
    request_id: str
    success: bool
    event_id: str | None = None
    error: str = ""
    raw: dict[str, Any] = Field(default_factory=dict)


class CollectionItemResult(BaseModel):
    url: str
    success: bool
    opportunity_id: str | None = None
    title: str = ""
    error: str = ""


class CollectionReport(BaseModel):
    started_at: datetime
    finished_at: datetime
    source: str
    requested_limit: int
    discovered: int
    stored: int
    needs_review: int
    failures: int
    items: list[CollectionItemResult]


class BriefingReport(BaseModel):
    generated_at: datetime
    recommended_count: int
    urgent_count: int
    conflict_count: int
    delivered: bool
    destination: str
    artifact_path: str | None = None
