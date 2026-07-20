---
name: calendar-freebusy-check
description: >-
  Google Calendar free/busy 결과를 normalized busy intervals로 받아 각 공고 일정과 겹침 여부를 계산하고 Notion/저장소 conflict_status를 갱신한다.
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

# Calendar Free/Busy Check

## Input format

```json
{"busy":[{"start":"2026-09-30T09:30:00+09:00","end":"2026-09-30T10:30:00+09:00"}]}
```

## Command

```bash
campus-mate conflicts apply --input artifacts/freebusy.json
```

## Rules

- Parse timezone-aware datetimes.
- Mark overlap explicitly.
- Missing free/busy data leaves `미확인`, not `없음`.
- Conflict does not automatically reject an opportunity.

## Verify

```bash
python -m pytest tests/test_conflicts.py -q
```
