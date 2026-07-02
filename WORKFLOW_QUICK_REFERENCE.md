# Campus Career AI - 워크플로우 빠른 참조

## 🎯 한 눈에 보기

### 일일 타임라인

```
08:00:00
  ├─ Source Collector Agent 시작 (공고 수집)
  │  └─ 10분 내 완료: 신규 URL 목록 생성
  │
  └─ Kakao Report Agent 시작 (어제 분석 결과 보고)
     └─ 메시지 파일 생성

08:10~08:20
  ├─ Multi-pass Parser Agent 시작 (수집 URL 파싱)
  │  └─ HTML → OCR → Vision 3단계 순차 처리
  │  └─ 공고당 ~20초
  │
  └─ (병렬 처리)

08:20~08:30
  ├─ Fit & Priority Agent 시작 (점수 계산)
  │  └─ 적합도 & 우선순위 산출
  │  └─ 공고당 ~3초
  │
  └─ (병렬 처리)

08:30+
  ├─ Notion Dashboard Agent (카드 생성)
  │  └─ 추천 공고 → Notion 카드로 생성
  │  └─ Status 1분 주기 모니터링 시작
  │
  └─ (지속)

08:30~18:00
  ├─ 사용자가 Notion에서 Accept/Hold/Reject 선택
  │  │
  │  └─ Accept 감지 시:
  │     ├─ accept-state-sync (상태 동기화)
  │     ├─ calendar-freebusy-check (충돌 검사)
  │     ├─ calendar-event-create (일정 생성)
  │     └─ Notion Status = "Scheduled" 업데이트

18:00~23:59
  └─ 나머지는 자동 처리 (1분 주기 모니터링만 진행)
```

---

## 🔄 주요 데이터 흐름

```
Step 1: 프로필 (수동)
  user_profile_*.json
         ↓
Step 2: 수집 (08:00)
  daily_collection_*.json
         ↓
Step 3: 파싱 (자동)
  parsed_opportunity_*.json
         ↓
Step 4: 추천 (자동)
  recommended_opportunity_*.json
         ↓
Step 5: Notion (자동)
  Notion DB + notion_sync_log_*.json
         ↓
Step 6: Accept 감지 (모니터링)
  accept-state-sync 트리거
         ↓
Step 7: Calendar (Accept만)
  calendar_event_created_*.json
         ↓
Step 8: 보고 (08:00)
  kakao_brief_*.md + kakao_send_log_*.json
```

---

## 🚨 에러 시나리오별 처리

| 시나리오 | 처리 방식 | 결과 |
|--------|---------|------|
| 사이트 접근 실패 | 다른 사이트 계속 처리 | source_watchlist 업데이트, failure_reason 기록 |
| HTML 파싱 실패 | OCR 단계로 진행 | 최대한 정보 추출 (confidence 낮음) |
| 3단계 모두 실패 | 수동 검토 큐 | parse_failed 상태로 저장, 사용자 알림 |
| 필드 충돌 | 자동 확정 금지 | conflict = true, needs_review 표시 |
| 정보 불명확 | "확인 필요" 표시 | eligibility_status = "조건 확인 필요" |
| Notion API 오류 | 3회 재시도 | 실패 로그 기록, 다음 사이클 재시도 |
| Calendar 충돌 | 자동 반영 보류 | conflict_status = "conflict", 사용자 알림 |
| 마감일 불명확 | 일정 생성 보류 | calendar_status = "needs_review" |
| Kakao API 실패 | 메시지 파일로 저장 | MVP 모드: 파일 저장만 진행 |

---

## 📊 성능 기준값

```
수집:     10개 공고 = ~5-10분
파싱:     10개 공고 = ~3-5분 (병렬 처리 시)
추천:     10개 공고 = ~30초
Notion:   카드당 ~1초
Calendar: 공고당 ~5초 (5개 이벤트)
보고:     메시지 생성 ~2초

총 일일 처리 시간: 08:00~08:35 (35분 내)
```

---

## 🔑 주요 체크포인트

### 1️⃣ 프로필 설정 시
- [ ] user_id 생성됨 (timestamp 기반)
- [ ] 모든 필드 정규화됨 (학년, 지역, 시간대)
- [ ] 관심 분야 키워드 확장됨

