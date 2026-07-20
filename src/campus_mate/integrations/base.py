from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from campus_mate.models import ConflictStatus, Opportunity, OpportunityStatus, Recommendation


class OpportunityRepository(Protocol):
    def ensure_schema(self) -> None: ...

    def upsert(self, opportunity: Opportunity) -> Opportunity: ...

    def get(self, opportunity_id: str) -> Opportunity | None: ...

    def list_by_status(self, statuses: Sequence[OpportunityStatus]) -> list[Opportunity]: ...

    def list_all(self) -> list[Opportunity]: ...

    def update_recommendation(self, opportunity_id: str, recommendation: Recommendation) -> Opportunity: ...

    def update_conflict(self, opportunity_id: str, status: ConflictStatus) -> Opportunity: ...

    def update_status(
        self,
        opportunity_id: str,
        status: OpportunityStatus,
        *,
        sync_error: str = "",
        calendar_event_ids: dict[str, str] | None = None,
    ) -> Opportunity: ...
