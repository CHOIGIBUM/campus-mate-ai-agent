# Agent - Skill 매핑 정의

## 📌 전체 매핑 요약

| Agent | 역할 | 사용 Skills | 의존 Agent | 트리거 |
|------|------|-----------|-----------|--------|
| **profile-agent** | 프로필 관리 | profile-build | 없음 | 수동 (온보딩) |
| **source-collector-agent** | 공고 수집 | source-watchlist-crawl | 없음 | Scheduler (08:00) |
| **multipass-parser-agent** | 3단계 파싱 | html-opportunity-parse, rendered-page-ocr, poster-vision-extract, schema-merge-and-validate | source-collector-agent | 자동 (URL 수집 후) |
| **fit-priority-agent** | 개인화 추천 | interest-keyword-expand, fit-score-rank, deadline-priority-rank | multipass-parser-agent, profile-agent | 자동 (파싱 완료 후) |
| **notion-dashboard-agent** | Notion 관리 | notion-dashboard-sync, accept-state-sync | fit-priority-agent | 자동 (추천 완료 후) + 1분 모니터링 |
| **calendar-scheduler-agent** | Calendar 일정 | calendar-freebusy-check, calendar-event-create | notion-dashboard-agent | Notion Accept 신호 감지 |
| **kakao-report-agent** | 일일 보고 | kakao-brief-generate | 모든 Agent (정보 수집) | Scheduler (08:00) |

---

## 1️⃣ Profile Agent

### 역할
사용자의 온보딩 정보를 수집하고 구조화

### 사용 Skills

#### Skill #1: profile-build
```
목적: 사용자 입력을 JSON으로 정규화
입력:
  {
    "name": "최기범",
    "school": "강원대학교",
    "major": "AI융합학과",
    "year": "2학년",
    "interests": ["의료AI", "데이터 분석"],
    "positions": ["AI 개발자"],
    "activity_types": ["해커톤", "공모전"],
    "regions": ["강원", "서울"],
    "available_hours_per_week": 5,
    "report_time": "08:00"
  }

출력:
  user_profile_user_20260702_001.json
  {
    "user_id": "user_20260702_001",
    "basic_info": {...},
    "interests": {...},
    "career_goal": {...},
    "preferences": {...},
    "availability": {...},
    "metadata": {...}
  }

저장 경로: ./data/profiles/
```

### 데이터 저장소
```
./data/profiles/
├─ user_profile_user_20260702_001.json
├─ user_profile_user_20260703_002.json
└─ ...
```

---

## 2️⃣ Source Collector Agent

### 역할
매일 7개 사이트에서 신규 공고 URL 수집

### 사용 Skills

#### Skill #1: source-watchlist-crawl
```
목적: 사이트 순회 & URL 추출
입력:
  {
    "sites": [
      {
        "site_name": "링커리어",
        "source_url": "https://www.linkareer.com",
        "crawl_selector": "a.opportunity-card"
      },
      {
        "site_name": "씽굿",
        "source_url": "https://www.thinggood.com",
        "crawl_selector": "div.job-item"
      },
      ...
    ],
    "existing_urls": [URL 배열 from 어제 수집 결과],
    "max_timeout": 30
  }

출력:
  daily_collection_2026-07-02.json
  {
    "collection_date": "2026-07-02",
    "collection_time": "08:00:00+09:00",
    "total_urls_collected": 47,
    "unique_urls_new": 12,
    "site_status": [
      {
        "site_name": "링커리어",
        "parse_status": "success",
        "last_success_at": "2026-07-02T08:05:00+09:00",
        "urls_found": 15,
        "new_urls_count": 3
      },
      ...
    ],
    "new_urls": [
      {
        "site_name": "링커리어",
        "source_url": "https://www.linkareer.com/opp_xxx",
        "collected_at": "2026-07-02T08:05:00+09:00"
      },
      ...
    ]
  }

저장 경로: ./data/collections/
```

### 데이터 저장소
```
./data/collections/
├─ daily_collection_2026-07-02.json
├─ daily_collection_2026-07-03.json
├─ source_watchlist.json (사이트별 이력)
└─ ...
```

