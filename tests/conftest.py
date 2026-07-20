from __future__ import annotations

from pathlib import Path

import pytest

from campus_mate.config import Settings
from campus_mate.models import UserProfile


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    value = Settings(
        CAMPUS_MATE_ENV="test",
        CAMPUS_MATE_STORAGE_BACKEND="json",
        CAMPUS_MATE_DATA_DIR=tmp_path / "data",
        CAMPUS_MATE_ARTIFACTS_DIR=tmp_path / "artifacts",
        CAMPUS_MATE_PROFILE_PATH=tmp_path / "data/profile.json",
        CAMPUS_MATE_LOCAL_STORE_PATH=tmp_path / "data/opportunities.json",
        CAMPUS_MATE_ENABLE_OCR=False,
        CAMPUS_MATE_ENABLE_VISION=False,
    )
    value.ensure_directories()
    return value


@pytest.fixture
def profile() -> UserProfile:
    return UserProfile(
        name="테스터",
        school="강원대학교",
        grade="3학년",
        major="AI융합학과",
        interests=["인공지능", "데이터", "헬스케어"],
        activity_types=["공모전", "해커톤"],
        career_goal="AI 엔지니어",
        keywords=["Python", "LLM"],
        preferred_regions=["강원", "온라인"],
    )
