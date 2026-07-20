from __future__ import annotations

from datetime import date

from campus_mate.models import Opportunity, Priority
from campus_mate.services.recommendation import RecommendationEngine


def test_recommendation_is_explainable(profile) -> None:
    item = Opportunity(
        source="fixture",
        source_url="https://example.test/1",
        title="전국 대학생 AI 데이터 해커톤",
        organization="강원 AI 센터",
        eligibility="전국 대학생 및 대학원생",
        summary="Python과 LLM을 활용한 디지털 헬스케어 서비스 개발",
        deadline=date(2026, 8, 10),
    )
    result = RecommendationEngine().score(item, profile, today=date(2026, 7, 20))
    assert result.score >= 70
    assert result.priority in {Priority.IMPORTANT, Priority.URGENT}
    assert result.breakdown["interest"] > 0
    assert any("키워드" in reason or "전공" in reason for reason in result.reasons)


def test_expired_notice_is_not_urgent(profile) -> None:
    item = Opportunity(
        source="fixture",
        source_url="https://example.test/expired",
        title="AI 공모전",
        deadline=date(2026, 1, 1),
    )
    result = RecommendationEngine().score(item, profile, today=date(2026, 7, 20))
    assert result.days_until_deadline < 0
    assert result.priority != Priority.URGENT
    assert result.breakdown["deadline"] == 0
