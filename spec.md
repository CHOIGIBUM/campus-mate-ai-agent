# Campus Mate — 시스템 명세

## 1. 목적

여러 사이트에 분산된 공모전 정보를 수집·구조화하고, 사용자 프로필과 비교해 추천한 뒤 Notion·Slack·Google Calendar로 연결합니다.

## 2. 기능 범위

### 운영 기능

- 사용자 프로필 생성·검증
- Linkareer 목록·상세 페이지 수집
- JSON-LD, Next.js 상태, HTML 파싱
- 필드별 근거·신뢰도·충돌을 유지하는 병합
- 적합도 점수·마감 우선순위·추천 이유 계산
- Notion 비파괴 upsert와 상태 보존
- Slack 추천 브리핑
- `Accept` 공고의 Calendar 요청 생성과 결과 반영
- Timely 정기 자동화
- JSON 저장소 기반 fixture 실행과 자동 테스트

### 선택 기능

- 렌더링 OCR
- 포스터 Vision
- Google Calendar free/busy 충돌 확인

선택 기능은 해당 의존성과 인증정보가 설정된 경우에만 실행합니다.

### 비지원 기능

- 지원서 자동 제출
- 사용자 승인 없는 참가 결정
- `linkareer` 이외 사이트의 운영 수집
- 적합도를 수상·선발 확률로 변환하는 기능

## 3. 구성 요소

| 구성 요소 | 책임 |
|---|---|
| 사용자 | 프로필 입력, 추천 검토, Notion 상태 선택 |
| Orchestrator | 실행 모드 선택, Agent 호출, 단계 인계, 복구 |
| 기능 Agent | 역할별 계약 적용과 결과 검증 |
| Python 실행 계층 | 수집·파싱·추천·저장·외부 서비스 요청 생성 |
| Timely | 정기 실행과 외부 커넥터 호출 |
| Notion | 공고 현황판과 승인 상태 관리 |
| Slack | 추천 브리핑 |
| Google Calendar | 승인 공고의 일정 관리 |

## 4. 기능 요구사항

### 프로필

- **FR-P01** `school`, `grade`, `major`, `interests`를 필수로 수집합니다.
- **FR-P02** 누락값을 임의 기본값으로 채우지 않습니다.
- **FR-P03** 목록형 입력을 정규화하고 중복을 제거합니다.
- **FR-P04** `UserProfile` 검증 후 저장합니다.
- **FR-P05** 추천에 불필요한 민감정보를 수집하지 않습니다.

### 수집

- **FR-C01** 허용된 소스와 최대 수집 개수를 적용합니다.
- **FR-C02** URL을 정규화하고 안정적인 공고 ID를 생성합니다.
- **FR-C03** 항목별 실패를 격리합니다.
- **FR-C04** 발견·성공·실패 수와 실패 원인을 저장합니다.

### 파싱

- **FR-M01** 구조화 데이터와 화면 HTML을 우선 파싱합니다.
- **FR-M02** 필요한 경우에만 OCR·Vision을 호출합니다.
- **FR-M03** 필드별 출처·원문·신뢰도를 저장합니다.
- **FR-M04** 핵심 필드 충돌은 `NeedsReview`로 처리합니다.
- **FR-M05** 확인되지 않은 날짜·자격·혜택을 추론하지 않습니다.
- **FR-M06** 마감일 충돌 항목의 자동 일정 생성을 차단합니다.

### 추천

- **FR-R01** 0–100 범위 점수와 항목별 세부 점수를 생성합니다.
- **FR-R02** 확인된 프로필·공고 필드로 추천 이유를 생성합니다.
- **FR-R03** 적합도와 마감일까지의 기간으로 `긴급`, `중요`, `참고`를 지정합니다.
- **FR-R04** 적합도와 파싱 신뢰도를 분리합니다.

### Notion

- **FR-N01** 기존 페이지를 유지한 채 필요한 속성만 보완합니다.
- **FR-N02** 안정적인 ID 또는 원문 URL로 upsert합니다.
- **FR-N03** 사용자 상태·메모·Calendar event ID를 보존합니다.
- **FR-N04** 파싱 경고와 동기화 오류를 저장합니다.

### Slack

- **FR-S01** 우선순위, 점수, 마감일 순으로 정렬합니다.
- **FR-S02** 제목, 마감일, 점수, 추천 이유, 충돌 상태, 링크를 포함합니다.
- **FR-S03** dry-run과 실제 전송을 분리합니다.
- **FR-S04** Slack 입력을 참가 승인으로 해석하지 않습니다.

### Calendar

- **FR-G01** `Accept` 상태만 일정 계획 대상으로 사용합니다.
- **FR-G02** 일정 종류는 `deadline`, `preparation`, `event`입니다.
- **FR-G03** 각 요청에 `request_id`와 `idempotency_key`를 부여합니다.
- **FR-G04** 성공·실패를 일정 단위로 반영합니다.
- **FR-G05** 성공이 확인된 뒤 `Scheduled`로 변경합니다.
- **FR-G06** 실패 항목은 `CalendarError`로 유지합니다.
- **FR-G07** 재실행 시 이미 생성된 일정 종류를 중복 생성하지 않습니다.

## 5. 공고 상태

```text
New
  ↓ 파싱·추천 완료
Recommended
  ├─ Accept → Scheduling → Scheduled
  ├─ Hold
  └─ Reject

파싱 충돌 → NeedsReview
일정 실패 → CalendarError → Scheduling → Scheduled
```

정기 수집은 사용자 또는 후속 단계가 설정한 상태를 이전 상태로 되돌리지 않습니다.

## 6. 데이터 계약

기준 모델은 `src/campus_mate/models.py`에 정의합니다.

- `UserProfile`
- `SourcePage`
- `ParseCandidate`
- `FieldEvidence`
- `Opportunity`
- `Recommendation`
- `CalendarEventRequest`
- `CalendarEventResult`
- `WorkflowReport`

실행 산출물은 `data/`, `artifacts/`, `_workspace/`에 저장하고 Git에서 제외합니다.

## 7. 비기능 요구사항

### 보안

- 인증정보는 환경변수 또는 Timely Secrets에서 읽습니다.
- 실제 프로필·일정·로그를 Git에 포함하지 않습니다.
- Hook과 CI에서 인증정보 패턴을 검사합니다.

### 안정성

- 네트워크 작업에는 timeout과 제한된 retry를 적용합니다.
- 항목별 실패를 격리합니다.
- Notion upsert와 Calendar 요청은 멱등성을 유지합니다.
- 일부 성공 결과를 보존합니다.

### 추적성

- 파싱 필드에 근거와 신뢰도를 저장합니다.
- 추천 이유에 사용한 속성을 명시합니다.
- 자동 처리가 중단된 항목에 상태와 원인을 저장합니다.

## 8. 완료 조건

- 6개 Agent와 12개 Skill 구조 검증 통과
- 단위 테스트, lint, compile, secret scan 통과
- fixture 재실행 시 중복 저장 없음
- `Accept`가 아닌 공고의 Calendar 요청 없음
- 성공 결과 없는 `Scheduled` 상태 없음
