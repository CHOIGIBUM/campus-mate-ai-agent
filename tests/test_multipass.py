from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from campus_mate.models import SourcePage
from campus_mate.parsing.merge import MultiPassParser


def test_multipass_builds_valid_opportunity(settings) -> None:
    fixture = Path("examples/fixtures/linkareer_detail.html").read_text(encoding="utf-8")
    page = SourcePage(
        source="링커리어",
        url="https://linkareer.com/activity/1001?utm_source=test",
        html=fixture,
        fetched_at=datetime.now(ZoneInfo("Asia/Seoul")),
    )
    opportunity = MultiPassParser(settings).parse(page)
    assert opportunity.title == "2026 대학생 AI 서비스 해커톤"
    assert opportunity.source_url == "https://linkareer.com/activity/1001"
    assert opportunity.deadline.isoformat() == "2026-09-30"
    assert opportunity.parse_confidence > 0.7
    assert opportunity.opportunity_id