### 2️⃣ 수집 완료 시
- [ ] new_urls 배열이 empty가 아님
- [ ] source_watchlist 업데이트됨
- [ ] 각 사이트별 parse_status 기록됨

### 3️⃣ 파싱 완료 시
- [ ] 3가지 방법 모두 시도됨 (html, ocr, vision)
- [ ] 각 필드에 confidence 있음 (0-100)
- [ ] 충돌 감지 시 conflict = true, needs_review 표시됨

### 4️⃣ 추천 완료 시
- [ ] fit_score (0-100) 계산됨
- [ ] fit_breakdown 배열에 항목별 점수 있음
- [ ] priority (긴급/중요/참고) 분류됨
- [ ] recommendation_reason 배열 채워짐

### 5️⃣ Notion 동기화 시
- [ ] 카드가 Notion에 생성됨
- [ ] 포스터 이미지 URL 저장됨
- [ ] Status = "New" 또는 "Recommended"
- [ ] Timely ID 연동 완료

### 6️⃣ Accept 후
- [ ] Notion Status = "Accept" 감지됨
- [ ] accept-state-sync 실행됨
- [ ] Calendar 충돌 검사 진행됨
- [ ] 충돌 없으면 이벤트 생성

### 7️⃣ Calendar 반영 후
- [ ] 마감일 이벤트 생성됨
- [ ] 행사일 이벤트 생성됨
- [ ] 준비 일정 5개 생성됨 (D-5~D-1)
- [ ] Notion Status = "Scheduled" 변경됨

### 8️⃣ 일일 보고 시
- [ ] kakao_brief.md 파일 생성됨
- [ ] 긴급 마감 섹션 포함됨
- [ ] 신규 추천 TOP 3-5 포함됨
- [ ] Notion 링크 포함됨

---

## ⚙️ 환경 설정 필요 항목

### 필수 (MVP)
- [ ] User 프로필 데이터 위치: `./data/profiles/`
- [ ] 수집 데이터 위치: `./data/collections/`
- [ ] 파싱 결과 위치: `./data/parsed/`
- [ ] 추천 결과 위치: `./data/recommended/`
- [ ] 로그 위치: `./data/logs/`
- [ ] 보고 파일 위치: `./data/kakao/`

### API 토큰 (나중에 추가)
- [ ] Notion Integration Token
- [ ] Google Calendar API 토큰
- [ ] Kakao 채널 API 키 (향후)
- [ ] Vision API 키 (Google Cloud 또는 Claude API)

### 스케줄
- [ ] Scheduler 설정: 08:00 (Asia/Seoul)
- [ ] Notion 모니터링: 1분 주기
- [ ] 재시도 정책: max 3회

---

## 📝 로깅 정책

모든 Agent가 다음을 기록:
- timestamp (ISO 8601)
- operation (create, update, error)
- status (success, failed, retry)
- error_message (if any)

로그 경로: `./data/logs/`
로그 파일명: `{agent_name}_log_{date}.json`

---

## 🎓 실습 체크리스트 (처음 실행 시)

Day 1:
- [ ] Profile Agent 실행 → user_profile 생성 확인
- [ ] Source Collector Agent 수동 실행 → daily_collection 생성 확인

Day 2:
- [ ] Multi-pass Parser → 샘플 3개 공고 파싱 확인
- [ ] Fit & Priority Agent → recommended.json 적합도 점수 확인

Day 3:
- [ ] Notion Dashboard Agent → Notion에 카드 3개 생성 확인
- [ ] 수동으로 1개 카드 Status = "Accept" 변경

Day 4:
- [ ] Calendar Scheduler → Google Calendar에 일정 생성 확인
- [ ] Kakao Report Agent → 메시지 파일 생성 확인

전체:
- [ ] 일일 자동화 08:00 트리거 테스트
- [ ] Accept → Calendar 연쇄 트리거 테스트
- [ ] 에러 처리 & 로깅 확인

---

## 🔗 관련 문서

- `WORKFLOW_ARCHITECTURE.md` — 상세 아키텍처 (흐름도, 상태머신, 의존성)
- `AGENT_SKILL_MAPPING.md` — 각 Agent의 Skills 호출 순서 & 입출력
- `./.claude/agents/*.md` — 각 Agent 역할 정의
- `./.claude/runners/*/main.py` — 로컬 MVP 실행 진입점
- `./.claude/skills/*/spec.md` — 각 Skill 상세 스펙

