from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from campus_mate.models import UserProfile
from campus_mate.utils import atomic_write_json, read_json


class OnboardingService:
    def __init__(self, profile_path: Path):
        self.profile_path = profile_path

    def load(self) -> UserProfile:
        payload = read_json(self.profile_path)
        if payload is None:
            raise FileNotFoundError(
                f"Profile not found: {self.profile_path}. Run 'campus-mate profile init' first."
            )
        return UserProfile.model_validate(payload)

    def save(self, profile: UserProfile) -> UserProfile:
        atomic_write_json(self.profile_path, profile.model_dump(mode="json"))
        return profile

    def import_payload(self, payload: dict[str, Any]) -> UserProfile:
        return self.save(UserProfile.model_validate(payload))

    def import_json_text(self, text: str) -> UserProfile:
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise ValueError("Profile JSON must be an object")
        return self.import_payload(payload)

    def interactive(self, ask: Callable[[str], str] = input) -> UserProfile:
        print("Campus Mate 온보딩 — 추천에 사용할 정보를 입력합니다.")
        existing: dict[str, Any] = read_json(self.profile_path, {}) or {}

        def prompt(label: str, key: str, *, required: bool = True) -> str:
            default = str(existing.get(key) or "")
            suffix = f" [{default}]" if default else ""
            while True:
                value = ask(f"{label}{suffix}: ").strip() or default
                if value or not required:
                    return value
                print("필수 항목입니다.")

        def prompt_list(label: str, key: str, *, required: bool = False) -> list[str]:
            default_values = existing.get(key) or []
            default = ", ".join(default_values) if isinstance(default_values, list) else str(default_values)
            suffix = f" [{default}]" if default else ""
            while True:
                raw = ask(f"{label} (쉼표로 구분){suffix}: ").strip() or default
                values = [piece.strip() for piece in raw.split(",") if piece.strip()]
                if values or not required:
                    return values
                print("한 개 이상 입력해 주세요.")

        profile = UserProfile(
            name=prompt("이름", "name", required=False),
            school=prompt("학교", "school"),
            grade=prompt("학년", "grade"),
            major=prompt("학과·전공", "major"),
            interests=prompt_list("관심 분야", "interests", required=True),
            activity_types=prompt_list("희망 활동 유형", "activity_types") or ["공모전", "해커톤"],
            career_goal=prompt("희망 직무·진로", "career_goal", required=False),
            keywords=prompt_list("추가 관심 키워드", "keywords"),
            preferred_regions=prompt_list("선호 지역", "preferred_regions"),
            available_times=prompt_list("가능 시간대", "available_times"),
        )
        self.save(profile)
        print("\n저장된 추천 프로필")
        print(self.summary(profile))
        return profile

    def summary(self, profile: UserProfile) -> str:
        return "\n".join(
            [
                f"- 학교/학년: {profile.school} · {profile.grade}",
                f"- 전공: {profile.major}",
                f"- 관심 분야: {', '.join(profile.interests)}",
                f"- 활동 유형: {', '.join(profile.activity_types)}",
                f"- 희망 진로: {profile.career_goal or '-'}",
                f"- 키워드: {', '.join(profile.keywords) or '-'}",
            ]
        )