### source_watchlist.json 구조
```json
{
  "sites": [
    {
      "site_name": "링커리어",
      "site_type": "job_board",
      "parse_status": "success",
      "last_success_at": "2026-07-02T08:05:00+09:00",
      "failure_reason": null,
      "collected_count": 145,
      "last_failure_at": null
    }
  ]
}
```

---

## 3️⃣ Multi-pass Parser Agent

### 역할
수집된 URL을 3가지 방식으로 파싱하고 결과 병합

### 사용 Skills (순차 실행)

#### Skill #1: html-opportunity-parse
```
목적: HTML 본문에서 공고 정보 추출
입력:
  {
    "opportunity_url": "https://dacon.io/competitions/xxx",
    "site_name": "Dacon"
  }

출력:
  {
    "parse_method": "html",
    "extracted_fields": {
      "title": {
        "value": "의료 데이터 AI 해커톤",
        "evidence": "<h1>의료 데이터 AI 해커톤</h1>",
        "confidence": 95
      },
      "submission_deadline": {
        "value": "2026-07-15T23:59:00+09:00",
        "evidence": "마감: 2026-07-15 23:59",
        "confidence": 90
      },
      ...
    },
    "status": "success"
  }

처리 시간: ~3초
```

#### Skill #2: rendered-page-ocr
```
목적: 렌더링/PDF/OCR로 HTML 누락 정보 보완
입력:
  {
    "opportunity_url": "https://dacon.io/competitions/xxx",
    "html_result": {...}, (1차 결과와 비교)
    "timeout": 10
  }

출력:
  {
    "parse_method": "rendered_ocr",
    "extracted_fields": {
      "submission_deadline": {
        "value": "2026-07-15T23:59:00+09:00",
        "evidence": "OCR: 마감: 7월 15일 23:59",
        "confidence": 75
      },
      ...
    },
    "status": "success"
  }

처리 시간: ~5-10초
```

#### Skill #3: poster-vision-extract
```
목적: 포스터 이미지에서 정보 추출
입력:
  {
    "opportunity_url": "https://dacon.io/competitions/xxx",
    "image_urls": ["https://example.com/poster.png"],
    "vision_api": "claude_vision"
  }

출력:
  {
    "parse_method": "vision",
    "extracted_fields": {
      "organizer": {
        "value": "데이콘",
        "evidence": "포스터 이미지 텍스트: 주최: 데이콘",
        "confidence": 85
      },
      "deadline": {
        "value": "2026-07-15T23:59:00+09:00",
        "evidence": "마감: 7/15 23:59",
        "confidence": 80
      },
      ...
    },
    "status": "success"
  }

처리 시간: ~5초
```

#### Skill #4: schema-merge-and-validate
```
목적: 3단계 결과 병합 & 검증
입력:
  {
    "opportunity_id": "opp_20260702_001",
    "html_result": {...},
    "ocr_result": {...},
    "vision_result": {...}
  }

출력:
  parsed_opportunity_20260702_001.json
  {
    "opportunity_id": "opp_20260702_001",
    "raw_source": {
      "source_name": "Dacon",
      "source_url": "https://dacon.io/...",
      "collected_at": "2026-07-02T08:15:00+09:00",
      "parse_methods_used": ["html", "rendered_pdf_ocr", "poster_vision"]
    },
    "basic_info": {
      "title": "의료 데이터 AI 해커톤",
      "category": "해커톤",
      "organizer": "데이콘",
      "target_user": "대학생 및 대학원생",
      "location": "온라인",
      "online_offline": "online"
    },
    "schedule": {
      "recruitment_start": "2026-07-01",
      "recruitment_end": "2026-07-15T23:59:00+09:00",
      "submission_deadline": "2026-07-15T23:59:00+09:00",
      "event_start": "2026-07-22T10:00:00+09:00",
      "event_end": "2026-07-22T18:00:00+09:00"
    },
    "details": {
      "summary": "의료 데이터를 활용한 AI 아이디어 및 모델 개발 해커톤",
      "eligibility": "대학생 및 대학원생",
      "required_materials": ["참가 신청서", "아이디어 기획서"],
      "benefits": ["상금", "수료증", "멘토링"],
      "award": "확인 필요",
      "application_method": "온라인 접수",
      "contact": "확인 필요"
    },
    "extraction_metadata": {
      "title": {
        "source_method": "html",
        "evidence": "<h1>의료 데이터 AI 해커톤</h1>",
        "confidence": 95
      },
      "submission_deadline": {
        "source_method": "html",
        "evidence": "마감: 2026-07-15 23:59",
        "confidence": 90,
        "conflict": {
          "ocr_value": "2026-07-15T23:59:00+09:00",
          "vision_value": "2026-07-15T23:59:00+09:00",
          "status": "no_conflict"
        }
      },
      ...
    },
    "validation_status": {
      "conflict": false,
      "needs_review": false,
      "review_note": null
    }
  }

저장 경로: ./data/parsed/
처리 시간: ~1초 (병합만)
```

