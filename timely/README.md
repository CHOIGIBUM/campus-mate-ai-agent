# Timely 실행 매핑

Campus Mate의 기준 Harness는 `.claude/`에 있습니다. Timely는 같은 계약을 일정에 따라 실행하며 Python CLI와 외부 커넥터를 호출합니다.

## 구성별 역할

- `.claude/` — 재사용 가능한 Agent·Skill의 기준 정의
- `src/campus_mate/` — 재현 가능한 실제 실행 코드
- `timely/automations.yaml` — 자동화 일정과 커넥터 인계 기준

## 자동화 일정

```text
08:00 daily-collector
  campus-mate collect
  선택적으로 Google Calendar free/busy 조회
  campus-mate conflicts apply

09:00 slack-briefing
  campus-mate brief

매시 정각 accept-sync
  campus-mate calendar plan
  Timely/Composio Google Calendar 일정 생성
  campus-mate calendar apply
```

인증정보는 Timely Secrets에 저장합니다. Agent와 Skill 정의를 별도의 `.pi/` 폴더에 복제해 서로 다른 버전으로 관리하지 않습니다.
