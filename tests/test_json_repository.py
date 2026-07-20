from __future__ import annotations

from datetime import date

from campus_mate.integrations.json_repository import JsonOpportunityRepository
from campus_mate.models import Opportunity, OpportunityStatus


def test_upsert_preserves_manual_status(settings) -> None:
    repo = JsonOpportunityRepository(settings.local_store_path)
    original = Opportunity(
        source="fixture",
        source_url="https://example.test/1",
        title="원래 제목",
        deadline=date(2026, 8, 1),
        status=OpportunityStatus.RECOMMENDED,
    )
    stored = repo.upsert(original)
    repo.update_status(stored.opportunity_id, OpportunityStatus.ACCEPT)
    changed = original.model_copy(update={"title": "수정된 제목", "status": OpportunityStatus.RECOMMENDED})
    updated = repo.upsert(changed)
    assert updated.title == "수정된 제목"
    assert updated.status == OpportunityStatus.ACCEPT


def test_repository_lists_by_status(settings) -> None:
    repo = JsonOpportunityRepository(settings.local_store_path)
    item = repo.upsert(
        Opportunity(
            source="fixture",
            source_url="https://example.test/2",
            title="공고",
            status=OpportunityStatus.RECOMMENDED,
        )
    )
    assert [value.opportunity_id for value in repo.list_by_status([OpportunityStatus.RECOMMENDED])] == [
        item.opportunity_id
    ]
