---
name: calendar-sync
description: >-
  Google Calendar free/busy 결과를 공고 충돌 상태에 반영하고, Notion Accept 항목에서 중복 방지 일정 요청을 생성하며, Timely/Composio 결과를 request_id별로 적용해 Scheduling·Scheduled·CalendarError 상태를 안전하게 관리한다.
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

먼저 [Calendar 커넥터 계약](references/calendar-contract.md)을 읽습니다.

## A. Free/busy 기반 충돌 상태

정규화된 입력 형식:

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

- 날짜·시간에는 시간대 정보가 있어야 합니다.
- free/busy 입력이 없으면 충돌 상태를 `없음`이 아니라 `미확인`으로 둡니다.
- 일정 충돌이 있다고 해서 공고를 자동으로 거절하지 않습니다.

## B. Accept 항목 일정 요청 생성

```bash
campus-mate calendar plan --output artifacts/calendar-requests.json
```

규칙:

- `Accept` 상태의 공고만 대상입니다.
- 일정 종류는 `deadline`, `preparation`, `event`입니다.
- 이미 event ID가 있는 일정 종류는 건너뜁니다.
- 안정적인 `request_id`와 `idempotency_key`가 필요합니다.
- 계획 단계에서는 `Scheduled`가 아니라 `Scheduling`으로 변경합니다.

## C. Timely/Composio 커넥터

Timely는 각 요청을 읽고 다음 형식으로 결과를 반환합니다.

```json
{
  "request_id": "...",
  "success": true,
  "event_id": "google-event-id",
  "error": ""
}
```

커넥터 결과는 반드시 원래 `request_id`와 연결되어야 합니다.

## D. 결과 반영

```bash
campus-mate calendar apply \
  --requests artifacts/calendar-requests.json \
  --results artifacts/calendar-results.json
```

허용되는 상태 흐름:

```text
Recommended → Accept | Hold | Reject
Accept → Scheduling → Scheduled
Accept/Scheduling → CalendarError
CalendarError → Scheduling → Scheduled
```

규칙:

- 결과가 없는 요청을 `Scheduled`로 바꾸지 않습니다.
- 재시도 중에도 성공한 event ID를 보존합니다.
- 일부 성공 결과는 일정별로 반영합니다.
- 실패 요청은 다시 시도할 수 있는 상태로 남깁니다.
- 정기 수집이 사용자 상태를 이전 단계로 되돌리지 않습니다.

## 품질 기준

- `Accept`가 아닌 공고의 Calendar 요청: 0건
- 중복 요청 또는 중복 일정: 0건
- `Scheduled` 변경 전 확인된 성공 결과 필수
- 재시도 목록에는 실패했거나 결과가 누락된 요청만 포함

## 구현

- `src/campus_mate/workflows/conflicts.py`
- `src/campus_mate/workflows/accept_sync.py`
- `src/campus_mate/integrations/calendar_bridge.py`
- `tests/test_conflicts.py`
- `tests/test_calendar_bridge.py`
