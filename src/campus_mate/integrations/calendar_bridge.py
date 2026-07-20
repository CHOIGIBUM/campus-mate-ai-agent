from __future__ import annotations

from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from campus_mate.integrations.base import OpportunityRepository
from campus_mate.models import (
    CalendarEventRequest,
    CalendarEventResult,
    ConflictStatus,
    Opportunity,
    OpportunityStatus,
)
from campus_mate.utils import atomic_write_json, read_json, stable_identifier


class CalendarManifestPlanner:
    """Create idempotent calendar requests for Timely/Composio.

    Python owns state and idempotency. Timely only executes the external calendar tool and
    writes a result manifest, so a failed tool call cannot incorrectly mark every record as
    scheduled.
    """

    def __init__(self, repository: OpportunityRepository, timezone: str = "Asia/Seoul"):
        self.repository = repository
        self.timezone = timezone
        self.zone = ZoneInfo(timezone)

    def plan(self) -> list[CalendarEventRequest]:
        accepted = self.repository.list_by_status(
            [OpportunityStatus.ACCEPT, OpportunityStatus.CALENDAR_ERROR]
        )
        requests: list[CalendarEventRequest] = []
        for item in accepted:
            item_requests = self._plan_for_item(item)
            requests.extend(item_requests)
            if item_requests and item.status == OpportunityStatus.ACCEPT:
                self.repository.update_status(item.opportunity_id, OpportunityStatus.SCHEDULING)
            elif not item_requests and item.calendar_event_ids:
                self.repository.update_status(
                    item.opportunity_id,
                    OpportunityStatus.SCHEDULED,
                    calendar_event_ids=item.calendar_event_ids,
                )
        return requests

    def _plan_for_item(self, item: Opportunity) -> list[CalendarEventRequest]:
        existing = item.calendar_event_ids
        result: list[CalendarEventRequest] = []
        if item.deadline:
            if "deadline" not in existing:
                result.append(
                    self._request(
                        item,
                        kind="deadline",
                        summary=f"[마감] {item.title}",
                        event_date=item.deadline,
                        event_time=time(23, 0),
                        description=self._description(item, "공모전 접수 마감"),
                    )
                )
            if "preparation" not in existing:
                result.append(
                    self._request(
                        item,
                        kind="preparation",
                        summary=f"[D-3 준비] {item.title}",
                        event_date=item.deadline - timedelta(days=3),
                        event_time=time(9, 0),
                        description=self._description(item, "마감 3일 전 제출물 점검"),
                    )
                )
        if item.event_date and "event" not in existing:
            result.append(
                self._request(
                    item,
                    kind="event",
                    summary=f"[행사] {item.title}",
                    event_date=item.event_date,
                    event_time=time(9, 0),
                    description=self._description(item, "행사 또는 시작일"),
                )
            )
        return result

    def _request(
        self,
        item: Opportunity,
        *,
        kind: str,
        summary: str,
        event_date: date,
        event_time: time,
        description: str,
    ) -> CalendarEventRequest:
        start = datetime.combine(event_date, event_time, self.zone)
        idempotency_key = stable_identifier(item.opportunity_id, kind, start.isoformat(), length=32)
        return CalendarEventRequest(
            request_id=idempotency_key,
            opportunity_id=item.opportunity_id,
            notion_page_id=item.notion_page_id,
            kind=kind,  # type: ignore[arg-type]
            summary=summary,
            start_datetime=start,
            duration_minutes=60,
            timezone=self.timezone,
            description=description,
            idempotency_key=idempotency_key,
        )

    def _description(self, item: Opportunity, heading: str) -> str:
        parts = [heading]
        if item.organization:
            parts.append(f"주최/주관: {item.organization}")
        if item.source_url:
            parts.append(f"원문: {item.source_url}")
        parts.append(f"Campus Mate ID: {item.opportunity_id}")
        return "\n".join(parts)

    @staticmethod
    def write(path: Path, requests: list[CalendarEventRequest]) -> None:
        atomic_write_json(
            path,
            {
                "schema_version": 1,
                "tool": "GOOGLECALENDAR_CREATE_EVENT",
                "requests": [request.model_dump(mode="json") for request in requests],
            },
        )


