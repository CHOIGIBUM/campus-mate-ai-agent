---
name: campus-mate-onboarding
description: >-
  Campus Mate 사용자 온보딩을 대화형으로 수행한다. 기존 프로필을 읽고 필수 누락값만 질문한 뒤 검증된 JSON으로 저장하고 추천 기준을 요약한다.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - Edit
  - Agent
  - Skill
---

# Campus Mate Onboarding

## Procedure

1. `data/user_profile.json`이 있으면 읽고 사용자에게 현재 값을 요약합니다.
2. 학교, 학년, 전공, 관심 분야 중 누락된 항목만 질문합니다.
3. 선택 항목은 필요할 때만 요청합니다: 활동 유형, 희망 직무, 키워드, 지역, 가능한 시간.
4. 쉼표 입력은 리스트로 변환하고 중복을 제거합니다.
5. 사용자 응답을 JSON으로 작성한 뒤 다음으로 검증합니다:

```bash
campus-mate profile import --file <profile.json>
```

6. `campus-mate profile show`로 최종값을 확인합니다.
7. 사용자에게 저장된 기준과 향후 추천에 쓰이는 검색어를 보여줍니다.

## Constraints

- 임의 기본값 금지
- 주민번호, 전화번호 등 불필요한 개인정보 수집 금지
- profile 수정 시 변경되지 않은 필드 유지

## Output

- `data/user_profile.json`
- profile summary
- downstream rerun recommendation
