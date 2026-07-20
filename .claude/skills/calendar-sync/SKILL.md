---
name: calendar-sync
description: >-
  free/busy 충돌 상태를 반영하고 Accept 공고의 중복 방지 일정 요청을 생성한 뒤 connector 결과를 적용한다.
user-invocable: false
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - Edit
---

# Calendar 동기화

[Calendar 커넥터 계약](references/calendar-contract.md)을 적용합니다.

## A. 충돌 상태

입력:

```json
{
  "busy": [
    {
      "start": "2026-09-30T09:30:00+09:00",
      "end": "2026-09-30T10:30:00+09:00"
    }
  ]
}
```

명령:

```bash
campus-mate conflicts apply --input examples/integrations/freebusy.example.json
```

규칙:

- 시간대 포함 필수
- 입력 없음: `미확인`
- 충돌 있음: 상태만 표시, 자동 거절 금지

## B. 일정 요청 생성

```bash
campus-mate calendar plan --output artifacts/calendar-requests.json
```

규칙:

- `Accept` 공고만 대상
- 일정 종류: `deadline`, `preparation`, `event`
- 기존 event ID가 있는 일정 종류 제외
- `request_id`, `idempotency_key` 필수
- 요청 생성 후 상태: `Scheduling`

## C. Connector 결과

```json
{
  "request_id": "...",
  "success": true,
  "event_id": "google-event-id",
  "error": ""
}
```

## D. 결과 반영

```bash
campus-mate calendar apply \
  --requests artifacts/calendar-requests.json \
  --results artifacts/calendar-results.json
```

규칙:

- 성공 결과가 있는 일정만 event ID 저장
- 필요한 일정이 성공한 공고만 `Scheduled`
- 실패 공고는 `CalendarError`
- 재시도 시 성공 event ID 유지
- 실패 또는 결과 누락 요청만 재시도

## 품질 기준

- 비승인 공고 요청 0건
- 중복 요청·일정 0건
- 결과 없는 `Scheduled` 0건

## 구현·검증

- `src/campus_mate/workflows/conflicts.py`
- `src/campus_mate/workflows/accept_sync.py`
- `src/campus_mate/integrations/calendar_bridge.py`
- `tests/test_conflicts.py`
- `tests/test_calendar_bridge.py`
