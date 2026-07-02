# Campus Career AI Harness

> 대학생에게 맞는 공모전, 해커톤, 인턴십, 비교과, 장학금, 교육 기회를 수집하고 추천한 뒤, Accept한 항목만 일정과 일일 브리핑으로 연결하는 Claude Agent/Skill 하네스입니다.

이 저장소는 `revfactory/webtoon-harness`의 구성 방식을 참고해 `.claude/agents`와 `.claude/skills` 중심으로 정리되어 있습니다. 현재는 외부 API 없이도 검증 가능한 로컬 MVP가 포함되어 있으며, Notion, Google Calendar, KakaoTalk 연동부는 로컬 JSON/Markdown 어댑터로 대체되어 있습니다.

**7개 Agent**, **15개 Campus Career Skill**로 구성됩니다. Skill은 `campus-career-orchestrator` 1개와 실제 workflow Skill 14개입니다.

## 특징

- **Claude 친화 구조**: custom agent 선언은 `.claude/agents/*.md`, skill 정의는 `.claude/skills/*/SKILL.md`에 배치했습니다.
- **검증 가능한 runner**: 실제 동작하는 Python runner는 `.claude/runners/*/main.py`에 분리했습니다.
- **로컬 MVP 우선**: 외부 API 키 없이 `data/` 아래 파일 산출물로 전체 파이프라인을 테스트할 수 있습니다.
- **교체 가능한 Skill 구현**: API 연동 시 각 Skill 내부 저장소만 실제 클라이언트로 교체하면 됩니다.
- **Accept 이후 자동화**: 사용자가 Accept한 항목만 Calendar 후보가 되고 Kakao 브리핑에 반영됩니다.

## 구조

```text
.claude/
  agents/                         # Claude custom agent 선언
    profile-agent.md
    source-collector-agent.md
    multipass-parser-agent.md
    fit-priority-agent.md
    notion-dashboard-agent.md
    calendar-scheduler-agent.md
    kakao-report-agent.md
  runners/                        # 로컬 실행 가능한 Python runner
    profile-agent/
    source-collector-agent/
    multipass-parser-agent/
    fit-priority-agent/
    notion-dashboard-agent/
    calendar-scheduler-agent/
    kakao-report-agent/
  skills/                         # Campus Career workflow Skill
    campus-career-orchestrator/
    profile-build/
    source-watchlist-crawl/
    html-opportunity-parse/
    rendered-page-ocr/
    poster-vision-extract/
    schema-merge-and-validate/
    interest-keyword-expand/
    fit-score-rank/
    deadline-priority-rank/
    notion-dashboard-sync/
    accept-state-sync/
    calendar-freebusy-check/
    calendar-event-create/
    kakao-brief-generate/
data/                             # 로컬 런타임 산출물
tools/skill-creator/              # Skill 제작 보조 도구
```

## Agent 팀

| 팀 | Agent | 역할 |
| --- | --- | --- |
| 온보딩 | `profile-agent` | 사용자 기본 정보, 관심사, 진로 목표, 가능 시간을 프로필 JSON으로 저장 |
| 수집 | `source-collector-agent` | 등록된 사이트와 학내 공지에서 신규 공고 URL 수집 |
| 파싱 | `multipass-parser-agent` | HTML, OCR, Vision 후보 결과를 표준 opportunity schema로 병합 |
| 추천 | `fit-priority-agent` | 관심 키워드 확장, 적합도 점수, 마감 우선순위 계산 |
| 대시보드 | `notion-dashboard-agent` | 추천 결과를 로컬 Notion 대시보드 상태로 동기화 |
| 일정 | `calendar-scheduler-agent` | Accept 상태 감지, 일정 충돌 확인, Calendar 이벤트 생성 |
| 브리핑 | `kakao-report-agent` | 일일 추천/긴급/수락 항목을 Kakao 브리핑 Markdown으로 생성 |

## Workflow

```text
Profile 입력
  -> Source 수집
  -> Multi-pass 파싱
  -> Schema 병합
  -> Fit/Priority 계산
  -> Notion 현황판 동기화
  -> 사용자 Accept
  -> Calendar 일정 생성
  -> Kakao 브리핑 생성
```

전체 흐름의 진입점은 `.claude/skills/campus-career-orchestrator/SKILL.md`입니다. 개별 Agent의 역할 정의는 `.claude/agents/*.md`, 실제 실행 코드는 `.claude/runners/*/main.py`에 있습니다.

## 사용 방법

Claude Code 프로젝트에 하네스를 가져올 때는 `.claude/` 디렉터리를 프로젝트 루트에 배치합니다.

```powershell
git clone https://github.com/CHOIGIBUM/Nexus_Harness_Eng.git
Copy-Item -Recurse Nexus_Harness_Eng\.claude C:\path\to\your-project\.claude
```

현재 저장소에서 로컬 MVP를 직접 실행할 수도 있습니다.

```powershell
python .claude\runners\source-collector-agent\main.py
python .claude\runners\multipass-parser-agent\main.py
python .claude\runners\fit-priority-agent\main.py
python .claude\runners\notion-dashboard-agent\main.py
python .claude\runners\calendar-scheduler-agent\main.py
python .claude\runners\kakao-report-agent\main.py
```

Skill 단위 실행도 지원합니다.

```powershell
'{"fit_score":88,"submission_deadline":"2026-07-07T23:59:00+09:00","today":"2026-07-02"}' |
  python .claude\skills\deadline-priority-rank\deadline_priority_rank.py
```

## 산출 데이터

- `data/profiles/`: 사용자 프로필
- `data/collections/`: 수집 로그와 신규 URL
- `data/parsed/`: 표준 schema로 병합된 공고
- `data/recommended/`: 적합도/우선순위 계산 결과
- `data/notion/`: 로컬 Notion 대시보드 상태
- `data/calendar/`: 로컬 Calendar 이벤트
- `data/kakao/`: 일일 브리핑 Markdown
- `data/state/`: Accept 상태 동기화 로그

## 다음 구현 단계

- 사이트별 실제 selector와 pagination 보강
- OCR/Vision 엔진 또는 멀티모달 API 연동
- Notion API 클라이언트 교체
- Google Calendar API 클라이언트 교체
- KakaoTalk 또는 대체 알림 채널 발송 연동
- E2E 테스트 파일 정식 추가