### 데이터 저장소
```
./data/parsed/
├─ parsed_opportunity_20260702_001.json
├─ parsed_opportunity_20260702_002.json
└─ ...
```

---

## 4️⃣ Fit & Priority Agent

### 역할
파싱된 공고를 사용자 프로필과 비교하여 점수 & 우선순위 계산

### 사용 Skills (순차 실행)

#### Skill #1: interest-keyword-expand
```
목적: 관심 분야 키워드 확장
입력:
  {
    "user_id": "user_20260702_001",
    "base_fields": ["의료AI", "데이터 분석", "AI Agent"]
  }

출력:
  {
    "user_id": "user_20260702_001",
    "expanded_keywords": {
      "의료AI": [
        "의료AI", "헬스케어", "의료 기술", "바이오",
        "medical AI", "healthcare", "health tech"
      ],
      "데이터 분석": [
        "데이터 분석", "빅데이터", "데이터 엔지니어",
        "data analysis", "data science"
      ],
      "AI Agent": [
        "AI Agent", "자동화", "LLM", "챗봇",
        "agentic", "automation"
      ]
    },
    "all_keywords_flattened": [...]
  }

저장 경로: ./data/profiles/ (프로필 업데이트)
처리 시간: ~1초
```

#### Skill #2: fit-score-rank
```
목적: 6가지 항목별 점수 계산 (총 0-100)
입력:
  {
    "user_profile": {...},
    "parsed_opportunity": {...}
  }

출력:
  {
    "fit_score": 88,
    "fit_breakdown": [
      {
        "category": "전공 적합도",
        "max_score": 25,
        "earned": 20,
        "reason": "AI융합학과 ↔ 해커톤 분야 직접 관련"
      },
      {
        "category": "관심 분야 적합도",
        "max_score": 25,
        "earned": 25,
        "reason": "의료AI, 데이터 분석 키워드 완전 일치"
      },
      {
        "category": "희망 직무 적합도",
        "max_score": 20,
        "earned": 18,
        "reason": "AI 개발자 역량 개발 기회"
      },
      {
        "category": "참가 자격 적합도",
        "max_score": 15,
        "earned": 15,
        "reason": "대학생 조건 완전 충족"
      },
      {
        "category": "일정 가능성",
        "max_score": 10,
        "earned": 10,
        "reason": "마감 D-5, 즉시 준비 필요"
      },
      {
        "category": "지역/온오프라인",
        "max_score": 5,
        "earned": 0,
        "reason": "온라인 행사, 지역 제한 없음"
      }
    ]
  }

저장 경로: ./data/recommended/ (다음 Skill로 전달)
처리 시간: ~1초
```

#### Skill #3: deadline-priority-rank
```
목적: 우선순위 분류 (긴급/중요/참고)
입력:
  {
    "fit_score": 88,
    "submission_deadline": "2026-07-07T23:59:00+09:00",
    "today": "2026-07-02",
    "user_profile": {...}
  }

출력:
  {
    "priority": "긴급",
    "d_day": 5,
    "priority_reason": "D-5 (7일 이내) AND fit_score 88점 (75점 이상)",
    "priority_category": "긴급 (D-7 이내 AND 적합도 75점 이상)",
    "timeline": {
      "today": "2026-07-02",
      "d_minus_7": "2026-06-30",
      "d_minus_5": "2026-07-02",
      "d_day": "2026-07-07"
    }
  }

저장 경로: ./data/recommended/ (최종 추천 정보)
처리 시간: ~0.5초
```

