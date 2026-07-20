---
name: accept-state-sync
description: >-
  Opportunity 상태 전이 규칙을 검증하고 Notion 사용자 선택을 보존하며 Calendar 결과에 따라 Scheduling/Scheduled/CalendarError를 적용한다.
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

# Accept State Sync

## Allowed transitions

```text
Recommended → Accept | Hold | Reject
Accept → Scheduling → Scheduled
Accept/Scheduling → CalendarError
CalendarError → Scheduling → Scheduled
```

Routine collection must not move user states backward.

## Rules

- Slack message is not approval.
- Missing calendar result cannot produce Scheduled.
- Preserve successful event IDs during retry.
- A rejected/held item must not be planned.

Implementation is shared between Notion repository and calendar result applier.
