# Campus Career AI - 워크플로우 아키텍처

## 1️⃣ 전체 워크플로우 흐름도

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Campus Career AI - 전체 프로세스 플로우                   │
└─────────────────────────────────────────────────────────────────────────────┘

[초기화 단계]
    ↓
    ┌──────────────────────────────────────┐
    │  [1] 사용자 온보딩 (수동)            │
    │  입력: 이름, 학과, 관심분야 등      │
    └──────────────────────────────────────┘
                ↓
    ┌──────────────────────────────────────┐
    │  profile-agent                       │
    │  → profile-build Skill               │
    │  출력: user_profile_{id}.json        │
    └──────────────────────────────────────┘
                ↓
                ↓ (저장: ./.pi/data/profiles/)
                ↓

[자동화 수집 단계 - 매일 08:00 (또는 사용자 지정시간)]
    ↓
    ┌──────────────────────────────────────┐
    │  source-collector-agent              │
    │  (Scheduler 트리거)                   │
    │  → source-watchlist-crawl Skill      │
    │  출력: daily_collection_{date}.json  │
    └──────────────────────────────────────┘
                ↓
                ↓ (URL 목록)
                ↓

[파싱 단계 - 3중 검증]
    ↓
    ┌────────────────────────────────────────┐
    │  multipass-parser-agent                │
    │  ┌──────────────────────────────────┐  │
    │  │  1차: html-opportunity-parse     │  │
    │  │  (HTML 텍스트 추출)              │  │
    │  └──────────────────────────────────┘  │
    │         ↓                              │
    │  ┌──────────────────────────────────┐  │
    │  │  2차: rendered-page-ocr          │  │
    │  │  (렌더링/OCR 보완)               │  │
    │  └──────────────────────────────────┘  │
    │         ↓                              │
    │  ┌──────────────────────────────────┐  │
    │  │  3차: poster-vision-extract      │  │
    │  │  (포스터 이미지 분석)            │  │
    │  └──────────────────────────────────┘  │
    │         ↓                              │
    │  ┌──────────────────────────────────┐  │
    │  │  schema-merge-and-validate       │  │
    │  │  (3단계 결과 병합 & 검증)       │  │
    │  └──────────────────────────────────┘  │
    │  출력: parsed_opportunity_{id}.json    │
    └────────────────────────────────────────┘
                ↓
                ↓ (구조화된 공고 데이터)
                ↓

[개인화 추천 단계]
    ↓
    ┌──────────────────────────────────────────┐
    │  fit-priority-agent                      │
    │  ┌────────────────────────────────────┐  │
    │  │ interest-keyword-expand            │  │
    │  │ (관심분야 → 키워드 확장)          │  │
    │  └────────────────────────────────────┘  │
    │         ↓                                │
    │  ┌────────────────────────────────────┐  │
    │  │ fit-score-rank                     │  │
    │  │ (적합도 점수 계산: 0-100)        │  │
    │  └────────────────────────────────────┘  │
    │         ↓                                │
    │  ┌────────────────────────────────────┐  │
    │  │ deadline-priority-rank             │  │
    │  │ (우선순위: 긴급/중요/참고)       │  │
    │  └────────────────────────────────────┘  │
    │  출력: recommendation_{id}.json         │
    └──────────────────────────────────────────┘
                ↓
                ↓ (적합도 점수 & 우선순위)
                ↓

[Notion 현황판 동기화]
    ↓
    ┌──────────────────────────────────────┐
    │  notion-dashboard-agent              │
    │  → notion-dashboard-sync Skill       │
    │                                      │
    │  [Notion에 카드 생성]                │
    │  • 프로그램명, 포스터, 링크         │
    │  • 적합도, 우선순위, 마감일        │
    │  • 상태 = "New"                    │
    │                                      │
    │  [1분 주기로 Status 모니터링]       │
    │  • "New" 상태 카드 감지             │
    │  • "Recommended" 상태 카드 감지     │
    │  • "Accept" 상태 변경 감지 ← 핵심! │
    │                                      │
    │  출력: notion_sync_log_{date}.json   │
    └──────────────────────────────────────┘
                ↓
                ↓ (Accept 신호)
                ↓

