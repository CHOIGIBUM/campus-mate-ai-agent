"""Profile Agent interactive onboarding flow."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "profile-build"))

from utils import (  # noqa: E402
    ensure_profiles_dir,
    find_existing_profile,
    generate_user_id,
    load_choices,
    load_profile,
    pick_multiple,
    print_profile_summary,
    validate_email,
    validate_free_input,
    validate_hours,
    validate_name,
    validate_time,
)
from profile_build import ProfileBuildSkill  # noqa: E402


class ProfileAgent:
    def __init__(self) -> None:
        ensure_profiles_dir()
        self.choices = load_choices()
        self.skill = ProfileBuildSkill()
        self.data: Dict[str, Any] = {}
        self.is_update = False

    def run(self) -> None:
        print("\n=== Profile Agent 시작 ===")
        self.step_1()
        self.step_2()
        self.step_3()
        self.step_4()
        self.step_5()

    def step_1(self) -> None:
        print("\n[Step 1] 기본 정보")
        while True:
            name = input("이름: ").strip()
            ok, msg = validate_name(name)
            if ok:
                self.data["name"] = name
                break
            print(msg)

        while True:
            email = input("이메일: ").strip()
            ok, msg = validate_email(email)
            if not ok:
                print(msg)
                continue
            existing = find_existing_profile(email)
            if existing:
                print(f"기존 프로필 발견: {existing.name}")
                ans = input("이 프로필을 수정하시겠습니까? (y/n): ").strip().lower()
                if ans == "y":
                    self.is_update = True
                    self.data["email"] = email
                    break
                print("새 이메일로 다시 입력해주세요.")
                continue
            self.data["email"] = email
            break

        while True:
            schools = self.choices["schools"]
            print("학교 선택:")
            for i, s in enumerate(schools, 1):
                print(f"  {i}. {s}")
            print(f"  {len(schools)+1}. 기타 입력")
            raw = input("번호: ").strip()
            if raw.isdigit():
                idx = int(raw)
                if 1 <= idx <= len(schools):
                    self.data["school"] = schools[idx - 1]
                    break
                if idx == len(schools) + 1:
                    val = input("학교명: ").strip()
                    ok, msg = validate_free_input(val, 100)
                    if ok:
                        self.data["school"] = val
                        break
                    print(msg)
            print("올바른 번호를 입력해주세요.")

        while True:
            majors = self.choices["majors"]
            print("학과 선택:")
            for i, m in enumerate(majors, 1):
                print(f"  {i}. {m}")
            print(f"  {len(majors)+1}. 기타 입력")
            raw = input("번호: ").strip()
            if raw.isdigit():
                idx = int(raw)
                if 1 <= idx <= len(majors):
                    self.data["major"] = majors[idx - 1]
                    break
                if idx == len(majors) + 1:
                    val = input("학과명: ").strip()
                    ok, msg = validate_free_input(val, 100)
                    if ok:
                        self.data["major"] = val
                        break
                    print(msg)
            print("올바른 번호를 입력해주세요.")

        years = ["1학년", "2학년", "3학년", "4학년", "석사", "박사"]
        while True:
            for i, y in enumerate(years, 1):
                print(f"  {i}. {y}")
            raw = input("학년 번호: ").strip()
            if raw.isdigit() and 1 <= int(raw) <= len(years):
                self.data["year"] = years[int(raw) - 1]
                break
            print("올바른 번호를 입력해주세요.")

    def step_2(self) -> None:
        print("\n[Step 2] 관심 분야 & 희망 직무")
        self.data["interests"] = pick_multiple("관심 분야", self.choices["interests"], 1, 10, allow_custom=True)
        self.data["positions"] = pick_multiple("희망 직무", self.choices["positions"], 1, 5, allow_custom=True)

    def step_3(self) -> None:
        print("\n[Step 3] 활동 선호도")
        self.data["activity_types"] = pick_multiple("활동 유형", self.choices["activity_types"], 1, 5)
        self.data["regions"] = pick_multiple("활동 지역", self.choices["regions"], 0, 5)

    def step_4(self) -> None:
        print("\n[Step 4] 시간 & 알림")
        while True:
            raw = input("주간 투자 시간(선택, Enter=스킵): ").strip()
            ok, hours = validate_hours(raw)
            if ok:
                self.data["available_hours_per_week"] = hours
                break
            print("0~168 사이의 정수를 입력해주세요.")
        while True:
            raw = input("보고 시간(HH:MM): ").strip()
            ok, msg = validate_time(raw)
            if ok:
                self.data["report_time"] = raw
                break
            print(msg)

    def step_5(self) -> None:
        print("\n[Step 5] 확인 및 저장")
        profile = {
            "name": self.data["name"],
            "email": self.data["email"],
            "school": self.data["school"],
            "major": self.data["major"],
            "year": self.data["year"],
            "interests": self.data["interests"],
            "positions": self.data["positions"],
            "activity_types": self.data["activity_types"],
            "regions": self.data["regions"],
            "available_hours_per_week": self.data.get("available_hours_per_week"),
            "report_time": self.data["report_time"],
        }
        user_id = generate_user_id()
        profile["user_id"] = user_id
        print_profile_summary({
            "basic_info": {k: profile[k] for k in ["name", "email", "school", "major", "year"]},
            "interests": {"fields": profile["interests"]},
            "career_goal": {"positions": profile["positions"]},
            "preferences": {
                "activity_types": profile["activity_types"],
                "regions": profile["regions"],
                "available_hours_per_week": profile["available_hours_per_week"],
            },
            "availability": {"report_time": profile["report_time"]},
        })
        ans = input("저장할까요? (y/n): ").strip().lower()
        if ans != "y":
            print("저장을 취소했습니다.")
            return
        success, msg, _ = self.skill.execute({
            "name": self.data["name"],
            "email": self.data["email"],
            "school": self.data["school"],
            "major": self.data["major"],
            "year": self.data["year"],
            "interests": self.data["interests"],
            "positions": self.data["positions"],
            "activity_types": self.data["activity_types"],
            "regions": self.data["regions"],
            "available_hours_per_week": self.data.get("available_hours_per_week"),
            "report_time": self.data["report_time"],
            "email": self.data["email"],
        }, user_id)
        print(msg)
        if success:
            print(f"user_id: {user_id}")


if __name__ == "__main__":
    ProfileAgent().run()
