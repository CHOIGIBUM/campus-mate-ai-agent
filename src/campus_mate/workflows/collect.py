from __future__ import annotations

import logging
from pathlib import Path

from campus_mate.config import Settings
from campus_mate.integrations.base import OpportunityRepository
from campus_mate.models import (
    CollectionItemResult,
    CollectionReport,
    OpportunityStatus,
    UserProfile,
)
from campus_mate.parsing.merge import MultiPassParser
from campus_mate.services.recommendation import RecommendationEngine
from campus_mate.sources.base import OpportunitySource
from campus_mate.utils import atomic_write_json, now_in_timezone

LOGGER = logging.getLogger(__name__)


def collect_opportunities(
    *,
    settings: Settings,
    repository: OpportunityRepository,
    source: OpportunitySource,
    parser: MultiPassParser,
    profile: UserProfile,
    limit: int,
    force_all_passes: bool = False,
    report_path: Path | None = None,
) -> CollectionReport:
    started = now_in_timezone(settings.timezone)
    repository.ensure_schema()
    urls = source.discover(limit)
    engine = RecommendationEngine()
    results: list[CollectionItemResult] = []
    stored = 0
    needs_review = 0
    today = started.date()

    for url in urls:
        try:
            page = source.fetch(url)
            opportunity = parser.parse(page, force_all_passes=force_all_passes)
            recommendation = engine.score(opportunity, profile, today=today)
            if opportunity.status != OpportunityStatus.NEEDS_REVIEW:
                status = OpportunityStatus.RECOMMENDED
            else:
                status = opportunity.status
                needs_review += 1
            opportunity = opportunity.model_copy(
                update={
                    "fit_score": recommendation.score,
                    "priority": recommendation.priority,
                    "recommendation_reasons": recommendation.reasons,
                    "status": status,
                }
            )
            stored_item = repository.upsert(opportunity)
            stored += 1
            results.append(
                CollectionItemResult(
                    url=url,
                    success=True,
                    opportunity_id=stored_item.opportunity_id,
                    title=stored_item.title,
                )
            )
            LOGGER.info(
                "Stored %s (%s, score=%s)",
                stored_item.title,
                stored_item.status.value,
                stored_item.fit_score,
            )
        except Exception as exc:  # isolate one bad notice from the rest of the scheduled run
            LOGGER.exception("Collection failed for %s", url)
            results.append(
                CollectionItemResult(url=url, success=False, error=f"{type(exc).__name__}: {exc}")
            )

    finished = now_in_timezone(settings.timezone)
    report = CollectionReport(
        started_at=started,
        finished_at=finished,
        source=source.name,
        requested_limit=limit,
        discovered=len(urls),
        stored=stored,
        needs_review=needs_review,
        failures=sum(not item.success for item in results),
        items=results,
    )
    path = report_path or settings.artifacts_dir / f"collection-{started:%Y%m%d-%H%M%S}.json"
    atomic_write_json(path, report.model_dump(mode="json"))
    return report