[사용자 의사 결정 포인트] ★
    ↓
    사용자가 Notion 현황판에서 선택:
    • [Accept] → 일정 생성으로 진행
    • [Hold]   → 보류 (나중에 검토)
    • [Reject] → 제외
                ↓

[Google Calendar 동기화 - Accept만 처리]
    ↓
    ┌────────────────────────────────────────┐
    │  calendar-scheduler-agent              │
    │  (Notion "Accept" 신호 감지)          │
    │                                        │
    │  [1단계: 충돌 검사]                    │
    │  → calendar-freebusy-check Skill      │
    │                                        │
    │  [2단계: 일정 생성]                    │
    │  → calendar-event-create Skill        │
    │    • 마감일 일정 (D-day 23:59)       │
    │    • 행사일 일정 (시작~종료)          │
    │    • 준비 일정 (D-5~D-1)              │
    │                                        │
    │  [3단계: 결과 반영]                    │
    │  → Notion Status = "Scheduled"       │
    │  → accept-state-sync Skill           │
    │                                        │
    │  출력: calendar_event_created_{id}.json│
    └────────────────────────────────────────┘
                ↓
                ↓ (Google Calendar에 일정 추가)
                ↓

[일일 보고 단계 - 매일 08:00 (또는 사용자 지정시간)]
    ↓
    ┌────────────────────────────────────────┐
    │  kakao-report-agent                    │
    │  (매일 정해진 시간에 자동 트리거)     │
    │  → kakao-brief-generate Skill         │
    │                                        │
    │  [보고 내용]                           │
    │  • 🔥 긴급 마감 (D-7 이내)            │
    │  • ⭐ 신규 추천 (TOP 3-5)             │
    │  • ⚠️  일정 충돌 항목                 │
    │  • ❓ 확인 필요 항목                  │
    │                                        │
    │  출력: kakao_brief_{date}.md          │
    │  + kakao_send_log_{date}.json         │
    │                                        │
    │  MVP: 메시지 파일 생성                │
    │  (향후 실제 Kakao API 연동)           │
    └────────────────────────────────────────┘
                ↓
                ↓ (사용자 알림)
                ↓
    [사용자 확인 후 Notion에서 상태 선택]
                ↓
            [Loop 반복]

```

---

## 2️⃣ 타임라인 뷰

```
┌──────────────────────────────────────────────────────────────────┐
│  시간대별 자동화 스케줄                                          │
└──────────────────────────────────────────────────────────────────┘

[Day 0]
  08:00:00
    ├─ Source Collector Agent 트리거
    │  └─ 7개 사이트 순회 → URL 수집
    │
    └─ Kakao Report Agent 트리거
       └─ 어제 분석 결과 보고 생성

[Day 0 - Continuous]
  00:00~23:59
    ├─ Multi-pass Parser Agent (수집된 URL 처리)
    │  └─ HTML, OCR, Vision 3단계 파싱
    │
    ├─ Fit & Priority Agent (파싱 완료 공고 분석)
    │  └─ 적합도 점수 & 우선순위 계산
    │
    ├─ Notion Dashboard Agent (1분 주기 모니터링)
    │  └─ 카드 생성/갱신 & Accept 감지
    │
    └─ Calendar Scheduler Agent (Accept 신호 대기)
       └─ 일정 생성 & Calendar 반영

[Day 1]
  08:00:00
    └─ [위의 Day 0 반복]

```

---

## 3️⃣ 데이터 흐름 (Data Flow)

```
┌─────────────────────────────────────────────────────────────────┐
│ 각 Agent 간 데이터 교환                                         │
└─────────────────────────────────────────────────────────────────┘

프로필
  user_profile_{user_id}.json
  ├─ basic_info (이름, 학과, 학년)
  ├─ interests (관심 분야)
  ├─ career_goal (희망 직무)
  ├─ preferences (활동 선호도)
  └─ availability (보고 시간)
       ↓
       ↓ (fit-priority-agent 입력)

공고 URL 목록
  daily_collection_{date}.json
  ├─ sites[] (사이트별 수집 결과)
  └─ new_urls[] (신규 URL 배열)
       ↓
       ↓ (multipass-parser-agent 입력)

