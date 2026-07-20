from __future__ import annotations

import json
import logging
import mimetypes
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

from campus_mate.config import Settings
from campus_mate.exceptions import ConfigurationError, IntegrationError
from campus_mate.models import (
    ConflictStatus,
    FieldEvidence,
    Opportunity,
    OpportunityStatus,
    Priority,
    Recommendation,
)
from campus_mate.utils import build_retry_session, compact_text, parse_date

LOGGER = logging.getLogger(__name__)


def _status_color(status: OpportunityStatus) -> str:
    return {
        OpportunityStatus.NEW: "gray",
        OpportunityStatus.RECOMMENDED: "blue",
        OpportunityStatus.ACCEPT: "green",
        OpportunityStatus.SCHEDULING: "yellow",
        OpportunityStatus.SCHEDULED: "purple",
        OpportunityStatus.HOLD: "orange",
        OpportunityStatus.REJECT: "red",
        OpportunityStatus.NEEDS_REVIEW: "brown",
        OpportunityStatus.CALENDAR_ERROR: "red",
    }[status]



PROPERTY_ALIASES: dict[str, tuple[str, ...]] = {
    "상태": ("상태(새)",),
    "요약": ("메모",),
}


PROPERTY_SCHEMA: dict[str, dict[str, Any]] = {
    "공모전명": {"title": {}},
    "공고 ID": {"rich_text": {}},
    "원문 링크": {"url": {}},
    "출처": {"select": {"options": []}},
    "유형": {"select": {"options": []}},
    "주최/주관": {"rich_text": {}},
    "모집 시작일": {"date": {}},
    "마감일": {"date": {}},
    "행사일": {"date": {}},
    "참가 자격": {"rich_text": {}},
    "제출물": {"rich_text": {}},
    "시상/혜택": {"rich_text": {}},
    "요약": {"rich_text": {}},
    "포스터": {"files": {}},
    "적합도": {"number": {"format": "number"}},
    "우선순위": {
        "select": {
            "options": [
                {"name": Priority.URGENT.value, "color": "red"},
                {"name": Priority.IMPORTANT.value, "color": "yellow"},
                {"name": Priority.REFERENCE.value, "color": "gray"},
            ]
        }
    },
    "추천 이유": {"rich_text": {}},
    "상태": {
        "select": {
            "options": [
                {"name": status.value, "color": _status_color(status)}
                for status in OpportunityStatus
            ]
        }
    },
    "일정 충돌": {
        "select": {
            "options": [
                {"name": ConflictStatus.UNKNOWN.value, "color": "gray"},
                {"name": ConflictStatus.NONE.value, "color": "green"},
                {"name": ConflictStatus.EXISTS.value, "color": "red"},
            ]
        }
    },
    "파싱 신뢰도": {"number": {"format": "percent"}},
    "파싱 근거": {"rich_text": {}},
    "캘린더 이벤트 ID": {"rich_text": {}},
    "동기화 오류": {"rich_text": {}},
    "마지막 수집시각": {"date": {}},
}


_MANUAL_OR_TERMINAL = {
    OpportunityStatus.ACCEPT,
    OpportunityStatus.SCHEDULING,
    OpportunityStatus.SCHEDULED,
    OpportunityStatus.HOLD,
    OpportunityStatus.REJECT,
    OpportunityStatus.CALENDAR_ERROR,
}


