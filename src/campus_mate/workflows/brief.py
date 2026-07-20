from __future__ import annotations

from pathlib import Path

from campus_mate.config import Settings
from campus_mate.integrations.base import OpportunityRepository
from campus_mate.integrations.slack import SlackBriefingClient
from campus_mate.models import BriefingReport, OpportunityStatus
from campus_mate.utils import now_in_timezone


def create_briefing(
    *,
    settings: Settings,
    repository: OpportunityRepository,
    slack: SlackBriefingClient,
    dry_run: bool = False,
    output_path: Path | None = None,
) -> BriefingReport:
    now = now_in_timezone(settings.timezone)
    opportunities = repository.list_by_status([OpportunityStatus.RECOMMENDED])
    message = slack.build_message(opportunities, today=now.date())
    urgent = [
        item
        for item in opportunities
        if item.deadline and 0 <= (item.deadline - now.date()).days <= 7
    ]
    conflicts = [item for item in opportunities if item.conflict_status.value == "있음"]
    delivered = False
    artifact: str | None = None
    if dry_run:
        path = output_path or settings.artifacts_dir / f"slack-briefing-{now:%Y%m%d-%H%M%S}.json"
        slack.write_dry_run(message, path)
        artifact = str(path)
    else:
        slack.send(message)
        delivered = True
    return BriefingReport(
        generated_at=now,
        recommended_count=len(opportunities),
        urgent_count=len(urgent),
        conflict_count=len(conflicts),
        delivered=delivered,
        destination=settings.slack_channel_id or "dry-run artifact",
        artifact_path=artifact,
    )
