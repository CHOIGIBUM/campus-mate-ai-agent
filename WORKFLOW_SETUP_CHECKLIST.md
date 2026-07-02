# Campus Career AI - 워크플로우 설정 완료 체크리스트

## ✅ 정의/설정 완료 항목

### 📋 설계 문서
- [x] WORKFLOW_ARCHITECTURE.md - 전체 플로우, 다이어그램, 상태머신, 의존성
- [x] AGENT_SKILL_MAPPING.md - 7개 Agent × 14개 워크플로우 Skill의 상세 매핑
- [x] WORKFLOW_QUICK_REFERENCE.md - 빠른 참조 가이드
- [x] CAMPUS_CAREER_AI_PROJECT_SUMMARY.md - 프로젝트 개요 (2주차 작성)

### 🤖 7개 Agents (각 `.claude/agents/*.md`)
- [x] profile-agent (프로필 관리)
- [x] source-collector-agent (공고 수집)
- [x] multipass-parser-agent (3단계 파싱)
- [x] fit-priority-agent (개인화 추천)
- [x] notion-dashboard-agent (Notion 현황판)
- [x] calendar-scheduler-agent (Google Calendar)
- [x] kakao-report-agent (일일 보고, Cron: 08:00)

### 🛠️ 15개 Campus Career Skills (오케스트레이터 1개 + 14개 워크플로우 Skill)

**데이터 수집 & 파싱 (7개)**
- [x] profile-build
- [x] interest-keyword-expand
- [x] source-watchlist-crawl
- [x] html-opportunity-parse
- [x] rendered-page-ocr
- [x] poster-vision-extract
- [x] schema-merge-and-validate

**개인화 추천 (2개)**
- [x] fit-score-rank
- [x] deadline-priority-rank

**외부 연동 (5개)**
- [x] notion-dashboard-sync
- [x] calendar-freebusy-check
- [x] calendar-event-create
- [x] kakao-brief-generate
- [x] accept-state-sync

---

## 🎯 워크플로우 핵심 설정

### 트리거 정의
```
✓ Schedule (매일 08:00 Asia/Seoul)
  ├─ Source Collector Agent
  └─ Kakao Report Agent

✓ Auto-trigger (데이터 처리 완료)
  ├─ Multi-pass Parser (URL 수집 후)
  ├─ Fit & Priority (파싱 완료 후)
  ├─ Notion Dashboard (추천 완료 후)
  └─ Calendar Scheduler (Accept 신호 감지)

✓ Monitoring (1분 주기)
  └─ Notion Dashboard (Status 변경 감지)
```

### 데이터 저장소
```
✓ ./data/profiles/          → user_profile_*.json
✓ ./data/collections/       → daily_collection_*.json
✓ ./data/parsed/            → parsed_opportunity_*.json
✓ ./data/recommended/       → recommended_opportunity_*.json
✓ ./data/logs/              → notion_sync_log_*.json
✓ ./data/calendar/          → calendar_event_created_*.json
✓ ./data/kakao/             → kakao_brief_*.md + kakao_send_log_*.json
```

### 상태 관리
```
✓ Notion Status 상태 전이
  New → Recommended → [Accept|Hold|Reject]
         ↓            ↓
       Conflict     Scheduled

✓ 내부 workflow 상태
  - pending_calendar_creation
  - calendar_created
  - conflict_detected
  - user_review_needed
```

### 에러 처리
```
✓ 사이트 접근 실패    → source_watchlist 기록, 다른 사이트 계속
✓ 파싱 실패          → OCR/Vision으로 자동 폴백
✓ 정보 충돌          → conflict = true, needs_review 표시
✓ 불명확 정보        → "확인 필요" 표시, 임의 생성 금지
✓ API 오류           → 최대 3회 재시도, 실패 로그 기록
✓ Calendar 충돌      → conflict_status 표시, 자동 반영 보류
```

---

## 🚀 다음 단계별 구현 일정

