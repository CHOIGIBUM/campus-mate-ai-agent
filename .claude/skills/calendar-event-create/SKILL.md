---
name: calendar-event-create
description: >-
  Notion Accept 항목에서 idempotent Google Calendar request manifest를 만들고 Timely/Composio result를 request_id별로 적용한다.
user-invocable: false
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

# Calendar Event Create

Read [calendar-contract.md](references/calendar-contract.md).

## Plan

```bash
campus-mate calendar plan --output artifacts/calendar-requests.json
```

## Connector

Timely creates each request and returns `request_id`, success, event_id, and error.

## Apply

```bash
campus-mate calendar apply \
  --requests artifacts/calendar-requests.json \
  --results artifacts/calendar-results.json
```

## Invariants

- Accept only
- existing event kind skipped
- stable idempotency key
- result matched by request_id
- partial success preserved
- Scheduled only after confirmed success

## Verify

```bash
python -m pytest tests/test_calendar_bridge.py -q
```
