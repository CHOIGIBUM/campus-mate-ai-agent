# Campus Mate — 프로젝트 운영 지침

Campus Mate는 대학생 대상 공모전 공고를 수집하고, 불완전한 정보를 구조화하며, 사용자 프로필과의 적합도를 계산한 뒤 사용자가 승인한 공고를 Notion·Slack·Google Calendar로 연결하는 **Python 실행 계층을 갖춘 Claude Code Harness**입니다.

프로젝트는 두 계층으로 구성됩니다.

1. **Harness 계층** — `.claude/agents/`, `.claude/skills/`, 루트 계약 문서, 단계별 인계 규칙, Hook
2. **실행 계층** — `src/campus_mate/` Python 패키지, CLI 명령, 테스트, Timely 커넥터 매핑

Harness는 누가 어떤 작업을 언제 수행할 수 있는지, 어떤 근거가 필요한지, 다음 단계로 넘기기 전에 무엇을 확인해야 하는지를 정합니다. Python 코드는 파싱, 점수 계산, 저장, 외부 서비스 연동처럼 재현 가능한 작업을 수행합니다.

## 기준 아키텍처

다음 여섯 개 기능 Agent는 프로젝트의 고정된 역할 체계입니다.

1. `profile-manager`
2. `source-collector`
3. `multipass-parser`
4. `fit-priority`
5. `notion-dashboard`
6. `schedule-notification`

Timely는 이 역할을 다음 세 자동화로 조합해 실행합니다.

- `daily-collector` — 매일 08:00 공고 수집, 파싱, 추천, Notion 반영, 선택적 충돌 상태 갱신
- `slack-briefing` — 매일 09:00 추천 공고 브리핑
- `accept-sync` — 매시 정각 Notion `Accept` 감지 및 Calendar 동기화

이 세 이름은 **자동화 일정**이며 추가 Claude subagent가 아닙니다.

메인 대화는 `campus-mate-orchestrator` Skill을 실행합니다. 각 Agent는 자신의 범위만 처리하고 구조화된 인계 결과를 Orchestrator에 반환해야 합니다. 별도의 경쟁적인 실행 흐름을 만들지 않습니다.

## 기준 문서

- 범위와 완료 기준: `spec.md`
- 단계 순서와 복구 규칙: `workflow.md`
- Agent·Skill·코드 연결 관계: `role-table.md`
- 런타임 모델과 공고 상태: `src/campus_mate/models.py`
- Timely 일정 매핑: `timely/automations.yaml`

문서와 코드가 서로 다르면 차이를 보고하고 둘을 함께 수정합니다. 한쪽을 임의로 기준으로 삼아 조용히 넘어가지 않습니다.

## 반드시 지켜야 할 규칙

### 근거와 파싱

- 마감일, 참가 자격, 혜택, 주최기관, 행사일을 추측해서 만들지 않습니다.
- 필드별 근거, 출처, 신뢰도, 경고를 유지합니다.
- 기본 출처가 심하게 깨진 경우가 아니라면 OCR·Vision보다 JSON-LD, Next.js 상태, 화면에 표시된 HTML을 우선합니다.
- 핵심 필드의 충돌이 해결되지 않으면 `NeedsReview`로 처리합니다.
- 현재 완전 지원되는 운영용 수집 어댑터는 Linkareer뿐입니다. 다른 사이트는 확장 대상입니다.

### 추천

- 적합도는 설명 가능한 정렬 기준이며 수상·선발 가능성 예측이 아닙니다.
- 파싱 신뢰도와 적합도 점수를 분리합니다.
- 추천 이유는 실제 프로필과 공고 필드에 근거해야 합니다.
- 참가 자격이 확인되지 않았으면 참가 가능으로 간주하지 않습니다.

### 외부 서비스 쓰기

- 공고 갱신을 위해 Notion 데이터베이스 전체를 삭제하거나 다시 만들지 않습니다.
- 안정적인 `opportunity_id` 또는 정규화된 원문 URL을 기준으로 upsert합니다.
- `Accept`, `Hold`, `Reject`, `Scheduling`, `Scheduled` 상태를 보존합니다.
- Slack은 알림 채널입니다. 참가 승인은 Notion에서 처리합니다.
- `Accept` 상태의 공고만 Calendar 요청을 만들 수 있습니다.
- 커넥터 결과로 성공이 확인된 뒤에만 `Scheduled`로 변경합니다.
- 일부 일정 생성에 실패하면 성공한 event ID를 보존하고 실패한 요청만 다시 시도합니다.

### 보안

- 소스 코드, Markdown, fixture, 스크린샷, 로그, 인계 문서에 실제 인증정보를 넣지 않습니다.
- 환경변수 또는 Timely Secrets를 사용합니다.
- 커밋 전 `python scripts/scan_secrets.py .`를 실행합니다.
- 과거 파일에 한 번이라도 저장된 인증정보는 삭제 여부와 관계없이 폐기하고 재발급합니다.

### 런타임 작업 공간

다음 디렉터리는 실행 중 생성되며 Git에서 제외됩니다.

```text
_workspace/runs/<run-id>/
artifacts/
data/
```

완전한 인계 결과에는 다음 항목이 포함되어야 합니다.

- `status`: `PASS`, `NEEDS_REVIEW`, `FAIL` 중 하나
- 입력 식별자 또는 경로
- 출력 경로
- 처리 건수와 검증 요약
- 경고와 오류
- 다음 Agent 또는 중단 조건

### 코드 품질

- Python 3.11 이상
- 단계 간 데이터와 외부 데이터는 Pydantic 모델로 검증
- 기본 시간대는 `Asia/Seoul`
- 운영 코드에 고정 날짜를 넣지 않고 테스트에서만 날짜 주입
- 네트워크 요청에 명시적 timeout과 제한된 retry 적용
- 수집 어댑터는 `sources/`, 외부 서비스 커넥터는 `integrations/`에 배치
- 동작을 변경할 때 관련 테스트도 함께 수정

## 표준 검증 명령

```bash
python -m pytest -q
python scripts/validate_harness.py
python scripts/scan_secrets.py .
python -m compileall -q src scripts .claude/hooks
ruff check src tests scripts .claude/hooks
```

## 사용자에게 설명할 때의 기준

- Campus Mate를 Timely가 오케스트레이션하고 Python이 실제 처리를 수행하는 Harness로 설명합니다.
- 여섯 개 기능 Agent와 세 개 자동화 일정을 구분합니다.
- OCR, Vision, 미지원 사이트는 실제 설정과 시연이 확인되지 않았다면 활성 기능으로 표현하지 않습니다.
- `적합도 점수`는 투명한 정렬 기준으로 설명하며 확률로 표현하지 않습니다.
