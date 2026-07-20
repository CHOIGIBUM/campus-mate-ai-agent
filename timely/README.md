# Timely 자동화 매핑

Timely는 `.claude/`의 Agent·Skill 계약에 따라 Python CLI와 외부 커넥터를 실행합니다.

## 자동화

```text
08:00 daily-collector
  campus-mate collect
  [선택] Google Calendar free/busy 조회
  [선택] campus-mate conflicts apply

09:00 slack-briefing
  campus-mate brief

매시 정각 accept-sync
  campus-mate calendar plan
  Timely/Composio Google Calendar 생성
  campus-mate calendar apply
```

## 구성

- `.claude/` — Agent·Skill 계약
- `src/campus_mate/` — Python 실행 코드
- `timely/automations.yaml` — 일정·명령·커넥터 인계

인증정보는 Timely Secrets에서 주입합니다.
