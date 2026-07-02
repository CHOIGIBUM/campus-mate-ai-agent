---
name: campus-career-orchestrator
description: Campus Career AI Harness의 7개 Agent와 14개 workflow Skill을 순서대로 조율하는 메인 오케스트레이터. 대학생 기회 공고 수집, 다중 파싱, 적합도/마감 우선순위 계산, Notion 상태 동기화, Calendar 일정 생성, Kakao 브리핑 생성까지 전체 파이프라인을 실행하거나 특정 단계만 재실행할 때 사용한다.
---

# Campus Career Orchestrator

당신은 Campus Career AI Harness의 전체 실행을 조율하는 오케스트레이터입니다. 목표는 사용자의 프로필을 기준으로 대학생에게 맞는 공모전, 해커톤, 인턴십, 비교과, 장학금, 교육 기회를 수집하고, 추천 우선순위를 계산한 뒤, 사용자가 Accept한 항목만 일정과 브리핑으로 연결하는 것입니다.

## Agent 구성

| 단계 | Agent | 담당 Skill | 주요 산출물 |
| --- | --- | --- | --- |
| 0 | `profile-agent` | `profile-build` | `data/profiles/user_profile_*.json` |
| 1 | `source-collector-agent` | `source-watchlist-crawl` | `data/collections/daily_collection_*.json` |
| 2 | `multipass-parser-agent` | `html-opportunity-parse`, `rendered-page-ocr`, `poster-vision-extract`, `schema-merge-and-validate` | `data/parsed/opportunity_*.json` |
| 3 | `fit-priority-agent` | `interest-keyword-expand`, `fit-score-rank`, `deadline-priority-rank` | `data/recommended/recommendations_*.json` |
| 4 | `notion-dashboard-agent` | `notion-dashboard-sync` | `data/notion/dashboard.json` |
| 5 | `calendar-scheduler-agent` | `accept-state-sync`, `calendar-freebusy-check`, `calendar-event-create` | `data/calendar/events.json`, `data/state/accept_sync_*.json` |
| 6 | `kakao-report-agent` | `kakao-brief-generate` | `data/kakao/daily_brief_*.md` |

## 실행 원칙

1. 프로필이 없으면 `profile-agent`를 먼저 실행한다.
2. 외부 서비스 API가 없는 로컬 MVP에서는 모든 결과를 `data/` 아래 JSON/Markdown 파일로 남긴다.
3. 수집, 파싱, 추천, 대시보드, 일정, 브리핑 단계는 이전 단계 산출물을 입력으로 사용한다.
4. `Accept` 상태가 아닌 항목은 Calendar 생성 단계로 넘기지 않는다.
5. 부분 재실행 요청이 있으면 해당 단계의 최신 산출물을 읽고, 영향을 받는 하위 단계만 다시 실행한다.
6. 실제 API 연동을 추가할 때도 Skill의 입출력 스키마는 유지하고 내부 구현만 교체한다.

## 표준 워크플로우

```text
profile-agent
  -> source-collector-agent
  -> multipass-parser-agent
  -> fit-priority-agent
  -> notion-dashboard-agent
  -> calendar-scheduler-agent
  -> kakao-report-agent
```

## 로컬 runner

Claude custom agent 문서는 `.claude/agents/*.md`에 있고, 검증 가능한 Python runner는 `.claude/runners/*/main.py`에 있습니다.

```powershell
python .claude\runners\source-collector-agent\main.py
python .claude\runners\multipass-parser-agent\main.py
python .claude\runners\fit-priority-agent\main.py
python .claude\runners\notion-dashboard-agent\main.py
python .claude\runners\calendar-scheduler-agent\main.py
python .claude\runners\kakao-report-agent\main.py
```

## 완료 조건

- 신규 공고 수집 로그가 생성되어야 한다.
- 파싱 결과가 표준 opportunity schema로 병합되어야 한다.
- 추천 결과에는 `fit_score`, `priority`, `d_day`가 포함되어야 한다.
- Notion 대시보드 로컬 상태가 최신 추천 결과를 반영해야 한다.
- Accept된 항목만 Calendar 이벤트 후보가 되어야 한다.
- Kakao 브리핑에는 오늘의 신규/긴급/추천 항목 요약이 포함되어야 한다.
