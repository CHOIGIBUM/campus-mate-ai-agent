---
name: campus-mate-orchestrator
description: >-
  Campus Mate 전체 Harness의 메인 진입점. 온보딩, 수집, 멀티패스 파싱, 추천, Notion 동기화, Slack 브리핑, Accept→Calendar 반영, 부분 재실행과 QA를 6개 기능 Agent로 조율한다. Timely의 daily-collector·slack-briefing·accept-sync는 이 Skill의 실행 모드를 스케줄링한다.
argument-hint: "[status|onboard|demo|daily|brief|accept-sync|partial:<phase>]"
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

# Campus Mate Orchestrator

이 Skill은 메인 대화 컨텍스트에서 실행됩니다. 전문 Agent는 자신의 범위만 수행하고, 메인 Orchestrator가 순서와 handoff를 관리합니다.

## Mode selection

- `status` — 설정, 계약, 최근 산출물 확인; 외부 write 없음
- `onboard` — 프로필 생성 또는 수정
- `demo` — fixture 기본, 명시적으로 승인된 경우만 live
- `daily` — 수집부터 Notion까지
- `brief` — Slack 브리핑만
- `accept-sync` — Accept 항목 Calendar 반영만
- `partial:<phase>` — 해당 단계와 필요한 downstream만 재실행

요청이 모호하면 `status` 또는 dry-run을 선택합니다.

## Phase 0 — Context and run

1. `CLAUDE.md`, `spec.md`, `workflow.md`, `role-table.md`를 읽습니다.
2. `_workspace/runs/<timestamp>-<mode>/`와 `manifest.json`을 만듭니다.
3. storage backend, profile, optional OCR/Vision, external credential의 **존재 여부만** 확인합니다.
4. 명시되지 않은 외부 write는 실행하지 않습니다.

## Phase 1 — Profile Manager

호출 조건: 프로필이 없거나 사용자가 추천 기준을 변경했습니다.

- `profile-manager`가 누락값만 질문하고 `profile-build` 계약으로 검증합니다.
- `PASS`가 아니면 추천을 시작하지 않습니다.
- fixture demo에서는 `examples/profile.example.json`을 사용할 수 있습니다.

## Phase 2 — Source Collector

호출 조건: `daily`, live demo, collection rerun.

- production adapter가 실제 구현되어 있는지 확인합니다.
- 현재 완전 지원 source는 Linkareer입니다.
- 발견, 중복 제거, fetch 실패를 별도 기록합니다.

## Phase 3 — Multi-pass Parser

- HTML 계열 evidence를 먼저 추출합니다.
- 누락된 핵심 필드에 대해서만 OCR/Vision을 선택 실행합니다.
- 상충값은 추측하지 않고 `NeedsReview`로 보냅니다.
- `NeedsReview` 항목은 저장과 표시가 가능하지만 자동 scheduling은 금지합니다.

## Phase 4 — Fit & Priority

- `fit-priority`가 `recommendation-rank` 계약을 적용합니다.
- score breakdown, priority, reasons를 확인합니다.
- 점수를 합격 가능성으로 표현하지 않습니다.

## Phase 5 — Notion Dashboard

- 외부 write가 허용되면 schema와 비파괴 upsert를 수행합니다.
- dry-run/fixture mode에서는 JSON repository를 사용합니다.
- 사용자 상태와 수동 메모가 보존되었는지 확인합니다.

## Phase 6 — Schedule and notification

### Brief

- `schedule-notification`이 Slack payload를 만듭니다.
- interactive mode는 기본 dry-run입니다.
- Timely `slack-briefing` schedule은 configured delivery를 실행할 수 있습니다.

### Conflict

- normalized free/busy 입력이 있으면 `calendar-sync`의 conflict 단계만 실행합니다.
- 입력이 없으면 `미확인`을 유지합니다.

## Phase 7 — Accept sync

- `schedule-notification`이 Accept-only request manifest를 만듭니다.
- connector 결과가 없으면 apply를 실행하지 않습니다.
- 결과가 있으면 request_id별로 적용하고 성공 event ID를 보존합니다.

## Phase 8 — QA

`qa-audit`를 실행합니다.

- artifact와 handoff completeness
- state invariants
- duplicate prevention
- tests, harness validator, lint, compile, secret scan as needed

## Fixture demo

```bash
mkdir -p data artifacts
cp examples/profile.example.json data/user_profile.json
CAMPUS_MATE_STORAGE_BACKEND=json \
  campus-mate demo \
  --fixture examples/fixtures/linkareer_detail.html \
  --output artifacts/demo-result.json
campus-mate list
```

검증:

- title, deadline, evidence가 구조화됨
- score, priority, reason 존재
- status는 `Recommended` 또는 `NeedsReview`
- repeated run이 duplicate를 만들지 않음

## Agent prompt requirements

각 Agent 호출에는 반드시 포함합니다.

- run ID와 mode
- exact input paths or identifiers
- expected output paths
- relevant Skill contract
- external-write permission
- required handoff schema

## Error policy

| Situation | Action |
|---|---|
| profile missing | return to `profile-manager` |
| one URL fails | continue other items and record failure |
| OCR/Vision unavailable | record skipped pass; never infer |
| core field conflict | `NeedsReview`; block scheduling |
| Notion failure | preserve artifact; no destructive retry |
| Slack failure | preserve dry-run payload |
| Calendar partial failure | preserve successful IDs; retry failures only |
| secret detected | block write/commit |

## Completion report

- mode and run ID
- Agents invoked
- discovered, parsed, recommended, review, and failure counts
- Notion result
- Slack result
- Calendar result
- QA status
- warnings and artifact paths

## Additional resources

- [run-modes.md](references/run-modes.md)
- [handoff-template.json](templates/handoff-template.json)
- Root `workflow.md`, `spec.md`, and `role-table.md`
