---
name: campus-mate-demo
description: >-
  Campus Mate 데모를 실행한다. fixture 기반 재현 가능한 로컬 데모 또는 명시적으로 승인된 live 연동 데모를 선택하고, 수집→파싱→추천→저장→브리핑→Accept/Calendar 흐름을 검증한다.
argument-hint: "[fixture|live]"
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

# Campus Mate Demo

## Mode selection

- `fixture` (default): external services 없이 JSON backend
- `live`: Notion/Slack/Timely connector 설정이 확인된 경우만

## Fixture demo

```bash
cp examples/profile.example.json data/user_profile.json
CAMPUS_MATE_STORAGE_BACKEND=json \
  campus-mate demo --fixture examples/fixtures/linkareer_detail.html \
  --output artifacts/demo-result.json
campus-mate list
```

검증:

- title/deadline/evidence가 구조화됨
- fit score와 reason 존재
- status는 Recommended 또는 NeedsReview
- repeated run이 duplicate를 만들지 않음

## Live demo

1. profile 확인
2. Notion schema 확인
3. collect 실행
4. Slack dry-run 검수 후 전송
5. 사용자가 Notion에서 Accept
6. calendar plan
7. Timely connector result 생성
8. calendar apply
9. Scheduled와 event IDs 확인

## Safety

`live`라는 명시가 없으면 외부 write를 수행하지 않습니다. 토큰은 출력하지 않습니다.