### 최종 출력
```
./data/recommended/
├─ recommended_opportunity_20260702_001.json
└─ {...merged with parsed_opportunity + fit_breakdown + priority}
```

### recommended_opportunity 최종 구조
```json
{
  "opportunity_id": "opp_20260702_001",
  "raw_source": {...},
  "basic_info": {...},
  "schedule": {...},
  "details": {...},
  "extraction_metadata": {...},
  "validation_status": {...},
  "personalization": {
    "user_id": "user_20260702_001",
    "fit_score": 88,
    "fit_breakdown": [...],
    "priority": "긴급",
    "d_day": 13,
    "priority_reason": "...",
    "recommendation_reason": [
      "AI융합학과, 의료AI, 데이터 분석 관심 분야와 관련",
      "대학생 참가 가능",
      "마감까지 D-5, 즉시 준비 필요"
    ],
    "eligibility_status": "가능",
    "calendar_conflict_status": "no_conflict"
  }
}
```

---

## 5️⃣ Notion Dashboard Agent

### 역할
추천 정보를 Notion에 카드로 생성/갱신하고 Accept 신호 감지

### 사용 Skills

#### Skill #1: notion-dashboard-sync
```
목적: Notion API 호출하여 카드 생성/갱신 및 Status 모니터링
입력:
  {
    "notion_integration_token": "secret_...",
    "database_id": "123...",
    "opportunity": {...},  // recommended_opportunity JSON
    "action": "create" | "update"
  }

출력 (카드 생성):
  {
    "action": "created",
    "notion_page_id": "abc123def456",
    "status": "New",
    "timestamp": "2026-07-02T08:30:00+09:00",
    "properties": {
      "Title": "의료 데이터 AI 해커톤",
      "Poster": "https://example.com/poster.png",
      "원문 링크": "https://dacon.io/competitions/xxx",
      "유형": "해커톤",
      "출처": "데이콘",
      "적합도": 88,
      "우선순위": "긴급",
      "마감일": "2026-07-15",
      "행사일": "2026-07-22",
      "참가 가능": "가능",
      "일정 충돌": "없음",
      "상태": "New",
      "추천 이유": "AI융합학과, 의료AI, 데이터 분석 관심 분야와 관련",
      "Timely ID": "opp_20260702_001"
    }
  }

저장 경로: ./data/logs/notion_sync_log_{date}.json
처리 시간: ~1초

[모니터링 프로세스]
매 1분마다:
  ├─ Notion Database 쿼리
  │  └─ WHERE status != null
  │
  ├─ 이전 상태와 비교
  │  └─ Status 변경 감지
  │
  └─ 변경 감지 시 처리:
     • New → Recommended: 자동 (추천 완료)
     • Recommended → Accept: ← 중요!
     • Recommended → Hold: 보류 처리
     • Recommended → Reject: 제외 처리
     • Accept → Scheduled: Calendar 반영 후
```

#### Skill #2: accept-state-sync
```
목적: Accept 신호를 Timely 내부 상태로 동기화
입력:
  {
    "opportunity_id": "opp_20260702_001",
    "notion_page_id": "abc123def456",
    "status_old": "Recommended",
    "status_new": "Accept",
    "timestamp": "2026-07-02T15:30:00+09:00"
  }

출력:
  {
    "sync_status": "success",
    "opportunity_id": "opp_20260702_001",
    "workflow_status": "pending_calendar_creation",
    "trigger_calendar_scheduler": true,
    "internal_state_updated": true
  }

처리 시간: ~0.5초
```

### 데이터 저장소
```
./data/logs/
├─ notion_sync_log_2026-07-02.json
├─ notion_sync_log_2026-07-03.json
└─ ...

notion_sync_log 구조:
{
  "date": "2026-07-02",
  "syncs": [
    {
      "timestamp": "2026-07-02T08:30:00+09:00",
      "sync_type": "create",
      "opportunity_id": "opp_20260702_001",
      "action": "created",
      "notion_page_id": "abc123",
      "status": "New"
    },
    {
      "timestamp": "2026-07-02T15:30:00+09:00",
      "sync_type": "status_change",
      "opportunity_id": "opp_20260702_001",
      "status_old": "Recommended",
      "status_new": "Accept",
      "trigger_calendar": true
    }
  ]
}
```

