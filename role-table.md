# Campus Mate — Agent·Skill·코드 관계표

## 기능 Agent

| Agent | 책임 | Skill | Python 구현 | 출력 | 다음 단계 |
|---|---|---|---|---|---|
| `profile-manager` | 프로필 수집·정규화·검증 | `profile-build` | `services/onboarding.py`, `services/keywords.py`, `models.UserProfile` | 프로필, 검색어 | `fit-priority` |
| `source-collector` | URL 탐색·정규화·실패 격리 | `source-watchlist-crawl` | `sources/linkareer.py`, `workflows/collect.py` | URL·조회 결과 | `multipass-parser` |
| `multipass-parser` | HTML·OCR·Vision 추출과 필드 병합 | `html-opportunity-parse`, `rendered-page-ocr`, `poster-vision-extract`, `schema-merge-and-validate` | `parsing/*.py` | `Opportunity` | `fit-priority` |
| `fit-priority` | 적합도·우선순위·추천 이유 | `recommendation-rank` | `services/recommendation.py`, `services/keywords.py` | `Recommendation` | `notion-dashboard` |
| `notion-dashboard` | schema 보완·upsert·상태 보존 | `notion-dashboard-sync` | `integrations/notion.py` | page ID·동기화 결과 | `schedule-notification` |
| `schedule-notification` | 충돌 상태·Slack·Calendar | `slack-brief-generate`, `calendar-sync` | `workflows/brief.py`, `conflicts.py`, `accept_sync.py`, `integrations/calendar_bridge.py` | 브리핑·일정 결과 | QA |

## Timely 자동화

| 자동화 | 실행 시점 | 실행 범위 | 외부 변경 |
|---|---|---|---|
| `daily-collector` | 매일 08:00 | 수집 → 파싱 → 추천 → Notion | Notion |
| `slack-briefing` | 매일 09:00 | 추천 브리핑 | Slack |
| `accept-sync` | 매시 정각 | Accept 조회 → Calendar 결과 반영 | Calendar·Notion |

## Skill

| Skill | 역할 | 실행 연결 |
|---|---|---|
| `campus-mate-orchestrator` | 실행 모드·Agent 호출·인계·복구 | Claude Code 메인 진입점 |
| `profile-build` | 프로필 생성·검증·검색어 생성 | `campus-mate profile ...` |
| `source-watchlist-crawl` | Linkareer URL 수집 | `campus-mate collect` |
| `html-opportunity-parse` | 구조화 데이터·HTML 추출 | `parsing/html.py` |
| `rendered-page-ocr` | 선택적 OCR 추출 | `parsing/ocr.py` |
| `poster-vision-extract` | 선택적 포스터 Vision 추출 | `parsing/vision.py` |
| `schema-merge-and-validate` | 필드 병합·근거·충돌 판정 | `parsing/merge.py` |
| `recommendation-rank` | 점수·우선순위·이유 | `services/recommendation.py` |
| `notion-dashboard-sync` | schema 확인·upsert | `integrations/notion.py` |
| `slack-brief-generate` | Slack payload·전송 | `workflows/brief.py` |
| `calendar-sync` | free/busy·일정 요청·결과 반영 | `workflows/conflicts.py`, `accept_sync.py` |
| `qa-audit` | 구조·상태·테스트·보안 검증 | 테스트·검증 스크립트 |

Agent는 책임과 판단 기준을 정의하고, Skill은 실행 절차를 정의하며, Python 코드는 재현 가능한 처리를 수행합니다.
