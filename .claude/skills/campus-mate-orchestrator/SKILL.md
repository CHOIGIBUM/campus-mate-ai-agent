---
name: campus-mate-orchestrator
description: >-
  Campus Mate 전체 하네스의 메인 진입점. 온보딩, 일일 수집, 멀티패스 파싱, 적합도 추천, Notion 동기화, Slack 브리핑, Accept→Google Calendar 반영, 부분 재실행과 오류 복구를 6개 기능 에이전트와 3개 운영 에이전트로 조율한다.
argument-hint: "[onboard|demo|daily|brief|accept-sync|status|partial:<phase>]"
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

# Campus Mate Orchestrator — code-backed agent workflow

이 스킬은 메인 대화 컨텍스트에서 실행됩니다. Custom subagent는 다른 subagent를 중첩 생성하지 않으므로, 이 스킬이 각 에이전트를 순서대로 호출하고 handoff를 수집합니다.

## 요청 해석

`$ARGUMENTS`와 사용자 문맥을 읽어 mode를 선택합니다.

- `onboard` — 프로필 생성/수정
- `demo` — fixture 또는 live 시연
- `daily` — 수집부터 Notion까지
- `brief` — Slack 브리핑만
- `accept-sync` — Calendar 승인 반영만
- `status` — 설정/산출물/상태 점검
- `partial:<phase>` — 해당 단계와 필요한 downstream만 재실행

명확하지 않으면 외부 write를 하지 않는 `status` 또는 dry-run으로 시작합니다.

## Phase 0 — 컨텍스트와 run 생성

1. `CLAUDE.md`, `spec.md`, `workflow.md`, `role-table.md`를 읽습니다.
2. `_workspace/runs/<timestamp>-<mode>/`를 만들고 `manifest.json`을 작성합니다.
3. storage backend, profile, optional OCR/Vision, external credentials의 존재 여부만 확인합니다. 비밀값 자체를 출력하지 않습니다.
4. 외부 write 여부를 판정합니다. interactive session에서 Slack/Notion/Calendar write가 명시되지 않았다면 dry-run을 우선합니다.

## Phase 1 — Profile Manager

호출 조건: profile이 없거나 사용자가 추천 기준을 변경했습니다.

- `profile-manager`에게 현재 profile path와 사용자 요청을 전달합니다.
- `PASS`가 아니면 recommendation을 시작하지 않습니다.
- profile snapshot과 handoff를 workspace에 저장합니다.

## Phase 2 — Source Collector

호출 조건: `daily`, `demo live`, 또는 collection partial rerun.

- 현재 production source는 Linkareer임을 명시합니다.
- `source-collector`가 limit, URL, 실패 격리를 검증합니다.
- integrated CLI를 사용할 때에도 collection report를 별도 artifact로 남깁니다.

## Phase 3 — Multi-pass Parser

- `multipass-parser`에 source pages/URLs와 optional-pass 설정을 전달합니다.
- HTML evidence를 우선하고 OCR/Vision skipped 여부를 기록합니다.
- `NeedsReview` 항목은 downstream 저장/표시는 가능하지만 자동 scheduling은 금지합니다.

## Phase 4 — Fit & Priority

- `fit-priority`에 validated profile과 parsed opportunities를 전달합니다.
- score breakdown, priority, reasons를 검증합니다.
- 점수를 합격 가능성으로 서술하지 않습니다.

## Phase 5 — Notion Dashboard

- external write가 허용되면 `notion-dashboard`로 schema/upsert를 수행합니다.
- dry-run/local mode이면 JSON repository에 기록하고 외부 write를 생략했다고 보고합니다.
- user state preservation을 확인합니다.

## Phase 6 — Schedule & Notification

### Briefing

- `schedule-notification` 또는 운영 agent `slack-briefing`으로 payload를 만듭니다.
- interactive session은 기본 dry-run, scheduled Timely는 configured delivery.

### Conflict

- Timely free/busy JSON이 있으면 적용합니다.
- 없으면 “미확인”으로 유지합니다.

## Phase 7 — Accept Sync

- 운영 agent `accept-sync`가 Accept-only manifest를 만듭니다.
- Timely connector 결과가 없으면 apply를 실행하지 않습니다.
- 결과가 있으면 request_id별 적용 후 상태를 검증합니다.

## Phase 8 — QA

`qa-audit` skill을 실행합니다.

- artifact/handoff completeness
- state invariants
- duplicate prevention
- tests/harness validator/secret scan as needed

`07_qa/qa-report.md`가 PASS 또는 명시된 제한이 있는 PASS-WITH-WARNINGS 상태여야 run을 완료합니다.

## Agent 호출 규칙

각 Agent 호출 prompt에는 반드시 포함합니다:

- run ID와 mode
- exact input paths
- expected output paths
- relevant contract/skill
- external-write permission
- completion handoff schema

Agent가 산출물 없이 요약만 반환하면 handoff 미완료로 간주하고 구체 경로를 요청합니다.

## 데이터 흐름

```text
profile.json
   ↓
URLs/pages → parse evidence → Opportunity
   ↓
Recommendation(score/priority/reasons)
   ↓
Notion page + status
   ├→ Slack briefing
   └→ Accept → calendar requests → connector results → Scheduled
```

## 에러 처리

| 상황 | 조치 |
|---|---|
| profile missing | profile-manager로 되돌림 |
| one URL fails | 나머지 계속, item failure 기록 |
| OCR/Vision unavailable | pass skipped, 추측 금지 |
| core field conflict | NeedsReview, scheduling 차단 |
| Notion failure | artifact 보존, destructive retry 금지 |
| Slack failure | dry-run payload 보존 |
| Calendar partial failure | successful IDs 보존, failed request만 retry |
| secret detected | write/commit 중단 |

## 후속 작업

- “프로필만 수정” → Phase 1, 4–6
- “파싱만 다시” → Phase 3–5, 필요 시 6
- “점수 기준 변경” → Phase 4–6
- “브리핑 다시” → Phase 6 only
- “승인 반영” → Phase 7 only
- “시연 상태 확인” → status mode, no external write

## 완료 보고 형식

- mode/run ID
- agents invoked
- counts: discovered/parsed/recommended/review/failures
- Notion result
- Slack result
- Calendar result
- QA status
- warnings
- artifact paths

## Additional resources

- [run-modes.md](references/run-modes.md)
- [handoff-template.json](templates/handoff-template.json)
- Root `workflow.md` and `spec.md`
