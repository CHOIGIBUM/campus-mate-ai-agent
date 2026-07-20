# Campus Mate — 오케스트레이션 워크플로

## 1. 실행 모드

| 모드 | 실행 범위 | 외부 쓰기 |
|---|---|---:|
| `status` | 설정·계약·산출물 확인 | 없음 |
| `onboard` | 프로필 생성·수정 | 로컬 프로필 |
| `demo` | fixture 기반 전체 흐름 | 기본 JSON |
| `daily` | 수집 → 파싱 → 추천 → Notion | 설정 시 Notion |
| `brief` | Slack 브리핑 | 설정 시 Slack |
| `accept-sync` | Accept 조회 → Calendar 결과 반영 | Calendar·Notion |
| `partial:<phase>` | 지정 단계와 필요한 후속 단계 | 단계별 |

외부 쓰기 권한이 명시되지 않은 대화형 실행은 dry-run으로 처리합니다.

## 2. 실행 디렉터리

```text
_workspace/runs/<timestamp>-<mode>/
├── manifest.json
├── 00_input/
├── 01_profile/
├── 02_collection/
├── 03_parsing/
├── 04_recommendation/
├── 05_notion/
├── 06_notification/
├── 07_calendar/
├── 08_qa/
└── handoffs/
```

## 3. 인계 계약

```json
{
  "status": "PASS",
  "agent": "multipass-parser",
  "inputs": ["02_collection/source-pages.json"],
  "outputs": ["03_parsing/opportunities.json"],
  "metrics": {"parsed": 8, "needs_review": 1},
  "warnings": [],
  "errors": [],
  "next": "fit-priority"
}
```

- `PASS` — 다음 단계 실행 가능
- `NEEDS_REVIEW` — 결과 저장 가능, 자동 일정 생성 불가
- `FAIL` — 후속 단계 실행 중단

## 4. 단계별 절차

### 단계 0 — 준비

1. 실행 모드를 결정합니다.
2. 관련 계약 문서를 읽습니다.
3. run 디렉터리와 manifest를 생성합니다.
4. 프로필, backend, 선택 기능, 인증정보의 존재 여부를 확인합니다.
5. 외부 쓰기 허용 범위를 기록합니다.

다음 조건에서는 실행을 중단합니다.

- 필요한 인증정보 없음
- 허용되지 않은 소스 요청
- Notion 전체 삭제·재생성 요청
- 실제 인증정보가 입력 파일이나 로그에서 감지됨

### 단계 1 — 프로필

담당: `profile-manager`

1. 기존 프로필을 읽습니다.
2. 누락 또는 변경 필드만 수집합니다.
3. `UserProfile`로 검증합니다.
4. 프로필과 실행 snapshot을 저장합니다.
5. 검색어 목록을 생성합니다.

통과 조건: 필수 필드 존재, 임의 생성값 없음.

### 단계 2 — 수집

담당: `source-collector`

1. `linkareer` 어댑터를 확인합니다.
2. 최대 수집 개수와 timeout을 적용합니다.
3. URL을 정규화하고 중복을 제거합니다.
4. 상세 페이지를 조회합니다.
5. 항목별 성공·실패를 저장합니다.

통과 조건: `collection-result.json` 생성.

### 단계 3 — 파싱

담당: `multipass-parser`

1. JSON-LD, Next.js 상태, 화면 HTML을 파싱합니다.
2. 핵심 필드 누락·충돌을 확인합니다.
3. 조건을 만족할 때만 OCR·Vision을 실행합니다.
4. 필드별 근거와 신뢰도를 병합합니다.
5. 핵심 충돌은 `NeedsReview`로 설정합니다.

통과 조건: 제목, 원문 URL, 안정적인 ID, 검토 상태 존재.

### 단계 4 — 추천

담당: `fit-priority`

1. 프로필 검색어를 생성합니다.
2. 항목별 점수와 총점을 계산합니다.
3. 마감 우선순위를 계산합니다.
4. 추천 이유를 생성합니다.
5. 파싱·자격 불확실성을 유지합니다.

통과 조건: 총점 0–100, 세부 점수 합 일치, 근거 기반 추천 이유 존재.

### 단계 5 — Notion

담당: `notion-dashboard`

1. 필요한 schema만 보완합니다.
2. 안정적인 ID 또는 URL로 upsert합니다.
3. 사용자 상태·메모·event ID를 보존합니다.
4. free/busy 입력이 있으면 충돌 상태를 반영합니다.
5. page ID와 오류 상태를 저장합니다.

통과 조건: 재실행 시 동일 page ID와 사용자 상태 유지.

### 단계 6 — Slack

담당: `schedule-notification`

1. `Recommended` 공고를 조회합니다.
2. 우선순위, 점수, 마감일로 정렬합니다.
3. Slack payload를 생성합니다.
4. dry-run 또는 실제 전송을 실행합니다.

통과 조건: payload에 token과 비공개 프로필 필드 없음.

### 단계 7 — Calendar

담당: `schedule-notification`

1. `Accept` 공고를 조회합니다.
2. 일정 요청을 생성합니다.
3. `request_id`와 `idempotency_key`를 부여합니다.
4. Timely/Composio 결과를 `request_id`로 연결합니다.
5. 성공 event ID를 저장합니다.
6. 성공 항목만 `Scheduled`로 변경합니다.
7. 실패 항목은 `CalendarError`로 유지합니다.

통과 조건: 비승인 공고 요청 0건, 결과 없는 `Scheduled` 0건.

### 단계 8 — QA

사용 Skill: `qa-audit`

- 산출물과 인계 객체 검증
- 상태 규칙 검증
- 중복 저장·일정 검증
- 필요 시 테스트·lint·compile·secret scan 실행
- `08_qa/qa-result.json` 생성

## 5. Timely 자동화

```text
08:00 daily-collector
  source-collector
  → multipass-parser
  → fit-priority
  → notion-dashboard

09:00 slack-briefing
  schedule-notification / Slack

매시 정각 accept-sync
  notion-dashboard 조회
  → schedule-notification / Calendar
```

## 6. 부분 재실행

- 프로필 변경 → 추천부터 재실행
- 파서 변경 → 영향 URL 파싱부터 재실행
- 점수 규칙 변경 → 추천부터 재실행
- Slack 형식 변경 → 브리핑만 재실행
- Calendar 실패 → 실패 요청만 재실행
- `Hold`·`Reject` → Calendar 단계 제외

## 7. 오류 처리

| 상황 | 처리 |
|---|---|
| URL 조회 실패 | 해당 항목 실패 저장, 나머지 계속 |
| OCR·Vision 실행 불가 | 해당 pass를 `SKIPPED`로 기록, 값 추론 금지 |
| 핵심 필드 충돌 | `NeedsReview`, Calendar 차단 |
| Notion 오류 | 로컬 산출물 보존, 제한된 retry |
| Slack 오류 | payload 보존 |
| Calendar 일부 실패 | 성공 ID 보존, 실패 요청만 재시도 |
| 인증정보 감지 | 외부 쓰기와 커밋 중단 |

## 8. 실행 결과 계약

`manifest.json`과 `08_qa/qa-result.json`에 다음 항목을 저장합니다.

- run ID와 실행 모드
- 호출 Agent
- 단계별 처리 건수
- Notion·Slack·Calendar 결과
- QA 상태
- warnings, errors, 산출물 경로
