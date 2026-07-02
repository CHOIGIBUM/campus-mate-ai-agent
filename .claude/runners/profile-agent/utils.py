"""Utilities for Profile Agent."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CHOICES_DIR = Path("./data/choices")
PROFILES_DIR = Path("./data/profiles")


def load_json_list(name: str, key: str) -> List[str]:
    path = CHOICES_DIR / name
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(key, [])


def load_choices() -> Dict[str, List[str]]:
    return {
        "schools": load_json_list("schools.json", "schools"),
        "majors": load_json_list("majors.json", "majors"),
        "interests": load_json_list("interests.json", "interests"),
        "positions": load_json_list("positions.json", "positions"),
        "activity_types": load_json_list("activity_types.json", "activity_types"),
        "regions": load_json_list("regions.json", "regions"),
    }


def ensure_profiles_dir() -> Path:
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    return PROFILES_DIR


def validate_name(name: str) -> Tuple[bool, str]:
    if not name or not name.strip():
        return False, "이름을 입력해주세요."
    if len(name.strip()) > 50:
        return False, "이름은 50자 이하여야 합니다."
    if not re.match(r"^[가-힣a-zA-Z0-9\s\-·]+$", name.strip()):
        return False, "이름에는 한글, 영문, 숫자, 공백, -, ·만 사용할 수 있습니다."
    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    if not email or not email.strip():
        return False, "이메일을 입력해주세요."
    pat = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pat, email.strip()):
        return False, "올바른 이메일 형식이 아닙니다."
    return True, ""


def validate_free_input(text: str, max_length: int = 100) -> Tuple[bool, str]:
    if not text or not text.strip():
        return False, "값을 입력해주세요."
    if len(text.strip()) > max_length:
        return False, f"{max_length}자 이하여야 합니다."
    return True, ""


def validate_time(time_str: str) -> Tuple[bool, str]:
    if not time_str or not time_str.strip():
        return False, "시간을 입력해주세요."
    if not re.match(r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$", time_str.strip()):
        return False, "시간 형식이 올바르지 않습니다. (HH:MM)"
    return True, ""


def validate_hours(hours_str: str) -> Tuple[bool, Optional[int]]:
    if not hours_str or not hours_str.strip():
        return True, None
    try:
        hours = int(hours_str.strip())
    except ValueError:
        return False, None
    if hours < 0 or hours > 168:
        return False, None
    return True, hours


def find_existing_profile(email: str) -> Optional[Path]:
    ensure_profiles_dir()
    for p in PROFILES_DIR.glob("user_profile_*.json"):
        try:
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("basic_info", {}).get("email") == email:
                return p
        except Exception:
            continue
    return None


def load_profile(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def generate_user_id() -> str:
    ensure_profiles_dir()
    today = datetime.now().strftime("%Y%m%d")
    existing = list(PROFILES_DIR.glob(f"user_profile_user_{today}_*.json"))
    seq = len(existing) + 1
    return f"user_{today}_{seq:03d}"


def pick_multiple(label: str, choices: List[str], min_count: int, max_count: int, allow_custom: bool = False) -> List[str]:
    print(f"\n{label}")
    for i, c in enumerate(choices, 1):
        print(f"  {i}. {c}")
    if allow_custom:
        print(f"  {len(choices) + 1}. 기타 입력")
    while True:
        raw = input("번호를 쉼표로 입력하세요: ").strip()
        if not raw:
            if min_count == 0:
                return []
            print(f"최소 {min_count}개 이상 선택해주세요.")
            continue
        items: List[str] = []
        ok = True
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            if not part.isdigit():
                ok = False
                break
            idx = int(part)
            if 1 <= idx <= len(choices):
                items.append(choices[idx - 1])
            elif allow_custom and idx == len(choices) + 1:
                custom = input("기타 입력: ").strip()
                valid, msg = validate_free_input(custom, 50)
                if not valid:
                    print(msg)
                    ok = False
                    break
                items.append(custom)
            else:
                ok = False
                break
        items = list(dict.fromkeys(items))
        if not ok:
            print("올바른 번호를 입력해주세요.")
            continue
        if len(items) < min_count:
            print(f"최소 {min_count}개 이상 선택해주세요.")
            continue
        if len(items) > max_count:
            print(f"최대 {max_count}개까지 선택 가능합니다.")
            continue
        return items


def print_profile_summary(profile: Dict[str, Any]) -> None:
    basic = profile.get("basic_info", {})
    interests = profile.get("interests", {})
    career = profile.get("career_goal", {})
    prefs = profile.get("preferences", {})
    avail = profile.get("availability", {})
    print("\n" + "=" * 50)
    print("프로필 요약")
    print("=" * 50)
    print(f"이름: {basic.get('name')}")
    print(f"이메일: {basic.get('email')}")
    print(f"학교: {basic.get('school')}")
    print(f"학과: {basic.get('major')}")
    print(f"학년: {basic.get('year')}")
    print(f"관심분야: {', '.join(interests.get('fields', []))}")
    print(f"희망직무: {', '.join(career.get('positions', []))}")
    print(f"활동유형: {', '.join(prefs.get('activity_types', []))}")
    print(f"지역: {', '.join(prefs.get('regions', []))}")
    print(f"주간시간: {prefs.get('available_hours_per_week')}")
    print(f"보고시간: {avail.get('report_time')}")