파싱된 공고
  parsed_opportunity_{id}.json
  ├─ basic_info (제목, 범주, 주최)
  ├─ schedule (마감, 행사일)
  ├─ details (자격, 혜택, 연락처)
  ├─ extraction_metadata (근거, 신뢰도)
  └─ validation_status (충돌, 검증 필요)
       ↓
       ↓ (fit-priority-agent 입력)

추천 정보
  recommended_opportunity_{id}.json
  ├─ fit_score (0-100)
  ├─ fit_breakdown (항목별 점수)
  ├─ priority (긴급/중요/참고)
  ├─ recommendation_reason (추천 이유)
  ├─ eligibility_status (참가 가능 여부)
  └─ calendar_conflict_status (일정 충돌)
       ↓
       ↓ (notion-dashboard-agent 입력)

Notion 카드
  (Notion Database)
  ├─ Title: 프로그램명
  ├─ Poster: 포스터 이미지 URL
  ├─ Link: 원문 링크
  ├─ Fit Score: 적합도 점수
  ├─ Priority: 우선순위
  ├─ Status: New/Recommended/Accept/Hold/Reject/Scheduled
  ├─ Deadline: 마감일
  ├─ Event Date: 행사일
  └─ Timely ID: 내부 연동 키
       ↓
       ↓ (사용자 수정: Status = "Accept")
       ↓

Accept 신호
  {
    opportunity_id: "opp_xxx",
    status_old: "Recommended",
    status_new: "Accept",
    timestamp: "2026-07-02T15:30:00+09:00"
  }
       ↓
       ↓ (calendar-scheduler-agent 입력)

Google Calendar 이벤트
  [마감일 일정]
  [행사일 일정]
  [준비 일정 D-5~D-1]
  + 충돌 검사 결과
       ↓
       ↓ (Notion Status 업데이트)
       ↓

최종 상태
  Notion Status = "Scheduled"
  Google Calendar = 일정 추가됨
  Kakao 보고 = 다음 일일 보고에 포함

```

---

## 4️⃣ 데이터 저장소 구조

```
workspace/
├─ ./.pi/
│  ├─ agents/ (7개 Agent 정의)
│  │  ├─ profile-agent/{AGENT.md}
│  │  ├─ source-collector-agent/{AGENT.md}
│  │  ├─ multipass-parser-agent/{AGENT.md}
│  │  ├─ fit-priority-agent/{AGENT.md}
│  │  ├─ notion-dashboard-agent/{AGENT.md}
│  │  ├─ calendar-scheduler-agent/{AGENT.md}
│  │  └─ kakao-report-agent/{AGENT.md}
│  │
│  └─ skills/ (14개 워크플로우 Skill 정의)
│     ├─ profile-build/{SKILL.md, spec.md}
│     ├─ interest-keyword-expand/{SKILL.md, spec.md}
│     ├─ source-watchlist-crawl/{SKILL.md, spec.md}
│     ├─ html-opportunity-parse/{SKILL.md, spec.md}
│     ├─ rendered-page-ocr/{SKILL.md, spec.md}
│     ├─ poster-vision-extract/{SKILL.md, spec.md}
│     ├─ schema-merge-and-validate/{SKILL.md, spec.md}
│     ├─ fit-score-rank/{SKILL.md, spec.md}
│     ├─ deadline-priority-rank/{SKILL.md, spec.md}
│     ├─ notion-dashboard-sync/{SKILL.md, spec.md}
│     ├─ calendar-freebusy-check/{SKILL.md, spec.md}
│     ├─ calendar-event-create/{SKILL.md, spec.md}
│     ├─ kakao-brief-generate/{SKILL.md, spec.md}
│     └─ accept-state-sync/{SKILL.md, spec.md}
│
├─ ./data/ (런타임 데이터)
│  ├─ profiles/
│  │  └─ user_profile_*.json
│  ├─ collections/
│  │  └─ daily_collection_*.json
│  ├─ parsed/
│  │  └─ parsed_opportunity_*.json
│  ├─ recommended/
│  │  └─ recommended_opportunity_*.json
│  ├─ calendar/
│  │  └─ calendar_event_created_*.json
│  ├─ kakao/
│  │  ├─ kakao_brief_*.md
│  │  └─ kakao_send_log_*.json
│  └─ logs/
│     └─ *.json
│
└─ ./WORKFLOW_ARCHITECTURE.md (이 파일)
```

---

## 5️⃣ 의존성 & 트리거 정의

```
┌──────────────────────────────────────────────────────────────────┐
│ Agent 간 의존성 그래프                                           │
└──────────────────────────────────────────────────────────────────┘

