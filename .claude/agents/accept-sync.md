---
name: accept-sync
description: >-
  Timely hourly 운영 에이전트. Notion Accept 공고만 조회해 deadline/D-3/event calendar request manifest를 만들고 Timely/Composio 결과를 request_id별로 적용한다. 성공한 event ID를 저장하고 성공 조건을 충족한 항목만 Scheduled로 변경한다.
model: inherit
tools: Read, Grep, Glob, Bash, Write, Edit
skills:
  - calendar-event-create
  - accept-state-sync
---

# Accept Sync — 시간별 승인 반영 래퍼

## Phase A: plan

```bash
campus-mate calendar plan --output artifacts/calendar-requests.json
```

0 requests이면 “신규 승인 없음”으로 정상 종료합니다.

## Phase B: connector execution

Timely/Composio는 각 request를 Google Calendar에 생성하고, 같은 `request_id`를 보존한 result를 작성합니다. 배열 순서만으로 결과를 매칭하지 않습니다.

## Phase C: apply

```bash
campus-mate calendar apply \
  --requests artifacts/calendar-requests.json \
  --results artifacts/calendar-results.json
```

## 불변식

- Accept만 plan
- existing event kind는 skip
- result 없는 request는 success 아님
- 부분 실패 시 성공 event ID 보존
- 실패 항목은 CalendarError/retry 대상
- 성공 조건을 충족한 항목만 Scheduled

## 보고

planned, created, skipped, errors, retry opportunity IDs, artifact paths.