---

## 6️⃣ Calendar Scheduler Agent

### 역할
Accept된 공고의 일정을 Google Calendar에 생성하고 충돌 검사

### 사용 Skills

#### Skill #1: calendar-freebusy-check
```
목적: 기존 일정과 충돌 검사
입력:
  {
    "google_calendar_token": "...",
    "events_to_check": [
      {
        "event_name": "의료 데이터 AI 해커톤 - 행사",
        "start_time": "2026-07-22T10:00:00+09:00",
        "end_time": "2026-07-22T18:00:00+09:00"
      }
    ],
    "min_overlap_duration": 3600  // 1시간 이상
  }

출력:
  {
    "conflict_status": "no_conflict",
    "busy_events": [],
    "available_slots": [
      {
        "start": "2026-07-22T00:00:00+09:00",
        "end": "2026-07-22T10:00:00+09:00"
      },
      {
        "start": "2026-07-22T18:00:00+09:00",
        "end": "2026-07-23T00:00:00+09:00"
      }
    ]
  }

또는 (충돌 있을 때):
  {
    "conflict_status": "conflict",
    "busy_events": [
      {
        "event_name": "기존 미팅",
        "start_time": "2026-07-22T09:00:00+09:00",
        "end_time": "2026-07-22T11:00:00+09:00"
      }
    ]
  }

처리 시간: ~2초
```

#### Skill #2: calendar-event-create
```
목적: Google Calendar에 일정 생성
입력:
  {
    "google_calendar_token": "...",
    "events": [
      {
        "event_type": "deadline",
        "event_name": "의료 데이터 AI 해커톤 - 마감",
        "start": "2026-07-15T23:59:00+09:00",
        "end": "2026-07-16T00:00:00+09:00",
        "description": "온라인 접수 마감\n참가 자격: 대학생 및 대학원생\n문의: ..."
      },
      {
        "event_type": "event",
        "event_name": "의료 데이터 AI 해커톤 - 행사",
        "start": "2026-07-22T10:00:00+09:00",
        "end": "2026-07-22T18:00:00+09:00",
        "location": "온라인 (Zoom)",
        "description": "의료 데이터를 활용한 AI 아이디어 및 모델 개발\n준비물: ...\n링크: ..."
      },
      {
        "event_type": "prep",
        "event_name": "팀원 모집 및 아이디어 회의",
        "start": "2026-07-10T19:00:00+09:00",
        "end": "2026-07-10T21:00:00+09:00",
        "description": "D-5: 팀원 모집 시작, 아이디어 브레인스토밍"
      },
      {
        "event_type": "prep",
        "event_name": "기획서 작성",
        "start": "2026-07-11T19:00:00+09:00",
        "end": "2026-07-11T21:00:00+09:00",
        "description": "D-4: 아이디어 회의 결과 정리, 기획서 작성"
      },
      ...
    ]
  }

출력:
  {
    "created_events": [
      {
        "event_type": "deadline",
        "google_event_id": "abc123xyz",
        "status": "created"
      },
      {
        "event_type": "event",
        "google_event_id": "def456uvw",
        "status": "created"
      },
      ...
    ],
    "total_events_created": 5
  }

저장 경로: ./data/calendar/
처리 시간: ~5초 (5개 이벤트)
```

### 데이터 저장소
```
./data/calendar/
├─ calendar_event_created_20260702_001.json
├─ calendar_event_created_20260702_002.json
└─ ...

calendar_event_created 구조:
{
  "opportunity_id": "opp_20260702_001",
  "opportunity_title": "의료 데이터 AI 해커톤",
  "user_id": "user_20260702_001",
  "events_created": [
    {
      "event_type": "deadline|event|prep",
      "event_name": "...",
      "start_time": "2026-07-15T23:59:00+09:00",
      "end_time": "...",
      "google_calendar_event_id": "abc123",
      "calendar_status": "created"
    }
  ],
  "conflict_status": "no_conflict|conflict|blocked",
  "conflict_details": null,
  "timeline": {
    "d_minus_5": "2026-07-10",
    "d_minus_1": "2026-07-14",
    "d_day": "2026-07-15"
  }
}
```

