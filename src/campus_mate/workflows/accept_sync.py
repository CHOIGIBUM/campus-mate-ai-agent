from __future__ import annotations

from pathlib import Path

from campus_mate.config import Settings
from campus_mate.integrations.base import OpportunityRepository
from campus_mate.integrations.calendar_bridge import CalendarManifestPlanner, CalendarResultApplier


def plan_calendar_requests(
    *,
    settings: Settings,
    repository: OpportunityRepository,
    output_path: Path,
) -> int:
    planner = CalendarManifestPlanner(repository, timezone=settings.timezone)
    requests = planner.plan()
    planner.write(output_path, requests)
    return len(requests)


def apply_calendar_results(
    *,
    repository: OpportunityRepository,
    requests_path: Path,
    results_path: Path,
) -> dict[str, int]:
    return CalendarResultApplier(repository).apply(requests_path, results_path)