[프로필 초기화]
  profile-agent (수동 트리거)
    │
    └─→ profile-build Skill

[자동 수집 및 처리]
  source-collector-agent (Scheduler: 매일 08:00)
    │
    └─→ source-watchlist-crawl Skill
        │
        ↓ (URL 목록)
        │
  multipass-parser-agent (자동 트리거)
    │
    ├─→ html-opportunity-parse Skill
    ├─→ rendered-page-ocr Skill
    ├─→ poster-vision-extract Skill
    └─→ schema-merge-and-validate Skill
        │
        ↓ (구조화된 공고)
        │
  fit-priority-agent (자동 트리거)
    │
    ├─→ interest-keyword-expand Skill
    ├─→ fit-score-rank Skill
    └─→ deadline-priority-rank Skill
        │
        ↓ (적합도 & 우선순위)
        │
  notion-dashboard-agent (자동 트리거 + 1분 모니터링)
    │
    ├─→ notion-dashboard-sync Skill (카드 생성/갱신)
    │
    └─→ [Accept 신호 감지]
        │
        ↓ (Accept 신호)
        │
  calendar-scheduler-agent (Accept 신호 트리거)
    │
    ├─→ calendar-freebusy-check Skill (충돌 검사)
    ├─→ calendar-event-create Skill (일정 생성)
    └─→ accept-state-sync Skill (상태 동기화)
        │
        ↓ (Calendar 업데이트 + Notion Status 변경)
        │
  kakao-report-agent (Scheduler: 매일 08:00)
    │
    └─→ kakao-brief-generate Skill (메시지 생성)

```

---

## 6️⃣ 에러 처리 & 예외 상황

```
┌──────────────────────────────────────────────────────────────────┐
│ 각 단계별 에러 처리 전략                                         │
└──────────────────────────────────────────────────────────────────┘

[수집 단계]
  ├─ 사이트 접근 실패
  │  └─ source_watchlist.failure_reason 기록
  │  └─ status = "failure" 표시
  │
  ├─ URL 수집 0개
  │  └─ daily_collection에 empty 기록
  │  └─ 다음 사이클 재시도
  │
  └─ 타임아웃 (30초)
     └─ parse_status = "timeout"

[파싱 단계]
  ├─ HTML 파싱 실패
  │  └─ next_method로 진행 (OCR)
  │
  ├─ 모든 방법 실패
  │  └─ status = "parse_failed"
  │  └─ 수동 검토 큐에 추가
  │
  ├─ 필드 충돌 (HTML ≠ OCR)
  │  └─ conflict = true
  │  └─ validation_status = "needs_review"
  │  └─ 자동 확정 금지
  │
  └─ 불명확한 정보
     └─ confidence < 60% → "확인 필요" 표시
     └─ 임의로 보충하지 않음

[추천 단계]
  ├─ 프로필 데이터 누락
  │  └─ eligibility_status = "needs_check"
  │
  ├─ 점수 계산 오류
  │  └─ fit_score = 0 (재계산 트리거)
  │
  └─ 키워드 확장 실패
     └─ base_keywords만 사용

[Notion 동기화]
  ├─ API 실패
  │  └─ retry_count 증가
  │  └─ 최대 3회 재시도 후 로그 기록
  │
  ├─ 중복 카드 감지
  │  └─ update only (생성 금지)
  │
  └─ 권한 오류
     └─ 에러 로그 기록
     └─ 사용자 알림

[Calendar 동기화]
  ├─ 일정 충돌 감지
  │  └─ conflict_status = "conflict"
  │  └─ calendar_status = "blocked"
  │  └─ 사용자에게 알림
  │
  ├─ 마감일 불명확
  │  └─ calendar_status = "needs_review"
  │  └─ 일정 생성 보류
  │
  └─ Google API 오류
     └─ retry_count 증가
     └─ 최대 3회 재시도

[Kakao 보고]
  ├─ 메시지 생성 실패
  │  └─ kakao_send_log.status = "failed"
  │
  ├─ Kakao API 인증 실패
  │  └─ 메시지 파일로 저장 (MVP)
  │
  └─ 전송 실패
     └─ 큐 유지 (다음 보고에 포함)

