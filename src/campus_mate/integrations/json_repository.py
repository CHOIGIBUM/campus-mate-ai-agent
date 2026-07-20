from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from threading import RLock

from campus_mate.exceptions import IntegrationError
from campus_mate.models import ConflictStatus, Opportunity, OpportunityStatus, Recommendation
from campus_mate.utils import atomic_write_json, read_json

_MANUAL_OR_TERMINAL = {
    OpportunityStatus.ACCEPT,
    OpportunityStatus.SCHEDULING,
    OpportunityStatus.SCHEDULED,
    OpportunityStatus.HOLD,
    OpportunityStatus.REJECT,
    OpportunityStatus.CALENDAR_ERROR,
}


class JsonOpportunityRepository:
    """Small deterministic repository used for tests, fixtures, and dry runs."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def ensure_schema(self) -> None:
        if not self.path.exists():
            atomic_write_json(self.path, {"items": {}})

    def _load(self) -> dict[str, Opportunity]:
        payload = read_json(self.path, {"items": {}}) or {"items": {}}
        return {
            key: Opportunity.model_validate(value)
            for key, value in (payload.get("items") or {}).items()
        }

    def _save(self, items: dict[str, Opportunity]) -> None:
        atomic_write_json(
            self.path,
            {"items": {key: item.model_dump(mode="json") for key, item in items.items()}},
        )

    def upsert(self, opportunity: Opportunity) -> Opportunity:
        with self._lock:
            items = self._load()
            existing = items.get(opportunity.opportunity_id)
            if existing:
                preserved_status = existing.status if existing.status in _MANUAL_OR_TERMINAL else opportunity.status
                preserved_conflict = existing.conflict_status
                preserved_calendar_ids = existing.calendar_event_ids
                preserved_page_id = existing.notion_page_id
                merged = opportunity.model_copy(
                    update={
                        "status": preserved_status,
                        "conflict_status": preserved_conflict,
                        "calendar_event_ids": preserved_calendar_ids,
                        "notion_page_id": preserved_page_id,
                        "sync_error": existing.sync_error if preserved_status == OpportunityStatus.CALENDAR_ERROR else "",
                    }
                )
            else:
                merged = opportunity
            items[merged.opportunity_id] = merged
            self._save(items)
            return merged

    def get(self, opportunity_id: str) -> Opportunity | None:
        return self._load().get(opportunity_id)

    def list_by_status(self, statuses: Sequence[OpportunityStatus]) -> list[Opportunity]:
        wanted = set(statuses)
        return [item for item in self._load().values() if item.status in wanted]

    def list_all(self) -> list[Opportunity]:
        return list(self._load().values())

    def update_recommendation(self, opportunity_id: str, recommendation: Recommendation) -> Opportunity:
        with self._lock:
            items = self._load()
            item = items.get(opportunity_id)
            if not item:
                raise IntegrationError(f"Unknown opportunity: {opportunity_id}")
            status = item.status
            if status in {OpportunityStatus.NEW, OpportunityStatus.NEEDS_REVIEW, OpportunityStatus.RECOMMENDED}:
                status = OpportunityStatus.RECOMMENDED
            item = item.model_copy(
                update={
                    "fit_score": recommendation.score,
                    "priority": recommendation.priority,
                    "recommendation_reasons": recommendation.reasons,
                    "status": status,
                }
            )
            items[opportunity_id] = item
            self._save(items)
            return item

    def update_conflict(self, opportunity_id: str, status: ConflictStatus) -> Opportunity:
        with self._lock:
            items = self._load()
            item = items.get(opportunity_id)
            if not item:
                raise IntegrationError(f"Unknown opportunity: {opportunity_id}")
            item = item.model_copy(update={"conflict_status": status})
            items[opportunity_id] = item
            self._save(items)
            return item

    def update_status(
        self,
        opportunity_id: str,
        status: OpportunityStatus,
        *,
        sync_error: str = "",
        calendar_event_ids: dict[str, str] | None = None,
    ) -> Opportunity:
        with self._lock:
            items = self._load()
            item = items.get(opportunity_id)
            if not item:
                raise IntegrationError(f"Unknown opportunity: {opportunity_id}")
            update = {"status": status, "sync_error": sync_error}
            if calendar_event_ids is not None:
                update["calendar_event_ids"] = calendar_event_ids
            item = item.model_copy(update=update)
            items[opportunity_id] = item
            self._save(items)
            return item
