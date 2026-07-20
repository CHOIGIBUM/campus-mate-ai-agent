from __future__ import annotations

from datetime import date

from campus_mate.integrations.calendar_bridge import CalendarManifestPlanner, CalendarResultApplier
from campus_mate.integrations.json_repository import JsonOpportunityRepository
from campus_mate.models import Opportunity, OpportunityStatus
from campus_mate.utils import atomic_write_json


def test_calendar_plan_and_successful_apply(settings, tmp_path) -> None:
    repo = JsonOpportunityRepository(settings.local_store_path)
    item = repo.upsert(
        Opportunity(
            source="fixture",
            source_url="https://example.test/calendar",
            title="일정 반영 공모전",
            organization="테스트 기관",
            deadline=date(2026, 9, 30),
            event_date=date(2026, 10, 5),
            status=OpportunityStatus.ACCEPT,
        )
    )
    planner = CalendarManifestPlanner(repo)
    requests = planner.plan()
    assert {request.kind for request in requests} == {"deadline", "preparation", "event"}
    request_path = tmp_path / "requests.json"
    result_path = tmp_path / "results.json"
    planner.write(request_path, requests)
    atomic_write_json(
        result_path,
        {
            "results": [
                {"request_id": request.request_id, "success": True, "event_id": f"evt-{request.kind}"}
                for request in requests
            ]
        },
    )
    outcome = CalendarResultApplier(repo).apply(request_path, result_path)
    final = repo.get(item.opportunity_id)
    assert outcome == {"scheduled": 1, "errors": 0, "untouched": 0}
    assert final.status == OpportunityStatus.SCHEDULED
    assert final.calendar_event_ids["deadline"] == "evt-deadline"


def test_partial_calendar_failure_marks_only_that_item_error(settings, tmp_path) -> None:
    repo = JsonOpportunityRepository(settings.local_store_path)
    item = repo.upsert(
        Opportunity(
            source="fixture",
            source_url="https://example.test/calendar-fail",
            title="실패 공모전",
            deadline=date(2026, 9, 30),
            status=OpportunityStatus.ACCEPT,
        )
    )
    planner = CalendarManifestPlanner(repo)
    requests = planner.plan()
    request_path = tmp_path / "requests.json"
    result_path = tmp_path / "results.json"
    planner.write(request_path, requests)
    results = []
    for request in requests:
        results.append(
            {
                "request_id": request.request_id,
                "success": request.kind == "deadline",
                "event_id": "evt-ok" if request.kind == "deadline" else None,
                "error": "connector failure" if request.kind != "deadline" else "",
            }
        )
    atomic_write_json(result_path, {"results": results})
    CalendarResultApplier(repo).apply(request_path, result_path)
    final = repo.get(item.opportunity_id)
    assert final.status == OpportunityStatus.CALENDAR_ERROR
    assert final.calendar_event_ids["deadline"] == "evt-ok"
    assert "connector failure" in final.sync_error
