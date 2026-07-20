# Campus Mate — 오케스트레이션 워크플로

## 1. 실행 모드

| 모드 | 일반적인 실행 계기 | 외부 쓰기 | 실행 단계 |
|---|---|---:|---|
| `status` | 설정 또는 프로젝트 상태 확인 | 없음 | 0, 8 |
| `onboard` | 신규 프로필 또는 프로필 수정 | 로컬 프로필만 | 0, 1, 8 |
| `demo` | fixture 시연 또는 명시적으로 승인된 live 시연 | 기본은 JSON | 0–8 |
| `daily` | Timely `daily-collector` 또는 수동 수집 | 설정 시 Notion | 0–5, 8 |
| `brief` | Timely `slack-briefing` 또는 수동 브리핑 | 승인 시 Slack | 0, 6, 8 |
| `accept-sync` | Timely 시간별 실행 또는 수동 승인 동기화 | Calendar와 Notion | 0, 7, 8 |
| `partial:<phase>` | 특정 단계 복구 | 단계에 따라 다름 | 해당 단계와 필요한 후속 단계 |

외부 서비스에 실제로 쓸지 명확하지 않으면 `status` 또는 dry-run부터 시작합니다.

## 2. 런타임 작업 공간

Orchestrator는 실행할 때마다 다음 구조를 만듭니다.

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

이 디렉터리는 실행 산출물용이며 Git에서 제외합니다.

## 3. Agent 인계 계약

```json
{
  "status": "PASS",
  "agent": "multipass-parser",
  "inputs": ["02_collection/source-pages.json"],
  "outputs": ["03_parsing/opportunities.json"],
  "metrics": {"parsed": 8, "needs_review": 1},
  "warnings": ["한 공고에서 서로 다른 마감일이 확인됨"],
  "errors": [],
  "next": "fit-priority"
}
```

허용되는 `status` 값은 다음과 같습니다.

- `PASS` — 다음 단계를 계속 진행할 수 있습니다.
- `NEEDS_REVIEW` — 안전하게 사용할 수 있는 일부 결과는 있지만 지정 검토가 필요합니다.
- `FAIL` — 다음 단계에서 안전하게 사용할 수 있는 결과가 없습니다.

## 4. 전체 실행 단계

### 단계 0 — 컨텍스트와 안전 확인

1. 사용자 요청 또는 Timely 일정에서 실행 모드를 결정합니다.
2. `CLAUDE.md`, `spec.md`, 관련 Skill을 읽습니다.
3. 실행 디렉터리와 manifest를 만듭니다.
4. 실제 값을 출력하지 않고 프로필, 저장 backend, 선택적 OCR·Vision, 인증정보 존재 여부만 확인합니다.
5. 외부 쓰기가 허용되었는지 결정합니다.

요청한 외부 쓰기에 필요한 설정이 없거나, 미지원 소스를 운영 지원으로 요구하거나, Notion 전체 삭제·재생성이 제안되면 중단합니다.

### 단계 1 — 프로필

담당 Agent: `profile-manager`

1. 기존 프로필이 있으면 불러옵니다.
2. 누락됐거나 사용자가 변경하려는 값만 질문합니다.
3. `UserProfile`로 정규화하고 검증합니다.
4. 프로필과 실행 시점 snapshot을 저장합니다.
5. 추천 검색어와 변경된 필드를 반환합니다.

통과 조건: 학교, 학년, 전공, 관심 분야 1개 이상이 존재하고 임의로 만든 값이 없어야 합니다.

### 단계 2 — 공고 수집

담당 Agent: `source-collector`

1. 지원되는 수집 어댑터인지 확인합니다.
2. 설정된 제한 개수까지 공고를 찾습니다.
3. URL을 정규화하고 중복을 제거합니다.
4. timeout과 제한된 retry로 상세 페이지를 가져옵니다.
5. 항목별 성공과 실패를 기록합니다.

통과 조건: 공고가 0건이어도 수집 결과 보고서가 존재해야 합니다.

### 단계 3 — 멀티패스 파싱

담당 Agent: `multipass-parser`

1. JSON-LD, Next.js 상태, 화면에 표시된 HTML을 파싱합니다.
2. 누락되거나 충돌하는 핵심 필드를 확인합니다.
3. 활성화되어 있고 필요할 때만 렌더링 OCR을 실행합니다.
4. 활성화되어 있고 필요할 때만 포스터 Vision을 실행합니다.
5. 필드별 근거, 신뢰도, 경고를 유지하며 병합합니다.
6. 해결되지 않은 핵심 충돌은 `NeedsReview`로 표시합니다.

통과 조건: 저장되는 모든 항목에 제목, 원문 URL, 안정적인 ID, 명시적인 검토 상태가 있어야 합니다.

### 단계 4 — 적합도와 우선순위

담당 Agent: `fit-priority`

1. 프로필 기반 검색어를 보수적으로 생성합니다.
2. 항목별 점수와 총점을 계산합니다.
3. 마감 우선순위를 계산합니다.
4. 실제 정보에 근거한 추천 이유를 만듭니다.
5. 참가 자격과 파싱의 불확실성을 유지합니다.

