from __future__ import annotations

from datetime import date

from campus_mate.integrations.slack import SlackBriefingClient
from campus_mate.models import ConflictStatus, Opportunity, OpportunityStatus, Priority


def test_slack_message_has_fallback_and_blocks(settings) -> None:
    settings.notion_dashboard_url = "https://notion.example/dashboard"
    item = Opportunity(
        source="fixture",
        source_url="https://example.test/slack",
        title="AI 해커톤",
        deadline=date(2026, 7, 25),
        fit_score=92,
        priority=Priority.URGENT,
        recommendation_reasons=["AI 관심 키워드 일치"],
        status=OpportunityStatus.RECOMMENDED,
        conflict_status=ConflictStatus.EXISTS,
    )
    message = SlackBriefingClient(settings).build_message([item], today=date(2026, 7, 20))
    assert "추천 1건" in message["text"]
    assert any(block.get("type") == "header" for block in message["blocks"])
    assert "Notion" in str(message["blocks"])
