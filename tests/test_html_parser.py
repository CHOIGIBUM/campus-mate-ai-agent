from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from campus_mate.models import SourcePage
from campus_mate.parsing.html import HtmlOpportunityParser


def test_linkareer_next_data_and_jsonld_are_parsed() -> None:
    fixture = Path("examples/fixtures/linkareer_detail.html").read_text(encoding="utf-8")
    page = SourcePage(
        source="링커리어",
        url="https://linkareer.com/activity/1001",
        html=fixture,
        fetched_at=datetime.now(ZoneInfo("Asia/Seoul")),
    )
    result = HtmlOpportunityParser().parse(page)
    assert result.values["title"] == "2026 대학생 AI 서비스 해커톤"
    assert result.values["organization"] == "테스트 AI 협회"
    assert result.values["deadline"].isoformat() == "2026-09-30"
    assert "전국 대학생" in result.values["eligibility"]
    assert "총 상금 500만원" in result.values["benefits"]
    assert result.values["poster_url"] == "https://example.test/poster.jpg"
    assert max(item.confidence for item in result.evidence["deadline"]) >= 0.98
