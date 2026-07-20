# Campus Mate — Agent·Skill·코드·인계 관계표

## 1. 기능 Agent

| Agent | 주요 책임 | 사용 Skill | Python 구현 | 주요 출력 | 다음 인계 |
|---|---|---|---|---|---|
| `profile-manager` | 사용자 프로필 수집·정규화·검증 | `profile-build` | `services/onboarding.py`, `services/keywords.py`, `models.UserProfile` | 검증된 프로필과 검색어 | `fit-priority` |
| `source-collector` | 지원되는 공고 URL 탐색과 실패 격리 | `source-watchlist-crawl` | `sources/linkareer.py`, `workflows/collect.py` | 수집 결과 보고서 | `multipass-parser` |
| `multipass-parser` | HTML·OCR·Vision 추출, 근거 병합, 검토 상태 판단 | `html-opportunity-parse`, `rendered-page-ocr`, `poster-vision-extract`, `schema-merge-and-validate` | `parsing/*.py`, `models.ParseCandidate` | 구조화된 `Opportunity` | `fit-priority` |
| `fit-priority` | 설명 가능한 적합도·마감 우선순위·추천 이유 계산 | `recommendation-rank` | `services/recommendation.py`, `services/keywords.py` | 점수, 우선순위, 추천 이유 | `notion-dashboard` |
| `notion-dashboard` | 기존 데이터를 보존하는 upsert와 상태 유지 | `notion-dashboard-sync` | `integrations/notion.py` | page ID와 동기화 결과 | `schedule-notification` |
| `schedule-notification` | 충돌 상태, Slack 브리핑, Accept 전용 Calendar 동기화 | `slack-brief-generate`, `calendar-sync` | `workflows/brief.py`, `conflicts.py`, `accept_sync.py`, `integrations/calendar_bridge.py` | 브리핑과 Calendar 산출물 | 사용자 또는 QA |

## 2. Timely 자동화

| 자동화 | 실행 시점 | 조합되는 기능 역할 | 명령 흐름 | 외부 변경 |
|---|---|---|---|---|
| `daily-collector` | 매일 08:00 | 수집 → 파싱 → 추천 → Notion → 선택적 충돌 갱신 | `campus-mate collect`, 선택적으로 `conflicts apply` | Notion 갱신 |
| `slack-briefing` | 매일 09:00 | 일정·알림 | `campus-mate brief` | Slack 메시지 |
| `accept-sync` | 매시 정각 | Notion 조회 → 일정·알림 | `calendar plan` → 커넥터 → `calendar apply` | Calendar와 Notion 상태 |

이 항목은 배포 일정이며 별도의 Agent 정의가 아닙니다.

## 3. Skill

| Skill | 역할 | 외부 변경 수준 | 주요 실행 연결 |
|---|---|---:|---|
| `campus-mate-orchestrator` | 모드 선택, Agent 호출, 인계, 복구, 최종 보고 | 모드에 따라 다름 | CLI와 여섯 Agent |
| `profile-build` | 대화형 온보딩, 프로필 검증, 보수적 검색어 생성 | 로컬 파일 쓰기 | `campus-mate profile ...`, `services/onboarding.py` |
| `source-watchlist-crawl` | 지원 소스 탐색과 URL 계약 | 네트워크 읽기 | `campus-mate-skill source-watchlist-crawl` |
| `html-opportunity-parse` | 결정적인 페이지 정보 추출 | 없음 | `campus-mate-skill html-opportunity-parse` |
| `rendered-page-ocr` | 선택적 렌더링 텍스트 복구 | 로컬 임시 파일·네트워크 읽기 | `campus-mate-skill rendered-page-ocr` |
| `poster-vision-extract` | 선택적 포스터 필드 추출 | 외부 모델 읽기 | `campus-mate-skill poster-vision-extract` |
| `schema-merge-and-validate` | 필드 우선순위, 근거, 신뢰도, 충돌 판정 | 없음 | `campus-mate-skill schema-merge-and-validate` |
| `recommendation-rank` | 키워드 확장, 0–100 세부 점수, 우선순위, 이유 | 없음 | `interest-keyword-expand`, `fit-score-rank`, `deadline-priority-rank` CLI 동작 |
| `notion-dashboard-sync` | schema 확인과 비파괴 upsert | 외부 쓰기 | `integrations/notion.py` |
| `slack-brief-generate` | 브리핑 형식 생성 및 선택적 전송 | 외부 쓰기 | `campus-mate brief`, `workflows/brief.py` |
| `calendar-sync` | free/busy, Accept 상태, 중복 방지 요청, 결과 반영 | 외부 읽기·쓰기 연결 | `conflicts apply`, `calendar plan/apply` |
| `qa-audit` | 계약, 상태, 테스트, 인증정보, 산출물 검증 | 로컬 읽기·쓰기 | `validate_harness.py`, 테스트, secret scan |

## 4. 코드가 결합된 Harness 원칙

Markdown은 단순한 설명 자료가 아닙니다. 각 Agent와 Skill은 실제 실행 코드와 검증 가능한 출력에 연결됩니다. 반대로 Python 코드가 전체 작업 정책을 독단적으로 정하지도 않습니다. 어떤 명령을 언제 실행할 수 있는지, 어떤 근거가 필요한지, 어떤 상태를 보존해야 하는지, 어느 조건에서 다음 단계로 넘길 수 없는지는 Agent와 Skill 계약이 정합니다.