```

---

## 7️⃣ 상태 전이 (State Machine)

```
┌──────────────────────────────────────────────────────────────────┐
│ Notion Status 상태 전이도                                        │
└──────────────────────────────────────────────────────────────────┘

                    [시작]
                      │
                      ↓
                  ┌───────┐
                  │ "New" │ (공고 생성됨)
                  └───────┘
                      │
         (자동분석)    │
                      ↓
              ┌──────────────┐
              │"Recommended" │ (추천 완료)
              └──────────────┘
               ↙   ↓   ↖
              /    |    \
            /      |     \
         [Accept] [Hold] [Reject]
           /        |       \
          /         |        \
         ↓          ↓         ↓
      ┌─────┐   ┌──────┐  ┌────────┐
      │Accept│  │ Hold │  │ Reject │ (종료)
      └─────┘   └──────┘  └────────┘
         │         │
         │ (Calendar) │
         │         └─→ [제외]
         │
         ↓
    ┌──────────┐
    │Scheduled │ (일정화 완료)
    └──────────┘

상태 설명:
  • New: 새 공고 발견
  • Recommended: 추천 점수 & 우선순위 계산 완료
  • Accept: 사용자가 진행 결정
  • Hold: 나중에 재검토 예정
  • Reject: 사용자가 제외
  • Conflict: 일정 충돌 (수동 검토 필요)
  • Scheduled: Google Calendar 일정 반영 완료

전이 규칙:
  • New → Recommended: 자동 (분석 완료)
  • Recommended → Accept: 사용자 (Notion 카드 클릭)
  • Recommended → Hold: 사용자 (나중에 검토)
  • Recommended → Reject: 사용자 (제외)
  • Accept → Scheduled: 자동 (Calendar 반영 완료)
  • Accept → Conflict: 자동 (일정 충돌 감지 시)
  • Conflict → Accept (수동 해결): 사용자
  • 모든 상태 → Scheduled: Calendar 반영 후
```

---

## 8️⃣ 성능 & 처리량 가정

```
┌──────────────────────────────────────────────────────────────────┐
│ 예상 처리량 및 시간                                             │
└──────────────────────────────────────────────────────────────────┘

[일일 수집 범위]
  • 7개 사이트 순회: ~5-10분
  • 신규 공고 예상: 5-20개/일

[파싱 시간]
  • 공고당 1차(HTML) 파싱: ~3초
  • 공고당 2차(OCR) 파싱: ~5-10초
  • 공고당 3차(Vision) 파싱: ~5초
  • 공고당 총합: ~15-20초
  • 20개 공고 파싱: ~5-6분

[추천 계산]
  • 공고당 적합도 계산: ~1초
  • 20개 공고: ~20초

[Notion 동기화]
  • 카드 생성: ~1초/개
  • 카드 갱신: ~0.5초/개
  • Status 모니터링: ~2-3초/회 (1분 주기)

[Calendar 생성]
  • Accept당 일정 5개 생성: ~5초
  • 충돌 검사: ~2초/회

[총 일일 처리 시간]
  • 08:00 트리거 → 15분 이내 완료
  • 나머지 23시간: 실시간 처리 (1분 주기 모니터링)

[병렬 처리]
  • 여러 공고 동시 파싱 가능 (권장: 3-5개 병렬)
  • Notion 모니터링은 독립적으로 수행
  • Calendar 생성은 Accept 신호 감지 후 즉시 수행

```

---

## 🎯 요약

| 항목 | 내용 |
|------|------|
| **Agent 수** | 7개 |
| **Skill 수** | 14개 워크플로우 Skill |
| **자동화 포인트** | 3개 (수집, 분석, 일일보고) |
| **수동 개입 포인트** | 1개 (Notion에서 Accept/Hold/Reject 선택) |
| **주요 트리거** | Scheduler (08:00), Notion Status (Accept 감지), 자동 연쇄 |
| **데이터 저장소** | ./.pi/ (정의), ./data/ (런타임) |
| **에러 처리** | 로깅 + 재시도 + 수동 검토 큐 |
| **상태 추적** | Notion Status + 내부 workflow 필드 |
| **확장성** | 각 Agent/Skill 독립적으로 업데이트 가능 |

