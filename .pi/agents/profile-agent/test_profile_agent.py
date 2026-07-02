from __future__ import annotations

import importlib.util
import json
from datetime import datetime
from pathlib import Path

AGENT_DIR = Path(__file__).parent
SKILL_PATH = AGENT_DIR.parent.parent / "skills" / "profile-build" / "profile_build.py"

spec = importlib.util.spec_from_file_location("profile_build", SKILL_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
ProfileBuildSkill = module.ProfileBuildSkill


def run_tests() -> None:
    skill = ProfileBuildSkill()
    results = []

    # test 1 new profile
    email1 = f"test1_{datetime.now().timestamp()}@example.com"
    user_id1 = "user_20260702_001"
    data1 = {
        "name": "최기범",
        "email": email1,
        "school": "강원대학교",
        "major": "AI융합학과",
        "year": "2학년",
        "interests": ["의료AI", "데이터 분석"],
        "positions": ["AI 개발자"],
        "activity_types": ["해커톤"],
        "regions": ["온라인"],
        "available_hours_per_week": 5,
        "report_time": "08:00",
    }
    s1, _, p1 = skill.execute(data1, user_id1)
    results.append(("신규 프로필 생성", s1 and p1 and p1["metadata"]["version"] == 1))

    # test 2 update profile
    data2 = dict(data1)
    data2["year"] = "3학년"
    data2["interests"] = ["의료AI", "데이터 분석", "AI Agent"]
    s2, _, p2 = skill.execute(data2, user_id1)
    results.append(("기존 프로필 수정", s2 and p2 and p2["metadata"]["version"] == 2 and p2["basic_info"]["year"] == "3학년"))

    # test 3 validation
    s3, _, _ = skill.execute({"name": "A"}, "user_20260702_002")
    results.append(("검증 에러 처리", not s3))

    # test 4 file stored
    file_path = Path("./data/profiles") / f"user_profile_{user_id1}.json"
    ok4 = file_path.exists()
    if ok4:
        with file_path.open("r", encoding="utf-8") as f:
            loaded = json.load(f)
        ok4 = loaded["user_id"] == user_id1
    results.append(("파일 저장", ok4))

    passed = 0
    for name, ok in results:
        print(f"{'✅ PASS' if ok else '❌ FAIL'} | {name}")
        passed += int(ok)
    print(f"총 {passed}/{len(results)} 통과")
    assert passed == len(results), "일부 테스트 실패"


if __name__ == "__main__":
    run_tests()
