# Nexus_Harness_Eng

강원대학교 2026 Harness Engineering: AI Agent & Skill Hackathon

## Campus Career AI

Campus Career AI는 대학생에게 맞는 공모전, 해커톤, 대외활동 기회를 수집하고, 사용자 프로필 기반으로 추천한 뒤, 사용자가 Accept한 항목만 일정으로 승격하는 Agentic Workflow 프로젝트입니다.

핵심 흐름은 다음과 같습니다.

```text
Profile 입력
  -> Source 수집
  -> Multi-pass 파싱
  -> Schema 병합
  -> Fit/Priority 계산
  -> Notion 현황판 동기화
  -> 사용자 Accept
  -> Calendar 일정 생성
  -> Kakao 브리프 생성
```

## 현재 구현 상태

현재는 외부 API 키 없이도 검증 가능한 로컬 MVP 파이프라인이 구현되어 있습니다.

- Profile Agent: 사용자 온보딩 입력을 프로필 JSON으로 저장
- Source Collector Agent: Source Watchlist 기반 URL 수집 및 중복 제거
- Multi-pass Parser Agent: HTML 파싱, OCR/Vision 단계 시도 기록, 표준 스키마 병합
- Fit & Priority Agent: 키워드 확장, 적합도 점수, 마감 기반 우선순위 계산
- Notion Dashboard Agent: 로컬 JSON 대시보드로 Notion 카드 생성/갱신 시뮬레이션
- Calendar Scheduler Agent: Accept 상태 감지, 충돌 검사, 로컬 Calendar 이벤트 생성
- Kakao Report Agent: 일일 브리프 Markdown 및 로그 생성

Notion, Google Calendar, KakaoTalk 실 API 연동은 아직 로컬 시뮬레이션 단계입니다. 실제 서비스 연동 시 각 Skill의 로컬 저장부를 API 클라이언트로 교체하면 됩니다.

## 디렉터리 구성

```text
.pi/
  agents/
    profile-agent/
    source-collector-agent/
    multipass-parser-agent/
    fit-priority-agent/
    notion-dashboard-agent/
    calendar-scheduler-agent/
    kakao-report-agent/
  skills/
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
data/
  choices/
  profiles/
```

## Agent와 Skill 역할

Agent는 흐름을 조율하는 runner입니다. Skill은 실제 작업 단위입니다.

예를 들어 `multipass-parser-agent`는 다음 Skill을 순서대로 호출합니다.

- `html-opportunity-parse`
- `rendered-page-ocr`
- `poster-vision-extract`
- `schema-merge-and-validate`

각 Agent의 실행 진입점은 `main.py`입니다.

## 로컬 실행 예시

PowerShell 기준:

```powershell
python .pi\agents\source-collector-agent\main.py
python .pi\agents\multipass-parser-agent\main.py
python .pi\agents\fit-priority-agent\main.py
python .pi\agents\notion-dashboard-agent\main.py
python .pi\agents\calendar-scheduler-agent\main.py
python .pi\agents\kakao-report-agent\main.py
```

JSON 입력을 직접 넘기는 방식도 지원합니다.

```powershell
'{"fit_score":88,"submission_deadline":"2026-07-07T23:59:00+09:00","today":"2026-07-02"}' |
  python .pi\skills\deadline-priority-rank\deadline_priority_rank.py
```

## 산출 데이터

런타임 산출물은 `data/` 아래에 생성됩니다.

- `data/collections/`: 수집 결과
- `data/parsed/`: 표준 스키마로 병합된 공고
- `data/recommended/`: 개인화 추천 결과
- `data/notion/`: 로컬 Notion 대시보드
- `data/calendar/`: 로컬 Calendar 이벤트
- `data/kakao/`: Kakao 브리프 Markdown 및 로그
- `data/state/`: Accept 상태 동기화 결과

## 다음 작업

- 실제 사이트별 크롤링 selector 보강
- OCR/Vision 엔진 연동
- Notion API 연동
- Google Calendar API 연동
- KakaoTalk 또는 대체 알림 채널 발송 연동
- E2E 테스트 파일 정식 추가
