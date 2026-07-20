---
name: campus-mate-orchestrator
description: >-
  Campus Mate 전체 Harness의 메인 진입점. 온보딩, 수집, 멀티패스 파싱, 추천, Notion 동기화, Slack 브리핑, Accept→Calendar 반영, 일부 단계 재실행과 QA를 6개 기능 Agent로 조율한다. Timely의 daily-collector·slack-briefing·accept-sync는 이 Skill의 실행 모드를 일정에 따라 호출한다.
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

# Campus Mate 오케스트레이터

이 Skill은 메인 대화에서 실행됩니다. 전문 Agent는 맡은 범위만 처리하고, 메인 Orchestrator가 실행 순서와 단계 간 인계를 관리합니다.

## 실행 모드 선택

- `status` — 설정, 계약 문서, 최근 산출물을 확인합니다. 외부 서비스에는 쓰지 않습니다.
- `onboard` — 사용자 프로필을 새로 만들거나 수정합니다.
- `demo` — 기본적으로 fixture를 사용하며, 명시적으로 허용된 경우에만 live 환경을 사용합니다.
- `daily` — 공고 수집부터 Notion 반영까지 실행합니다.
- `brief` — Slack 브리핑만 생성하거나 전송합니다.
- `accept-sync` — Notion `Accept` 항목만 Calendar에 반영합니다.
- `partial:<phase>` — 지정한 단계와 필요한 후속 단계만 다시 실행합니다.

요청이 모호하면 `status` 또는 dry-run을 선택합니다.

## 단계 0 — 컨텍스트와 실행 준비

1. `CLAUDE.md`, `spec.md`, `workflow.md`, `role-table.md`를 읽습니다.
2. `_workspace/runs/<timestamp>-<mode>/`와 `manifest.json`을 만듭니다.
3. 저장 backend, 프로필, 선택적 OCR·Vision, 외부 인증정보의 **존재 여부만** 확인합니다.
4. 명시적으로 허용되지 않은 외부 쓰기는 실행하지 않습니다.

## 단계 1 — Profile Manager

호출 조건: 프로필이 없거나 사용자가 추천 기준을 변경한 경우

- `profile-manager`가 누락된 값만 질문하고 `profile-build` 계약으로 검증합니다.
- 결과가 `PASS`가 아니면 추천 단계로 진행하지 않습니다.
- fixture 시연에서는 `examples/profile.example.json`을 사용할 수 있습니다.

## 단계 2 — Source Collector

호출 조건: `daily`, live 시연, 수집 단계 재실행

- 실제 운영용 어댑터가 구현되어 있는지 확인합니다.
- 현재 완전 지원 소스는 Linkareer입니다.
- 발견 건수, 중복 제거 건수, 상세 페이지 조회 실패를 각각 기록합니다.

## 단계 3 — Multi-pass Parser

- HTML 계열 근거를 먼저 추출합니다.
- 누락된 핵심 필드에만 OCR·Vision을 선택적으로 실행합니다.
- 상충하는 값은 추측하지 않고 `NeedsReview`로 보냅니다.
- `NeedsReview` 항목은 저장하고 표시할 수 있지만 자동 일정 생성은 금지합니다.

## 단계 4 — Fit & Priority

- `fit-priority`가 `recommendation-rank` 계약을 적용합니다.
- 항목별 점수, 우선순위, 추천 이유를 확인합니다.
- 점수를 수상·선발 가능성으로 표현하지 않습니다.

## 단계 5 — Notion Dashboard

- 외부 쓰기가 허용되면 schema 확인과 비파괴 upsert를 수행합니다.
- dry-run 또는 fixture 모드에서는 JSON 저장소를 사용합니다.
- 사용자 상태와 수동 메모가 보존되었는지 확인합니다.

## 단계 6 — 일정과 알림

### Slack 브리핑

- `schedule-notification`이 Slack payload를 만듭니다.
- 대화형 실행은 기본적으로 dry-run입니다.
- Timely의 `slack-briefing` 자동화는 설정된 채널로 실제 전송할 수 있습니다.

### 일정 충돌

- 정규화된 free/busy 입력이 있으면 `calendar-sync`의 충돌 확인 단계만 실행합니다.
- 입력이 없으면 충돌 상태를 `미확인`으로 유지합니다.

## 단계 7 — Accept 동기화

- `schedule-notification`이 `Accept` 항목만 대상으로 일정 요청 목록을 만듭니다.
- 커넥터 결과가 없으면 결과 반영 단계를 실행하지 않습니다.
- 결과가 있으면 `request_id`별로 반영하고 성공한 event ID를 보존합니다.

## 단계 8 — QA

`qa-audit`를 실행해 다음을 확인합니다.

- 산출물과 Agent 인계 결과의 완전성
- 공고 상태 규칙
- 중복 저장·중복 일정 방지
- 필요 시 테스트, Harness 검증, lint, compile, secret scan

## Fixture 시연

```bash
mkdir -p data artifacts
cp examples/profile.example.json data/user_profile.json
CAMPUS_MATE_STORAGE_BACKEND=json \
  campus-mate demo \
  --fixture examples/fixtures/linkareer_detail.html \
  --output artifacts/demo-result.json
campus-mate list
```

확인 항목:

- 제목, 마감일, 근거가 구조화되었는지
- 점수, 우선순위, 추천 이유가 존재하는지
- 상태가 `Recommended` 또는 `NeedsReview`인지
- 같은 작업을 다시 실행해도 중복 항목이 생기지 않는지

## Agent 호출에 포함할 정보

각 Agent를 호출할 때 다음 항목을 반드시 전달합니다.

- run ID와 실행 모드
- 정확한 입력 경로 또는 식별자
- 예상 출력 경로
- 적용할 Skill 계약
- 외부 쓰기 허용 여부
- 필요한 인계 결과 형식

## 오류 처리 기준

| 상황 | 처리 |
|---|---|
| 프로필 없음 | `profile-manager`로 돌아감 |
| 한 URL 조회 실패 | 다른 항목은 계속 처리하고 실패 기록 |
| OCR·Vision 사용 불가 | 생략 경고를 남기고 값을 추측하지 않음 |
| 핵심 필드 충돌 | `NeedsReview`; 자동 일정화 차단 |
| Notion 실패 | 산출물 보존, 파괴적 재시도 금지 |
| Slack 실패 | dry-run payload 보존 |
| Calendar 일부 실패 | 성공 ID 보존, 실패 요청만 재시도 |
| 인증정보 감지 | 외부 쓰기와 커밋 차단 |

## 완료 보고

- 실행 모드와 run ID
- 호출한 Agent
- 발견, 파싱, 추천, 검토 필요, 실패 건수
- Notion 결과
- Slack 결과
- Calendar 결과
- QA 상태
- 경고와 산출물 경로

## 관련 자료

- [실행 모드 설명](references/run-modes.md)
- [Agent 인계 예시](templates/handoff-template.json)
- 루트의 `workflow.md`, `spec.md`, `role-table.md`
