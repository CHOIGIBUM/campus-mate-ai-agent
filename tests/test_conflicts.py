from __future__ import annotations

from datetime import date

from campus_mate.integrations.calendar_bridge import apply_conflicts
from campus_mate.integrations.json_repository import JsonOpportunityRepository
from campus_mate.models import ConflictStatus, Opportunity, OpportunityStatus


def test_conflict_detection_updates_repository(settings) -> None:
    repo = JsonOpportunityRepository(settings.local_store_path)
    item = repo.upsert(
        Opportunity(
            source="fixture",
            source_url="https://example.test/conflict",
            title="충돌 공모전",
            event_date=date(2026, 9, 30),
            status=OpportunityStatus.RECOMMENDED,
        )
    )
    result = apply_conflicts(
        repo,
        {
            "busy": [
                {
                    "start": "2026-09-30T09:30:00+09:00",
                    "end": "2026-09-30T10:30:00+09:00",
                }
            ]
        },
    )
    assert result == {"checked": 1, "conflicts": 1}
    assert repo.get(item.opportunity_id).conflict_status == ConflictStatus.EXISTS