class CalendarResultApplier:
    def __init__(self, repository: OpportunityRepository):
        self.repository = repository

    def apply(self, requests_path: Path, results_path: Path) -> dict[str, int]:
        requests_payload = read_json(requests_path, {}) or {}
        result_payload = read_json(results_path, {}) or {}
        requests = {
            item["request_id"]: CalendarEventRequest.model_validate(item)
            for item in requests_payload.get("requests", [])
        }
        results = [CalendarEventResult.model_validate(item) for item in result_payload.get("results", [])]
        results_by_request = {result.request_id: result for result in results}
        opportunity_ids = {request.opportunity_id for request in requests.values()}

        scheduled = 0
        errors = 0
        untouched = 0
        for opportunity_id in opportunity_ids:
            item = self.repository.get(opportunity_id)
            if not item:
                untouched += 1
                continue
            event_ids = dict(item.calendar_event_ids)
            failure_messages: list[str] = []
            planned = [request for request in requests.values() if request.opportunity_id == opportunity_id]
            for request in planned:
                result = results_by_request.get(request.request_id)
                if result and result.success and result.event_id:
                    event_ids[request.kind] = result.event_id
                elif result:
                    failure_messages.append(result.error or f"{request.kind} calendar creation failed")
                else:
                    failure_messages.append(f"Missing calendar result for {request.kind}")
            planned_kinds = {request.kind for request in planned}
            all_done = planned_kinds.issubset(event_ids.keys()) and not failure_messages
            if all_done:
                self.repository.update_status(
                    opportunity_id,
                    OpportunityStatus.SCHEDULED,
                    calendar_event_ids=event_ids,
                )
                scheduled += 1
            else:
                self.repository.update_status(
                    opportunity_id,
                    OpportunityStatus.CALENDAR_ERROR,
                    sync_error=" | ".join(failure_messages) or "Calendar result missing",
                    calendar_event_ids=event_ids,
                )
                errors += 1
        return {"scheduled": scheduled, "errors": errors, "untouched": untouched}


class FreeBusyNormalizer:
    """Normalize Timely/Composio/Google event payloads into busy intervals."""

    @staticmethod
    def normalize(payload: Any) -> list[dict[str, str]]:
        if isinstance(payload, list):
            return FreeBusyNormalizer._from_list(payload)
        if not isinstance(payload, dict):
            return []
        if isinstance(payload.get("busy"), list):
            return FreeBusyNormalizer._from_list(payload["busy"])
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        calendars = data.get("calendars") if isinstance(data, dict) else None
        if isinstance(calendars, dict):
            intervals: list[dict[str, str]] = []
            for calendar in calendars.values():
                if isinstance(calendar, dict):
                    intervals.extend(FreeBusyNormalizer._from_list(calendar.get("busy", [])))
            return intervals
        items = data.get("items") if isinstance(data, dict) else None
        if isinstance(items, list):
            return FreeBusyNormalizer._from_event_items(items)
        return []

    @staticmethod
    def _from_list(items: list[Any]) -> list[dict[str, str]]:
        intervals: list[dict[str, str]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            start = item.get("start") or item.get("start_datetime")
            end = item.get("end") or item.get("end_datetime")
            if isinstance(start, dict):
                start = start.get("dateTime") or start.get("date")
            if isinstance(end, dict):
                end = end.get("dateTime") or end.get("date")
            if start and end:
                intervals.append({"start": str(start), "end": str(end)})
        return intervals

    @staticmethod
    def _from_event_items(items: list[Any]) -> list[dict[str, str]]:
        return FreeBusyNormalizer._from_list(items)


def apply_conflicts(
    repository: OpportunityRepository,
    payload: Any,
    *,
    timezone: str = "Asia/Seoul",
) -> dict[str, int]:
    intervals = FreeBusyNormalizer.normalize(payload)
    zone = ZoneInfo(timezone)
    parsed: list[tuple[datetime, datetime]] = []
    for interval in intervals:
        try:
            start = _parse_datetime(interval["start"], zone)
            end = _parse_datetime(interval["end"], zone)
        except (ValueError, TypeError):
            continue
        parsed.append((start, end))

    checked = 0
    conflicts = 0
    for item in repository.list_by_status([OpportunityStatus.RECOMMENDED, OpportunityStatus.ACCEPT]):
        candidate_intervals = _opportunity_intervals(item, zone)
        status = ConflictStatus.NONE
        if any(_overlaps(candidate, busy) for candidate in candidate_intervals for busy in parsed):
            status = ConflictStatus.EXISTS
            conflicts += 1
        repository.update_conflict(item.opportunity_id, status)
        checked += 1
    return {"checked": checked, "conflicts": conflicts}


def _opportunity_intervals(item: Opportunity, zone: ZoneInfo) -> list[tuple[datetime, datetime]]:
    values: list[tuple[datetime, datetime]] = []
    if item.deadline:
        start = datetime.combine(item.deadline, time(22, 30), zone)
        values.append((start, start + timedelta(hours=1, minutes=30)))
    if item.event_date:
        start = datetime.combine(item.event_date, time(9, 0), zone)
        values.append((start, start + timedelta(hours=2)))
    return values


def _parse_datetime(value: str, zone: ZoneInfo) -> datetime:
    text = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=zone)
    return parsed.astimezone(zone)


def _overlaps(left: tuple[datetime, datetime], right: tuple[datetime, datetime]) -> bool:
    return left[0] < right[1] and right[0] < left[1]


def write_standardized_busy(path: Path, payload: Any) -> None:
    atomic_write_json(path, {"busy": FreeBusyNormalizer.normalize(payload)})
