from __future__ import annotations

from campus_mate.services.onboarding import OnboardingService


def test_profile_roundtrip(settings, profile) -> None:
    service = OnboardingService(settings.profile_path)
    service.save(profile)
    loaded = service.load()
    assert loaded.major == profile.major
    assert "인공지능" in loaded.interests
    assert "ai융합학과" in loaded.search_terms