---

## 7️⃣ Kakao Report Agent

### 역할
매일 신규 추천, 긴급 마감, 충돌, 확인 필요 항목을 메시지로 보고

### 사용 Skills

#### Skill #1: kakao-brief-generate
```
목적: Kakao 보고 메시지 생성
입력:
  {
    "user_name": "최기범",
    "user_id": "user_20260702_001",
    "report_date": "2026-07-02",
    "new_recommendations": [
      {
        "opportunity_id": "opp_20260702_001",
        "title": "의료 데이터 AI 해커톤",
        "fit_score": 88,
        "priority": "긴급",
        "d_day": 5,
        "reason": "AI융합학과, 의료AI 관심 분야와 관련"
      },
      ...
    ],
    "urgent_deadlines": [
      // D-7 이내
    ],
    "conflicts": [
      // Calendar 충돌 항목
    ],
    "needs_review": [
      // 날짜, 자격 불명확 항목
    ],
    "notion_url": "https://notion.so/..."
  }

출력:
  kakao_brief_2026-07-02.md
  
  # [Campus Career AI] 최기범님 기준 오늘의 공모전 브리핑

  ## 🔥 긴급 마감
  - 의료 데이터 AI 해커톤 (D-5) | 온라인 해커톤

  ## ⭐ 신규 추천 (3건)
  1. 의료 데이터 AI 해커톤 — 의료AI, 데이터 분석 관심 분야 (적합도 88점)
  2. 강원 데이터 분석 경진대회 — 데이터 분석 역무 (적합도 84점)
  3. 링커리어 공모전 — AI 기술 활용 (적합도 78점)

  ## ⚠️ 일정 충돌
  - 의료 AI 해커톤 행사일(7/22 10:00–18:00)과 기존 미팅 충돌 확인 필요

  ## ❓ 확인 필요
  - 강원 공유대학: 수강 대상 학년 미명확
  - 링커리어 공모전: 상금 규모 확인 필요

  ---

  👉 [Notion 현황판에서 Accept/Hold/Reject 선택](https://notion.so/...)

저장 경로: ./data/kakao/
처리 시간: ~2초

로그 출력:
  kakao_send_log_2026-07-02.json
  {
    "date": "2026-07-02",
    "scheduled_time": "08:00",
    "actual_generated_time": "2026-07-02T08:00:00+09:00",
    "user_id": "user_20260702_001",
    "recipient_name": "최기범",
    "status": "generated",
    "send_method": "file_save",
    "file_path": "kakao_brief_2026-07-02.md",
    "message_length": 547,
    "urgent_count": 1,
    "new_recommendation_count": 3,
    "conflict_count": 1,
    "review_needed_count": 2,
    "note": "MVP: 메시지 파일 저장. 향후 Kakao API 연동"
  }
```

### 데이터 저장소
```
./data/kakao/
├─ kakao_brief_2026-07-02.md
├─ kakao_brief_2026-07-03.md
├─ kakao_send_log_2026-07-02.json
├─ kakao_send_log_2026-07-03.json
└─ ...
```

---

## 📊 Summary Table

| Agent | Skills | 입력 | 출력 | 저장소 | 처리시간 |
|------|--------|------|------|--------|---------|
| **profile** | 1개 | 사용자 입력 | user_profile.json | ./data/profiles/ | - |
| **source-collector** | 1개 | Source Watchlist | daily_collection.json | ./data/collections/ | 5-10분 |
| **multipass-parser** | 4개 | URL 목록 | parsed_opportunity.json | ./data/parsed/ | 20초/공고 |
| **fit-priority** | 3개 | parsed + profile | recommended.json | ./data/recommended/ | 3초/공고 |
| **notion-dashboard** | 2개 | recommended | notion_sync_log | ./data/logs/ | 1초/카드 |
| **calendar-scheduler** | 2개 | Accept 신호 | calendar_event.json | ./data/calendar/ | 5초/공고 |
| **kakao-report** | 1개 | 전체 현황 | kakao_brief.md | ./data/kakao/ | 2초 |

