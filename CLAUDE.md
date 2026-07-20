# Campus Mate — 프로젝트 운영 규칙

Campus Mate는 공고 수집·파싱·추천·현황판 동기화·일정 반영을 6개 Agent와 12개 Skill로 나누고, `src/campus_mate/`의 Python 코드로 실행하는 Claude Code Harness입니다.

## 구성

- `.claude/agents/` — 역할과 책임
- `.claude/skills/` — 단계별 실행 절차와 검증 기준
- `src/campus_mate/` — 수집·파싱·추천·외부 서비스 연동 코드
- `spec.md` — 기능 범위와 완료 조건
- `workflow.md` — 실행 순서와 복구 규칙
- `role-table.md` — Agent·Skill·코드 연결 관계
- `timely/automations.yaml` — 정기 자동화 일정

## 기능 Agent

1. `profile-manager`
2. `source-collector`
3. `multipass-parser`
4. `fit-priority`
5. `notion-dashboard`
6. `schedule-notification`

Timely 자동화 이름인 `daily-collector`, `slack-briefing`, `accept-sync`는 별도 Agent가 아니라 실행 일정입니다.

## 실행 원칙

### 역할 분리

- 메인 대화는 `campus-mate-orchestrator` Skill을 사용합니다.
- Agent는 지정된 범위만 처리합니다.
- 단계 간 전달은 구조화된 인계 객체로 수행합니다.
- 계약과 코드 동작을 함께 변경하고 관련 테스트를 갱신합니다.

### 공고 수집·파싱

- 운영 수집 어댑터는 `linkareer`입니다.
- JSON-LD, Next.js 상태, 화면 HTML을 우선 사용합니다.
- OCR과 Vision은 필요한 필드가 남아 있고 실행 환경이 준비된 경우에만 호출합니다.
- 날짜·참가 자격·혜택·주최기관을 추측하지 않습니다.
- 선택된 필드에는 출처, 원문 근거, 신뢰도를 유지합니다.
- 핵심 필드 충돌은 `NeedsReview`로 처리합니다.

### 추천

- 적합도는 0–100 범위의 정렬 기준입니다.
- 적합도와 파싱 신뢰도를 분리합니다.
- 추천 이유는 프로필과 공고의 확인된 필드에 근거합니다.
- 참가 자격이 확인되지 않으면 참가 가능으로 처리하지 않습니다.

### Notion·Slack·Calendar

- Notion은 안정적인 공고 ID 또는 정규화 URL로 upsert합니다.
- 기존 페이지 전체 삭제와 재생성을 금지합니다.
- `Accept`, `Hold`, `Reject`, `Scheduling`, `Scheduled` 상태와 수동 메모를 보존합니다.
- Slack은 추천 브리핑 채널이며 승인 입력으로 사용하지 않습니다.
- Calendar 요청은 `Accept` 상태에서만 생성합니다.
- 성공 결과가 확인된 일정만 `Scheduled`로 반영합니다.
- 일부 실패 시 성공한 event ID를 보존하고 실패 요청만 재시도합니다.

### 보안

- 인증정보는 환경변수 또는 Timely Secrets에서 읽습니다.
- 실제 token, 개인 프로필, 개인 일정, 실행 로그를 Git에 포함하지 않습니다.
- 외부 쓰기 전 `python scripts/scan_secrets.py .`를 실행합니다.

### 코드 품질

- Python 3.11 이상을 사용합니다.
- 외부 입력과 단계 간 객체는 Pydantic 모델로 검증합니다.
- 기본 시간대는 `Asia/Seoul`입니다.
- 네트워크 요청에는 timeout과 제한된 retry를 적용합니다.
- 운영 날짜를 코드에 고정하지 않습니다.

## Agent 인계 형식

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

`status`는 `PASS`, `NEEDS_REVIEW`, `FAIL` 중 하나입니다.

## 검증 명령

```bash
python -m pytest -q
python scripts/validate_harness.py
python scripts/scan_secrets.py .
python -m compileall -q src scripts .claude/hooks
ruff check src tests scripts .claude/hooks
```