### Phase 1: MVP 기본 기능 (1주)
```
[ ] Profile Agent 구현
    └─ profile-build Skill
    └─ user_profile.json 생성 확인

[ ] Source Collector Agent 구현
    └─ source-watchlist-crawl Skill
    └─ 샘플 3개 사이트에서 URL 수집 테스트

[ ] Multi-pass Parser Agent 구현
    └─ html-opportunity-parse Skill
    └─ 샘플 5개 공고 파싱 테스트 (HTML만)
```

### Phase 2: 점수 & 추천 (1주)
```
[ ] Fit & Priority Agent 구현
    └─ fit-score-rank Skill
    └─ deadline-priority-rank Skill
    └─ 적합도 점수 계산 테스트

[ ] Notion Dashboard Agent 구현 (기본)
    └─ notion-dashboard-sync Skill
    └─ Notion 테스트 계정에서 카드 생성 테스트
```

### Phase 3: 자동화 & 일정 (1주)
```
[ ] Calendar Scheduler Agent 구현
    └─ calendar-freebusy-check Skill
    └─ calendar-event-create Skill
    └─ Google Calendar 테스트 계정에서 일정 생성 테스트

[ ] Accept 신호 감지 및 연쇄 처리 테스트
    └─ Notion Status "Accept" 변경
    └─ Calendar에 자동 일정 생성 확인
```

### Phase 4: 자동화 & 보고 (1주)
```
[ ] Scheduler 설정 (08:00)
    └─ cron job 또는 Task Scheduler 등록

[ ] Kakao Report Agent 구현
    └─ kakao-brief-generate Skill
    └─ 메시지 파일 생성 테스트 (실제 API 발송은 추후)

[ ] 전체 통합 테스트
    └─ 08:00 자동 트리거 테스트
    └─ 데이터 흐름 전체 검증
```

---

## 📊 구현 우선순위

### 높음 (필수)
1. profile-build - 모든 추천의 기초
2. source-watchlist-crawl - 데이터 입력원
3. fit-score-rank - 추천의 핵심
4. notion-dashboard-sync - 사용자 인터페이스
5. accept-state-sync - 자동화 트리거

### 중간 (권장)
6. html-opportunity-parse - 3단계 파싱 중 가장 안정적
7. calendar-freebusy-check - 충돌 감지
8. calendar-event-create - Calendar 반영
9. deadline-priority-rank - 우선순위 분류

### 낮음 (향후)
10. rendered-page-ocr - OCR 처리 (복잡도 높음)
11. poster-vision-extract - Vision API 호출 (비용)
12. kakao-brief-generate - 메시지 생성 (MVP는 템플릿으로 가능)
13. interest-keyword-expand - 키워드 확장 (사전 필요)

---

## 🧪 테스트 시나리오

### 시나리오 1: 전체 자동화 흐름 (수동 트리거)
```
1. Profile Agent 실행
   → user_profile_test_001.json 생성 확인

2. Source Collector Agent 실행 (3개 사이트)
   → daily_collection_test.json 생성 확인
   → new_urls 배열 10-20개 기대

3. Multi-pass Parser Agent 실행 (5개 URL)
   → parsed_opportunity_*.json 5개 생성 확인
   → 각 파일에 fit_breakdown 없음 (Fit Agent 전에)

4. Fit & Priority Agent 실행 (5개 공고)
   → recommended_opportunity_*.json 5개 생성 확인
   → fit_score 88, priority "긴급" 등 확인

5. Notion Dashboard Agent 실행
   → Notion 테스트 DB에 카드 5개 생성 확인
   → 각 카드에 fit_score, 우선순위 표시 확인

결과: 총 처리 시간 < 5분 (병렬 처리 전제)
```

