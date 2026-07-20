from __future__ import annotations

from pathlib import Path

from campus_mate.config import Settings
from campus_mate.integrations.base import OpportunityRepository
from campus_mate.models import OpportunityStatus, SourcePage, UserProfile
from campus_mate.parsing.merge import MultiPassParser
from campus_mate.services.recommendation import RecommendationEngine
from campus_mate.utils import now_in_timezone


def run_fixture_demo(
    *,
    settings: Settings,
    repository: OpportunityRepository,
    fixture_path: Path,
    profile: UserProfile,
) -> dict[str, object]:
    html = fixture_path.read_text(encoding="utf-8")
    page = SourcePage(
        source="fixture",
        url="https://example.test/activity/1001",
        html=html,
        fetched_at=now_in_timezone(settings.timezone),
    )
    opportunity = MultiPassParser(settings).parse(page)
    recommendation = RecommendationEngine().score(
        opportunity, profile, today=now_in_timezone(settings.timezone).date()
    )
    opportunity = opportunity.model_copy(
        update={
            "fit_score": recommendation.score,
            "priority": recommendation.priority,
            "recommendation_reasons": recommendation.reasons,
            "status": OpportunityStatus.RECOMMENDED,
        }
    )
    stored = repository.upsert(opportunity)
    return {
        "opportunity": stored.model_dump(mode="json"),
        "recommendation": recommendation.model_dump(mode="json"),
    }
