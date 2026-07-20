---
name: campus-mate-orchestrator
description: >-
  Campus Mate의 온보딩, 수집, 멀티패스 파싱, 추천, Notion, Slack, Calendar, QA를 6개 기능 Agent로 조율한다.
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

## 실행 모드

- `status` — 설정·계약·최근 산출물 확인
- `onboard` — 프로필 생성·수정
- `demo` — fixture 기반 전체 실행
- `daily` — 수집부터 Notion까지 실행
- `brief` — Slack 브리핑
- `accept-sync` — Accept 공고 Calendar 동기화
- `partial:<phase>` — 지정 단계와 후속 단계 재실행

## 공통 준비

1. `CLAUDE.md`, `spec.md`, `workflow.md`, `role-table.md`를 읽습니다.
2. `_workspace/runs/<timestamp>-<mode>/`와 `manifest.json`을 생성합니다.
3. 입력 경로, backend, 선택 기능, 인증정보 존재 여부를 확인합니다.
4. 외부 쓰기 허용 범위를 manifest에 기록합니다.

## 실행 순서

### 1. 프로필

호출: `profile-manager`

- 프로필이 없거나 변경 요청이 있을 때 실행합니다.
- `PASS`가 아니면 추천 단계로 진행하지 않습니다.

### 2. 수집

호출: `source-collector`

- `daily`, live 실행, 수집 단계 재실행에서 호출합니다.
- 허용 어댑터는 `linkareer`입니다.

### 3. 파싱

호출: `multipass-parser`

- HTML 계열 출처를 우선합니다.
- 조건을 만족할 때만 OCR·Vision을 호출합니다.
- 핵심 충돌은 `NeedsReview`로 설정합니다.

### 4. 추천

호출: `fit-priority`

- 점수, 세부 점수, 우선순위, 추천 이유를 생성합니다.
- 적합도를 수상·선발 확률로 표현하지 않습니다.

### 5. Notion

호출: `notion-dashboard`

- 외부 쓰기 허용 시 Notion upsert를 실행합니다.
- fixture와 dry-run은 JSON 저장소를 사용합니다.

### 6. Slack·충돌 확인

호출: `schedule-notification`

- `brief`는 Slack payload를 생성하거나 전송합니다.
- free/busy 입력이 있으면 충돌 상태를 반영합니다.

### 7. Calendar

호출: `schedule-notification`

- `Accept` 공고만 일정 요청을 생성합니다.
- connector 결과가 있을 때만 결과 반영을 실행합니다.

### 8. QA

호출: `qa-audit`

- 산출물·인계·상태·중복·보안 규칙을 검증합니다.
- `08_qa/qa-result.json`을 생성합니다.

## Agent 호출 입력

- run ID
- 실행 모드
- 입력 경로 또는 식별자
- 출력 경로
- 적용 Skill
- 외부 쓰기 허용 범위
- 인계 객체 형식

## 오류 처리

| 상황 | 처리 |
|---|---|
| 프로필 없음 | `profile-manager` 실행 |
| URL 조회 실패 | 해당 항목 실패 저장, 나머지 계속 |
| OCR·Vision 실행 불가 | pass를 `SKIPPED`로 기록 |
| 핵심 필드 충돌 | `NeedsReview`, Calendar 차단 |
| Notion 오류 | 산출물 보존, 제한된 retry |
| Slack 오류 | payload 보존 |
| Calendar 일부 실패 | 성공 ID 보존, 실패 요청만 재시도 |
| 인증정보 감지 | 외부 쓰기와 커밋 중단 |

## Fixture 실행

```bash
mkdir -p data artifacts
cp examples/profile.example.json data/user_profile.json
CAMPUS_MATE_STORAGE_BACKEND=json \
  campus-mate demo \
  --fixture examples/fixtures/linkareer_detail.html \
  --output artifacts/demo-result.json
campus-mate list
```

검증 항목:

- 필드와 근거 생성
- 점수·우선순위·추천 이유 생성
- `Recommended` 또는 `NeedsReview` 상태
- 재실행 중복 없음

## 관련 문서

- [실행 모드](references/run-modes.md)
- [인계 예시](templates/handoff-template.json)
- `workflow.md`
- `spec.md`
- `role-table.md`