통과 조건: 점수는 0–100 범위이고 세부 점수 합이 총점과 같으며, 추천 이유가 관찰된 속성에 근거해야 합니다.

### 단계 5 — Notion과 충돌 상태

담당 Agent: `notion-dashboard`

1. 기존 데이터를 삭제하지 않고 필요한 schema만 보완합니다.
2. 안정적인 ID 또는 원문 URL을 기준으로 upsert합니다.
3. 사용자가 정한 상태, 수동 메모, Calendar ID를 보존합니다.
4. 정규화된 free/busy 입력이 있으면 충돌 상태를 반영합니다.
5. page ID와 동기화 오류를 기록합니다.

통과 조건: 같은 공고를 다시 실행해도 같은 page ID를 유지하고 사용자 상태를 보존해야 합니다.

### 단계 6 — Slack 브리핑

담당 Agent: `schedule-notification`

1. `Recommended` 상태의 공고를 조회합니다.
2. 우선순위, 점수, 마감일 순으로 정렬합니다.
3. Slack payload를 만듭니다.
4. 대화형 실행에서는 명시적인 전송 요청이 없으면 dry-run을 기본으로 합니다.
5. Timely 자동화에서는 설정된 채널로 전송할 수 있습니다.

통과 조건: payload에 token이나 비공개 프로필 필드가 없어야 합니다.

### 단계 7 — 승인과 Calendar

담당 Agent: `schedule-notification`

1. `Accept` 상태의 공고만 조회합니다.
2. 마감, 준비, 행사 일정 요청을 계획합니다.
3. 안정적인 request ID와 idempotency ID를 부여합니다.
4. Timely/Composio가 실제 일정을 생성합니다.
5. request ID를 기준으로 생성 결과를 반영합니다.
6. 성공한 event ID를 보존하고 실패한 요청만 다시 시도합니다.
7. 성공이 확인된 뒤에만 `Scheduled`로 변경합니다.

통과 조건: `Accept`가 아닌 공고에 대한 일정 요청이 없어야 하며, 확인되지 않은 항목을 `Scheduled`로 표시하지 않아야 합니다.

### 단계 8 — QA와 결과 보고

사용 Skill: `qa-audit`

1. 단계별 산출물과 Agent 인계 결과를 확인합니다.
2. 공고 상태 규칙과 중복 방지를 확인합니다.
3. 코드가 변경됐다면 테스트, Harness 검증, compile, lint, secret scan을 실행합니다.
4. 수행한 작업, 생략된 선택 단계, 경고, 후속 조치를 요약합니다.

## 5. Timely 자동화 구성

```text
08:00 daily-collector
  source-collector
  → multipass-parser
  → fit-priority
  → notion-dashboard
  → 선택적으로 schedule-notification의 충돌 상태 갱신

09:00 slack-briefing
  schedule-notification

매시 정각 accept-sync
  notion-dashboard 조회
  → schedule-notification Calendar 계획·결과 반영
```

이 자동화 이름은 배포·실행 단위이며 추가 `.claude/agents`가 아닙니다.

## 6. 일부 단계만 다시 실행하는 경우

- 프로필 변경 → 추천, Notion, 브리핑부터 다시 실행하고 별도 요청이 없으면 재수집하지 않습니다.
- 파서 개선 → 영향을 받는 URL만 다시 파싱한 뒤 추천과 Notion을 갱신합니다.
- 점수 규칙 변경 → 추천 단계부터 다시 실행합니다.
- Slack 형식 변경 → 브리핑만 다시 실행합니다.
- Calendar 실패 → 실패한 요청만 다시 실행합니다.
- 사용자가 `Hold` 또는 `Reject`로 변경 → Calendar를 만들지 않으며 앞 단계를 다시 실행할 필요가 없습니다.

## 7. 오류 복구 규칙

| 실패 상황 | 복구 방법 |
|---|---|
| 한 공고 URL 조회 실패 | 다른 URL은 계속 처리하고 해당 항목의 실패를 기록 |
| OCR 사용 불가 | 생략 경고를 남기고 HTML·Vision 근거 유지 |
| Vision 사용 불가 | 생략 경고를 남기고 필드를 추측하지 않음 |
| 마감일 충돌 | `NeedsReview`로 표시하고 자동 일정화 차단 |
| Notion rate limit | 제한된 retry 후 삭제 없이 동기화 오류 기록 |
| Slack 전송 실패 | dry-run payload와 오류 보존 |
| Calendar 요청 한 건 실패 | 성공한 ID는 보존하고 실패 요청만 재시도 |
| 인증정보 감지 | 외부 쓰기·커밋을 중단하고 노출된 인증정보 재발급 |

## 8. 최종 실행 요약

Orchestrator는 다음 항목을 보고합니다.

- run ID와 실행 모드
- 호출한 Agent
- 발견, 파싱, 추천, 검토 필요, 실패 건수
- Notion 생성·갱신·보존 건수
- Slack dry-run 또는 전송 결과
- Calendar 요청·성공·실패 건수
- QA 상태
- 정확한 산출물 경로와 경고
