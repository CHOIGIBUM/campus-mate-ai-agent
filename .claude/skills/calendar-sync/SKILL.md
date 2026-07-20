---
name: calendar-sync
description: >-
  Google Calendar free/busy 결과를 공고 충돌 상태에 반영하고, Notion Accept 항목에서 idempotent 일정 요청을 생성하며, Timely/Composio 결과를 request_id별로 적용해 Scheduling·Scheduled·CalendarError 상태를 안전하게 관리한다.
user-invocable: false
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - Edit
---

# Calendar Sync

Read [calendar-contract.md](references/calendar-contract.md).

## Part A — Free/busy conflict status

Normalized input:

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

Command:

```bash
campus-mate conflicts apply --input examples/integrations/freebusy.example.json
```

Rules:

- datetimes must be timezone-aware
- missing free/busy input leaves `미확인`, not `없음`
- a conflict does not automatically reject an opportunity

## Part B — Accept-only request planning

```bash
campus-mate calendar plan --output artifacts/calendar-requests.json
```

Rules:

- only `Accept` items are eligible
- event kinds: `deadline`, `preparation`, `event`
- existing event kind is skipped
- stable `request_id` and `idempotency_key` are required
- planning moves eligible items to `Scheduling`, not `Scheduled`

## Part C — Timely/Composio connector

Timely reads each request and returns:

```json
{
  "request_id": "...",
  "success": true,
  "event_id": "google-event-id",
  "error": ""
}
```

The connector result must be associated with the original `request_id`.

## Part D — Result application

```bash
campus-mate calendar apply \
  --requests artifacts/calendar-requests.json \
  --results artifacts/calendar-results.json
```

Allowed state flow:

```text
Recommended → Accept | Hold | Reject
Accept → Scheduling → Scheduled
Accept/Scheduling → CalendarError
CalendarError → Scheduling → Scheduled
```

Rules:

- missing result cannot become `Scheduled`
- preserve successful event IDs during retry
- partial success is applied per event
- failed request remains recoverable
- routine collection must not move user states backwards

## Quality gates

- non-Accept calendar requests: 0
- duplicate request/event: 0
- confirmed result required for `Scheduled`
- retry set contains failed or missing requests only

## Implementation

- `src/campus_mate/workflows/conflicts.py`
- `src/campus_mate/workflows/accept_sync.py`
- `src/campus_mate/integrations/calendar_bridge.py`
- `tests/test_conflicts.py`
- `tests/test_calendar_bridge.py`