class NotionOpportunityRepository:
    API_ROOT = "https://api.notion.com/v1"

    def __init__(self, settings: Settings, session: requests.Session | None = None):
        settings.require_notion()
        self.settings = settings
        self.session = session or build_retry_session(settings.max_retries)
        self._data_source_id: str | None = settings.notion_data_source_id
        self._schema: dict[str, Any] | None = None

    @property
    def data_source_id(self) -> str:
        if self._data_source_id:
            return self._data_source_id
        if not self.settings.notion_database_id:
            raise ConfigurationError("No Notion data source or database ID is configured.")
        database = self._request("GET", f"/databases/{self.settings.notion_database_id}")
        sources = database.get("data_sources") or []
        if not sources:
            raise ConfigurationError("The configured Notion database has no accessible data source.")
        self._data_source_id = str(sources[0]["id"]).replace("-", "")
        return self._data_source_id

    @property
    def headers(self) -> dict[str, str]:
        token = self.settings.notion_api_key
        assert token is not None
        return {
            "Authorization": f"Bearer {token.get_secret_value()}",
            "Notion-Version": self.settings.notion_version,
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        path_or_url: str,
        *,
        json_body: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        url = path_or_url if path_or_url.startswith("http") else f"{self.API_ROOT}{path_or_url}"
        request_headers = headers or self.headers
        if files:
            request_headers = {key: value for key, value in request_headers.items() if key.lower() != "content-type"}
        response = self.session.request(
            method,
            url,
            headers=request_headers,
            json=json_body if not files else None,
            files=files,
            timeout=self.settings.request_timeout,
        )
        if response.status_code >= 400:
            try:
                detail = response.json()
            except ValueError:
                detail = {"message": response.text[:500]}
            raise IntegrationError(
                f"Notion {method} {url} failed ({response.status_code}): {detail.get('message', detail)}"
            )
        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError as exc:
            raise IntegrationError(f"Notion returned a non-JSON response for {method} {url}") from exc

    def retrieve_schema(self, *, refresh: bool = False) -> dict[str, Any]:
        if self._schema is None or refresh:
            self._schema = self._request("GET", f"/data_sources/{self.data_source_id}")
        return self._schema

    def ensure_schema(self) -> None:
        schema = self.retrieve_schema(refresh=True)
        existing = schema.get("properties") or {}
        missing = {
            name: definition
            for name, definition in PROPERTY_SCHEMA.items()
            if name not in existing
            and not any(alias in existing for alias in PROPERTY_ALIASES.get(name, ()))
        }
        if "공모전명" in missing:
            title_properties = [name for name, prop in existing.items() if prop.get("type") == "title"]
            if title_properties:
                raise ConfigurationError(
                    "The Notion data source already has a title property named "
                    f"{title_properties[0]!r}. Rename it to '공모전명' in Notion before continuing."
                )
        if not missing:
            return
        self._request("PATCH", f"/data_sources/{self.data_source_id}", json_body={"properties": missing})
        self.retrieve_schema(refresh=True)
        LOGGER.info("Added %d missing Notion properties", len(missing))

    def _query(self, body: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        body = dict(body or {})
        body.setdefault("page_size", 100)
        results: list[dict[str, Any]] = []
        while True:
            payload = self._request(
                "POST", f"/data_sources/{self.data_source_id}/query", json_body=body
            )
            results.extend(item for item in payload.get("results", []) if item.get("object") == "page")
            if not payload.get("has_more") or not payload.get("next_cursor"):
                break
            body["start_cursor"] = payload["next_cursor"]
        return results

    def _find_page(self, opportunity_id: str, source_url: str | None = None) -> dict[str, Any] | None:
        pages = self._query(
            {
                "filter": {
                    "property": "공고 ID",
                    "rich_text": {"equals": opportunity_id},
                }
            }
        )
        if pages:
            return pages[0]
        if source_url:
            pages = self._query(
                {
                    "filter": {
                        "property": "원문 링크",
                        "url": {"equals": source_url},
                    }
                }
            )
            if pages:
                return pages[0]
        return None

    def _property_name(self, canonical: str) -> str:
        schema = self.retrieve_schema().get("properties") or {}
        if canonical in schema:
            return canonical
        for alias in PROPERTY_ALIASES.get(canonical, ()):
            if alias in schema:
                return alias
        return canonical

    def _status_payload(self, status: OpportunityStatus) -> dict[str, Any]:
        schema = self.retrieve_schema().get("properties") or {}
        property_schema = schema.get(self._property_name("상태")) or {}
        if property_schema.get("type") == "status":
            return {"status": {"name": status.value}}
        return {"select": {"name": status.value}}

    def _conflict_payload(self, status: ConflictStatus) -> dict[str, Any]:
        return {"select": {"name": status.value}}

    def _text_property(self, value: str) -> dict[str, Any]:
        value = compact_text(value, 1900)
        return {"rich_text": [{"type": "text", "text": {"content": value}}]} if value else {"rich_text": []}

    def _date_property(self, value: Any) -> dict[str, Any]:
        if not value:
            return {"date": None}
        iso = value.isoformat() if hasattr(value, "isoformat") else str(value)
        return {"date": {"start": iso}}

    def _serialize_evidence(self, opportunity: Opportunity) -> str:
        compact = {
            field: [
                {"source": item.source, "confidence": round(item.confidence, 3)}
                for item in evidence[:3]
            ]
            for field, evidence in opportunity.parse_evidence.items()
        }
        return compact_text(json.dumps(compact, ensure_ascii=False, separators=(",", ":")), 1900)

    def _poster_files(self, opportunity: Opportunity, existing_page: dict[str, Any] | None) -> dict[str, Any] | None:
        if not opportunity.poster_url:
            return None
        if existing_page:
            existing_files = (existing_page.get("properties", {}).get("포스터", {}).get("files") or [])
            if existing_files:
                return None
        if self.settings.notion_upload_posters:
            try:
                upload_id = self._upload_url(opportunity.poster_url)
                if upload_id:
                    return {
                        "files": [
                            {
                                "name": Path(urlparse(opportunity.poster_url).path).name or "poster.jpg",
                                "type": "file_upload",
                                "file_upload": {"id": upload_id},
                            }
                        ]
                    }
            except IntegrationError as exc:
                LOGGER.warning("Notion poster upload failed; falling back to external URL: %s", exc)
        return {
            "files": [
                {
                    "name": Path(urlparse(opportunity.poster_url).path).name or "poster",
                    "type": "external",
                    "external": {"url": opportunity.poster_url},
                }
            ]
        }

    def _upload_url(self, url: str) -> str | None:
        response = self.session.get(url, timeout=self.settings.request_timeout)
        if response.status_code >= 400:
            raise IntegrationError(f"Poster download failed ({response.status_code}): {url}")
        content_type = response.headers.get("Content-Type", "").split(";", 1)[0]
        if not content_type or content_type == "application/octet-stream":
            content_type = mimetypes.guess_type(url)[0] or "image/jpeg"
        filename = Path(urlparse(url).path).name or "poster.jpg"
        created = self._request(
            "POST",
            "/file_uploads",
            json_body={"mode": "single_part", "filename": filename, "content_type": content_type},
        )
        upload_id = created.get("id")
        upload_url = created.get("upload_url") or (
            f"{self.API_ROOT}/file_uploads/{upload_id}/send" if upload_id else None
        )
        if not upload_id or not upload_url:
            raise IntegrationError("Notion did not return a file upload ID and URL")
        self._request(
            "POST",
            upload_url,
            files={"file": (filename, response.content, content_type)},
            headers=self.headers,
        )
        return str(upload_id)

    def _properties_for(self, opportunity: Opportunity, *, include_status: bool) -> dict[str, Any]:
        properties: dict[str, Any] = {
            "공모전명": {
                "title": [{"type": "text", "text": {"content": compact_text(opportunity.title, 1900)}}]
            },
            "공고 ID": self._text_property(opportunity.opportunity_id),
            "원문 링크": {"url": opportunity.source_url},
            "출처": {"select": {"name": opportunity.source[:100]}},
            "유형": {"select": {"name": opportunity.opportunity_type[:100]}},
            "주최/주관": self._text_property(opportunity.organization),
            "모집 시작일": self._date_property(opportunity.recruit_start_date),
            "마감일": self._date_property(opportunity.deadline),
            "행사일": self._date_property(opportunity.event_date),
            "참가 자격": self._text_property(opportunity.eligibility),
            "제출물": self._text_property(opportunity.submission),
            "시상/혜택": self._text_property(opportunity.benefits),
            "요약": self._text_property(opportunity.summary),
            "파싱 신뢰도": {"number": opportunity.parse_confidence},
            "파싱 근거": self._text_property(self._serialize_evidence(opportunity)),
            "마지막 수집시각": self._date_property(opportunity.last_collected_at),
        }
        if opportunity.fit_score is not None:
            properties["적합도"] = {"number": opportunity.fit_score}
        if opportunity.priority:
            properties["우선순위"] = {"select": {"name": opportunity.priority.value}}
        if opportunity.recommendation_reasons:
            properties["추천 이유"] = self._text_property(" · ".join(opportunity.recommendation_reasons))
        if include_status:
            properties["상태"] = self._status_payload(opportunity.status)
        return {self._property_name(name): value for name, value in properties.items()}

    def upsert(self, opportunity: Opportunity) -> Opportunity:
        self.ensure_schema()
        existing_page = self._find_page(opportunity.opportunity_id, opportunity.source_url)
        existing = self._page_to_opportunity(existing_page) if existing_page else None
        if existing and existing.status in _MANUAL_OR_TERMINAL:
            opportunity = opportunity.model_copy(
                update={
                    "status": existing.status,
                    "conflict_status": existing.conflict_status,
                    "calendar_event_ids": existing.calendar_event_ids,
                    "notion_page_id": existing.notion_page_id,
                    "sync_error": existing.sync_error,
                }
            )
        properties = self._properties_for(opportunity, include_status=not bool(existing_page))
        poster = self._poster_files(opportunity, existing_page)
        if poster:
            properties[self._property_name("포스터")] = poster
        if existing_page:
            page_id = existing_page["id"]
            self._request("PATCH", f"/pages/{page_id}", json_body={"properties": properties})
        else:
            created = self._request(
                "POST",
                "/pages",
                json_body={
                    "parent": {"type": "data_source_id", "data_source_id": self.data_source_id},
                    "properties": properties,
                    "icon": {"type": "emoji", "emoji": "📌"},
                },
            )
            page_id = created["id"]
        stored = opportunity.model_copy(update={"notion_page_id": page_id})
        return stored

    def get(self, opportunity_id: str) -> Opportunity | None:
        page = self._find_page(opportunity_id)
        return self._page_to_opportunity(page) if page else None

    def list_by_status(self, statuses: Sequence[OpportunityStatus]) -> list[Opportunity]:
        if not statuses:
            return []
        if len(statuses) == 1:
            filter_body: dict[str, Any] = {
                "property": self._property_name("상태"),
                self._status_filter_key(): {"equals": statuses[0].value},
            }
        else:
            filter_body = {
                "or": [
                    {
                        "property": self._property_name("상태"),
                        self._status_filter_key(): {"equals": status.value},
                    }
                    for status in statuses
                ]
            }
        return [self._page_to_opportunity(page) for page in self._query({"filter": filter_body})]

    def list_all(self) -> list[Opportunity]:
        return [self._page_to_opportunity(page) for page in self._query()]

    def _status_filter_key(self) -> str:
        schema = self.retrieve_schema().get("properties") or {}
        return "status" if (schema.get(self._property_name("상태")) or {}).get("type") == "status" else "select"

    def update_recommendation(self, opportunity_id: str, recommendation: Recommendation) -> Opportunity:
        item = self.get(opportunity_id)
        if not item or not item.notion_page_id:
            raise IntegrationError(f"Unknown Notion opportunity: {opportunity_id}")
        status = item.status
        if status in {OpportunityStatus.NEW, OpportunityStatus.NEEDS_REVIEW, OpportunityStatus.RECOMMENDED}:
            status = OpportunityStatus.RECOMMENDED
        properties = {
            "적합도": {"number": recommendation.score},
            "우선순위": {"select": {"name": recommendation.priority.value}},
            "추천 이유": self._text_property(" · ".join(recommendation.reasons)),
            self._property_name("상태"): self._status_payload(status),
        }
        self._request("PATCH", f"/pages/{item.notion_page_id}", json_body={"properties": properties})
        return item.model_copy(
            update={
                "fit_score": recommendation.score,
                "priority": recommendation.priority,
                "recommendation_reasons": recommendation.reasons,
                "status": status,
            }
        )

    def update_conflict(self, opportunity_id: str, status: ConflictStatus) -> Opportunity:
        item = self.get(opportunity_id)
        if not item or not item.notion_page_id:
            raise IntegrationError(f"Unknown Notion opportunity: {opportunity_id}")
        self._request(
            "PATCH",
            f"/pages/{item.notion_page_id}",
            json_body={"properties": {self._property_name("일정 충돌"): self._conflict_payload(status)}},
        )
        return item.model_copy(update={"conflict_status": status})

    def update_status(
        self,
        opportunity_id: str,
        status: OpportunityStatus,
        *,
        sync_error: str = "",
        calendar_event_ids: dict[str, str] | None = None,
    ) -> Opportunity:
        item = self.get(opportunity_id)
        if not item or not item.notion_page_id:
            raise IntegrationError(f"Unknown Notion opportunity: {opportunity_id}")
        properties: dict[str, Any] = {
            self._property_name("상태"): self._status_payload(status),
            "동기화 오류": self._text_property(sync_error),
        }
        if calendar_event_ids is not None:
            properties[self._property_name("캘린더 이벤트 ID")] = self._text_property(
                json.dumps(calendar_event_ids, ensure_ascii=False, separators=(",", ":"))
            )
        self._request("PATCH", f"/pages/{item.notion_page_id}", json_body={"properties": properties})
        return item.model_copy(
            update={
                "status": status,
                "sync_error": sync_error,
                "calendar_event_ids": calendar_event_ids
                if calendar_event_ids is not None
                else item.calendar_event_ids,
            }
        )

    def _page_to_opportunity(self, page: dict[str, Any] | None) -> Opportunity:
        if not page:
            raise IntegrationError("Cannot parse an empty Notion page")
        props = page.get("properties") or {}
        status_text = self._property_value(props, self._property_name("상태")) or OpportunityStatus.NEW.value
        priority_text = self._property_value(props, "우선순위")
        conflict_text = self._property_value(props, "일정 충돌") or ConflictStatus.UNKNOWN.value
        evidence_text = self._property_value(props, "파싱 근거")
        event_ids_text = self._property_value(props, "캘린더 이벤트 ID")
        try:
            evidence_payload = json.loads(evidence_text) if evidence_text else {}
            evidence = {
                field: [FieldEvidence.model_validate(item) for item in values]
                for field, values in evidence_payload.items()
            }
        except (ValueError, TypeError):
            evidence = {}
        try:
            event_ids = json.loads(event_ids_text) if event_ids_text else {}
        except (ValueError, TypeError):
            event_ids = {}
        return Opportunity(
            opportunity_id=self._property_value(props, "공고 ID"),
            source=self._property_value(props, "출처") or "Unknown",
            source_url=self._property_value(props, "원문 링크"),
            title=self._property_value(props, "공모전명") or "제목 확인 필요",
            organization=self._property_value(props, "주최/주관"),
            opportunity_type=self._property_value(props, "유형") or "공모전",
            summary=self._property_value(props, self._property_name("요약")),
            eligibility=self._property_value(props, "참가 자격"),
            submission=self._property_value(props, "제출물"),
            benefits=self._property_value(props, "시상/혜택"),
            recruit_start_date=parse_date(self._property_value(props, "모집 시작일")),
            deadline=parse_date(self._property_value(props, "마감일")),
            event_date=parse_date(self._property_value(props, "행사일")),
            poster_url=self._files_url(props.get("포스터") or {}),
            parse_confidence=float(self._property_value(props, "파싱 신뢰도") or 0),
            parse_evidence=evidence,
            fit_score=self._optional_int(self._property_value(props, "적합도")),
            priority=Priority(priority_text) if priority_text in {item.value for item in Priority} else None,
            recommendation_reasons=[
                item.strip()
                for item in self._property_value(props, "추천 이유").split("·")
                if item.strip()
            ],
            status=OpportunityStatus(status_text)
            if status_text in {item.value for item in OpportunityStatus}
            else OpportunityStatus.NEW,
            conflict_status=ConflictStatus(conflict_text)
            if conflict_text in {item.value for item in ConflictStatus}
            else ConflictStatus.UNKNOWN,
            notion_page_id=page.get("id"),
            calendar_event_ids=event_ids if isinstance(event_ids, dict) else {},
            sync_error=self._property_value(props, "동기화 오류"),
        )

    def _optional_int(self, value: Any) -> int | None:
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _property_value(self, props: dict[str, Any], name: str) -> Any:
        prop = props.get(name) or {}
        kind = prop.get("type")
        if kind == "title":
            return "".join(item.get("plain_text", "") for item in prop.get("title", []))
        if kind == "rich_text":
            return "".join(item.get("plain_text", "") for item in prop.get("rich_text", []))
        if kind in {"select", "status"}:
            value = prop.get(kind)
            return value.get("name", "") if value else ""
        if kind == "number":
            return prop.get("number")
        if kind == "date":
            value = prop.get("date")
            return value.get("start", "") if value else ""
        if kind == "url":
            return prop.get("url") or ""
        return ""

    def _files_url(self, prop: dict[str, Any]) -> str | None:
        for item in prop.get("files", []) or []:
            item_type = item.get("type")
            if item_type in {"external", "file"}:
                return (item.get(item_type) or {}).get("url")
        return None
