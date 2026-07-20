from __future__ import annotations

import re
from datetime import date

from campus_mate.models import Opportunity, Priority, Recommendation, UserProfile


class RecommendationEngine:
    """Deterministic, explainable profile-to-notice scoring."""

    def score(self, opportunity: Opportunity, profile: UserProfile, *, today: date) -> Recommendation:
        text = opportunity.searchable_text
        breakdown: dict[str, int] = {}
        reasons: list[str] = []

        interest_score, interest_hits = self._interest_score(text, profile)
        breakdown["interest"] = interest_score
        if interest_hits:
            reasons.append("관심 키워드 일치: " + ", ".join(interest_hits[:4]))

        major_score, major_hits = self._major_score(text, profile)
        breakdown["major_career"] = major_score
        if major_hits:
            reasons.append("전공·진로 연관: " + ", ".join(major_hits[:3]))

        activity_score, activity_hit = self._activity_score(text, profile)
        breakdown["activity_type"] = activity_score
        if activity_hit:
            reasons.append(f"희망 활동 유형 일치: {activity_hit}")

        eligibility_score, eligibility_reason = self._eligibility_score(opportunity, profile)
        breakdown["eligibility"] = eligibility_score
        if eligibility_reason:
            reasons.append(eligibility_reason)

        deadline_score, days_until, deadline_reason = self._deadline_score(opportunity, today)
        breakdown["deadline"] = deadline_score
        if deadline_reason:
            reasons.append(deadline_reason)

        region_score, region_reason = self._region_score(text, profile)
        breakdown["region"] = region_score
        if region_reason:
            reasons.append(region_reason)

        completeness = self._completeness_score(opportunity)
        breakdown["data_quality"] = completeness
        total = max(0, min(sum(breakdown.values()), 100))
        priority = self._priority(total, days_until)
        if not reasons:
            reasons.append("기본 프로필 조건으로 평가")
        return Recommendation(
            score=total,
            priority=priority,
            reasons=reasons,
            breakdown=breakdown,
            days_until_deadline=days_until,
        )

    def _interest_score(self, text: str, profile: UserProfile) -> tuple[int, list[str]]:
        terms = [*profile.interests, *profile.keywords]
        hits = [term for term in terms if self._contains(text, term)]
        unique = list(dict.fromkeys(hits))
        return min(len(unique) * 8, 30), unique

    def _major_score(self, text: str, profile: UserProfile) -> tuple[int, list[str]]:
        terms = [profile.major, profile.career_goal]
        tokens = []
        for term in terms:
            tokens.extend(self._tokens(term))
        hits = [token for token in dict.fromkeys(tokens) if token in text]
        if not hits:
            return 0, []
        return min(8 + len(hits) * 4, 20), hits

    def _activity_score(self, text: str, profile: UserProfile) -> tuple[int, str]:
        aliases = {
            "공모전": ("공모전", "경진대회", "챌린지", "contest"),
            "해커톤": ("해커톤", "hackathon"),
            "대외활동": ("대외활동", "서포터즈", "기자단"),
            "교육": ("교육", "부트캠프", "아카데미", "캠프"),
            "인턴십": ("인턴", "intern"),
        }
        for preferred in profile.activity_types:
            key = next((name for name in aliases if name in preferred), preferred)
            words = aliases.get(key, (preferred.lower(),))
            if any(word.lower() in text for word in words):
                return 15, key
        return 3, ""

    def _eligibility_score(self, opportunity: Opportunity, profile: UserProfile) -> tuple[int, str]:
        eligibility = opportunity.eligibility.lower()
        if not eligibility:
            return 5, "참가 자격은 추가 확인 필요"
        grade_tokens = self._tokens(profile.grade)
        major_tokens = self._tokens(profile.major)
        if any(token in eligibility for token in grade_tokens + major_tokens):
            return 10, "학년·전공 조건과 일치"
        if any(word in eligibility for word in ("대학생", "대학(원)생", "전국 대학", "누구나", "제한 없음")):
            return 9, "대학생 또는 제한 없는 참가 자격"
        if any(word in eligibility for word in ("직장인", "고등학생", "중학생")):
            return 1, "참가 자격 확인 필요"
        return 6, "참가 자격 세부 확인 필요"

    def _deadline_score(self, opportunity: Opportunity, today: date) -> tuple[int, int | None, str]:
        if not opportunity.deadline:
            return 2, None, "마감일 확인 필요"
        days = (opportunity.deadline - today).days
        if days < 0:
            return 0, days, "이미 마감된 공고"
        if days <= 3:
            return 5, days, f"마감 임박(D-{days})"
        if days <= 7:
            return 9, days, f"마감 임박(D-{days})"
        if days <= 21:
            return 15, days, f"준비 기간 적절(D-{days})"
        if days <= 60:
            return 12, days, f"준비 기간 충분(D-{days})"
        return 8, days, f"장기 준비 가능(D-{days})"

    def _region_score(self, text: str, profile: UserProfile) -> tuple[int, str]:
        if not profile.preferred_regions:
            return 3, ""
        hits = [region for region in profile.preferred_regions if region.lower() in text]
        return (5, "선호 지역 일치: " + ", ".join(hits)) if hits else (1, "")

    def _completeness_score(self, opportunity: Opportunity) -> int:
        fields = [
            opportunity.title,
            opportunity.deadline,
            opportunity.organization,
            opportunity.eligibility,
            opportunity.source_url,
        ]
        return min(sum(value not in (None, "") for value in fields), 5)

    def _priority(self, score: int, days_until: int | None) -> Priority:
        if days_until is not None and 0 <= days_until <= 7 and score >= 60:
            return Priority.URGENT
        if score >= 70:
            return Priority.IMPORTANT
        return Priority.REFERENCE

    def _contains(self, text: str, phrase: str) -> bool:
        phrase = phrase.strip().lower()
        if not phrase:
            return False
        return phrase in text or any(token in text for token in self._tokens(phrase))

    def _tokens(self, text: str) -> list[str]:
        return [
            token.lower()
            for token in re.split(r"[\s,/()·|+_-]+", text or "")
            if len(token.strip()) >= 2
        ]