### 시나리오 2: Accept → Calendar 자동화
```
1. 위의 시나리오 1 완료

2. Notion에서 1개 카드 Status = "Accept" 변경

3. Notion Dashboard Agent 모니터링 대기 (1분 주기)
   → Status 변경 감지

4. accept-state-sync 실행
   → workflow_status = "pending_calendar_creation"

5. Calendar Scheduler Agent 실행
   → calendar-freebusy-check 완료
   → 충돌 없음 확인
   → calendar-event-create 5개 이벤트 생성

6. Google Calendar 확인
   → 마감일, 행사일, 준비 일정 (D-5~D-1) 5개 확인

7. Notion 카드 Status = "Scheduled" 변경 확인

결과: Accept → Calendar 반영 < 2분
```

### 시나리오 3: 일일 보고 (08:00 Cron)
```
1. 08:00에 자동 트리거

2. Source Collector Agent
   → daily_collection_{date}.json

3. Kakao Report Agent
   → 어제 데이터 기반 보고 생성
   → kakao_brief_{date}.md 파일 생성
   → 긴급 마감, 신규 추천 TOP 3, 충돌, 확인 필요 포함

4. 메시지 파일 내용 검증
   → 400-800자 범위
   → 마크다운 형식
   → Notion 링크 포함

결과: 메시지 생성 < 5초
```

---

## ✋ 주의사항

### 구현 중 지켜야 할 원칙
1. **임의 생성 금지**
   - 원문에 없는 정보는 절대 추가하지 않기
   - 불명확하면 "확인 필요"로 표시

2. **근거 기록**
   - 모든 추출 정보에 source_method, evidence, confidence 포함
   - 로그는 항상 기록 (에러도, 성공도)

3. **중복 방지**
   - 같은 공고를 두 번 처리하지 않기
   - opportunity_id로 비교

4. **충돌 감지**
   - 다른 방식에서 다른 값 → conflict = true
   - 자동 확정하지 않고 needs_review 표시

5. **성능 기준**
   - 공고당 파싱 < 20초 (3단계)
   - 공고당 추천 < 3초
   - Notion 카드당 < 1초
   - 전체 08:00~08:35 (35분 내 완료)

---

## 📞 연락처 & 문의

구현 중 의문점:
- Agent 간 데이터 형식 → `AGENT_SKILL_MAPPING.md` 의 입출력 예시 참고
- Skill 상세 정의 → `./.claude/skills/*/spec.md` 참고
- 상태 전이 규칙 → `WORKFLOW_ARCHITECTURE.md`의 상태머신 참고
- 에러 처리 → `WORKFLOW_QUICK_REFERENCE.md`의 에러 시나리오 참고

---

## 🎉 완성 기준

MVP 완성으로 인정하는 조건:
- [ ] 7개 Agent 모두 구현
- [ ] 모든 Skills 구현 (최소한 기본 기능)
- [ ] Profile → Notion까지 자동화 완료
- [ ] Accept → Calendar까지 자동화 완료
- [ ] 08:00 Cron 트리거 작동
- [ ] 에러 처리 & 로깅 완료
- [ ] 샘플 데이터로 E2E 테스트 성공

---

## 📚 문서 네비게이션

```
┌─ WORKFLOW_SETUP_CHECKLIST.md (이 파일)
│  └─ 설정 완료 체크리스트, 구현 일정, 테스트 시나리오
│
├─ WORKFLOW_ARCHITECTURE.md
│  └─ 상세 아키텍처, 플로우 다이어그램, 상태머신, 의존성
│
├─ AGENT_SKILL_MAPPING.md
│  └─ 7개 Agent × 14개 워크플로우 Skill의 상세 매핑
│  └─ 각 Skill의 입출력 JSON 형식
│
├─ WORKFLOW_QUICK_REFERENCE.md
│  └─ 빠른 참조, 에러 시나리오, 성능 기준값
│
├─ CAMPUS_CAREER_AI_PROJECT_SUMMARY.md
│  └─ 프로젝트 개요 (완성: 2주차)
│
└─ ./.claude/
   ├─ agents/
   │  └─ [7개 Agent].md
   ├─ runners/
   │  └─ [7개 Agent runner]/main.py
   └─ skills/
      └─ [오케스트레이터 1개 + 14개 워크플로우 Skill]/SKILL.md + spec.md
```

