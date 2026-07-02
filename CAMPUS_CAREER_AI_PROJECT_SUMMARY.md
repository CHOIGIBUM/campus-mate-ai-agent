# Campus Career AI - 프로젝트 완성 요약

## 📋 프로젝트 개요

**Campus Career AI**는 대학생을 위한 공모전·해커톤·대외활동 기회 자동 관리 시스템입니다.

- 매일 공고 사이트를 자동 수집
- 3단계 파싱으로 불완전한 정보 보완
- 사용자 프로필 기반 개인화 추천
- Notion 현황판에서 관리
- Google Calendar 자동 일정화
- Kakao 일일 보고

---

## 🤖 구성: 7개 Agents

### 1. **Profile Agent** (프로필 관리)
- 역할: 사용자 온보딩 정보 구조화
- 정의: `./.claude/agents/profile-agent.md`
- 실행: `./.claude/runners/profile-agent/`
- 담당 Task: 이름, 학과, 학년, 관심 분야, 희망 직무, 지역, 가능 시간 입력 및 JSON 저장
- 의존 Skill: `profile-build`

### 2. **Source Collector Agent** (공고 수집)
- 역할: 7개 사이트에서 신규 공고 URL 수집
- 정의: `./.claude/agents/source-collector-agent.md`
- 실행: `./.claude/runners/source-collector-agent/`
- 담당 Task: 매일 정해진 시간에 링커리어, 씽굿, 온오프믹스, 데이콘, 위비티, 대학교 공지, 공유대학 순회
- 의존 Skill: `source-watchlist-crawl`
- 스케줄: 사용자 프로필 지정 시간 (기본 08:00)

### 3. **Multi-pass Parser Agent** (3단계 파싱)
- 역할: HTML, OCR, Vision 3가지 방식으로 공고 정보 추출
- 정의: `./.claude/agents/multipass-parser-agent.md`
- 실행: `./.claude/runners/multipass-parser-agent/`
- 담당 Task: HTML 파싱 → 렌더링/OCR → 포스터 이미지 분석
- 의존 Skills: `html-opportunity-parse`, `rendered-page-ocr`, `poster-vision-extract`, `schema-merge-and-validate`
- 출력: 근거와 신뢰도를 포함한 JSON

### 4. **Fit & Priority Agent** (개인화 추천)
- 역할: 사용자 프로필과 공고 비교하여 적합도 점수 및 우선순위 계산
- 정의: `./.claude/agents/fit-priority-agent.md`
- 실행: `./.claude/runners/fit-priority-agent/`
- 담당 Task: 전공, 관심 분야, 희망 직무, 자격, 일정, 지역 기준 점수 계산
- 의존 Skills: `interest-keyword-expand`, `fit-score-rank`, `deadline-priority-rank`
- 출력: fit_score (0–100), priority (긴급/중요/참고), recommendation_reason

### 5. **Notion Dashboard Agent** (Notion 현황판)
- 역할: Notion 데이터베이스 관리 및 사용자 상태 변경 감지
- 정의: `./.claude/agents/notion-dashboard-agent.md`
- 실행: `./.claude/runners/notion-dashboard-agent/`
- 담당 Task: 공고 카드 생성/갱신, Accept 상태 감지 및 동기화
- 의존 Skill: `notion-dashboard-sync`, `accept-state-sync`
- 모니터링: 1분 주기로 Status 필드 변경 감지

### 6. **Calendar Scheduler Agent** (Google Calendar 일정화)
- 역할: Accept된 공고의 마감일, 행사일, 준비 일정 생성
- 정의: `./.claude/agents/calendar-scheduler-agent.md`
- 실행: `./.claude/runners/calendar-scheduler-agent/`
- 담당 Task: 일정 생성, 충돌 검사, 준비 일정 역산 (D-5~D-1)
- 의존 Skills: `calendar-freebusy-check`, `calendar-event-create`
- 충돌 감지 시 Kakao 보고 큐 추가

### 7. **Kakao Report Agent** (일일 보고)
- 역할: 신규 추천, 긴급 마감, 충돌, 확인 필요 항목을 메시지로 생성
- 정의: `./.claude/agents/kakao-report-agent.md`
- 실행: `./.claude/runners/kakao-report-agent/`
- 담당 Task: 매일 정해진 시간에 보고 메시지 생성 및 전송
- 의존 Skill: `kakao-brief-generate`
- 스케줄: 사용자 프로필 보고_시간 (기본 08:00)
- MVP: 메시지 파일 저장 또는 텍스트 미리보기 (실제 Kakao API 발송은 추후 연동)

---

## 🛠️ 구성: 15개 Campus Career Skills

`campus-career-orchestrator` 1개가 전체 실행 순서를 조율하고, 아래 14개 workflow Skill이 실제 작업 단위를 담당합니다.

### 데이터 수집 & 파싱

1. **profile-build** - 사용자 프로필 JSON 생성
2. **interest-keyword-expand** - 관심 분야 → 검색 키워드 확장
3. **source-watchlist-crawl** - 공고 사이트 순회 및 URL 수집
4. **html-opportunity-parse** - HTML 본문 파싱
5. **rendered-page-ocr** - 렌더링/PDF/OCR 파싱
6. **poster-vision-extract** - 포스터 이미지 Vision 분석
7. **schema-merge-and-validate** - 3단계 결과 병합 및 검증

### 개인화 추천

8. **fit-score-rank** - 적합도 점수 계산 (0–100)
9. **deadline-priority-rank** - 우선순위 분류 (긴급/중요/참고)

### 외부 연동

10. **notion-dashboard-sync** - Notion API 호출 (카드 생성/갱신)
11. **calendar-freebusy-check** - Google Calendar 충돌 검사
12. **calendar-event-create** - Google Calendar 일정 생성
13. **kakao-brief-generate** - Kakao 보고 메시지 생성
14. **accept-state-sync** - Notion Accept 감지 및 Timely 동기화

---

## 📂 파일 구조

```
./.claude/
├── agents/
│   ├── profile-agent.md
│   ├── source-collector-agent.md
│   ├── multipass-parser-agent.md
│   ├── fit-priority-agent.md
│   ├── notion-dashboard-agent.md
│   ├── calendar-scheduler-agent.md
│   └── kakao-report-agent.md
│
├── runners/
│   ├── profile-agent/
│   ├── source-collector-agent/
│   ├── multipass-parser-agent/
│   ├── fit-priority-agent/
│   ├── notion-dashboard-agent/
│   ├── calendar-scheduler-agent/
│   └── kakao-report-agent/
│
└── skills/
    ├── campus-career-orchestrator/
    ├── profile-build/
    │   ├── spec.md
    │   └── SKILL.md
    ├── interest-keyword-expand/
    │   ├── spec.md
    │   └── SKILL.md
    ├── source-watchlist-crawl/
    │   ├── spec.md
    │   └── SKILL.md
    ├── html-opportunity-parse/
    │   ├── spec.md
    │   └── SKILL.md
    ├── rendered-page-ocr/
    │   ├── spec.md
    │   └── SKILL.md
    ├── poster-vision-extract/
    │   ├── spec.md
    │   └── SKILL.md
    ├── schema-merge-and-validate/
    │   ├── spec.md
    │   └── SKILL.md
    ├── fit-score-rank/
    │   ├── spec.md
    │   └── SKILL.md
    ├── deadline-priority-rank/
    │   ├── spec.md
    │   └── SKILL.md
    ├── notion-dashboard-sync/
    │   ├── spec.md
    │   └── SKILL.md
    ├── calendar-freebusy-check/
    │   ├── spec.md
    │   └── SKILL.md
    ├── calendar-event-create/
    │   ├── spec.md
    │   └── SKILL.md
    ├── kakao-brief-generate/
    │   ├── spec.md
    │   └── SKILL.md
    └── accept-state-sync/
        ├── spec.md
        └── SKILL.md
```

---

## 🔄 전체 작동 흐름

```
[1] 사용자 프로필 입력
    ↓
[2] Profile Agent → profile-build Skill
    ↓ (매일 08:00 트리거)
[3] Source Collector Agent → source-watchlist-crawl Skill
    ↓ (신규 URL 수집)
[4] Multi-pass Parser Agent
    ├─ html-opportunity-parse
    ├─ rendered-page-ocr
    ├─ poster-vision-extract
    └─ schema-merge-and-validate
    ↓ (JSON 정규화)
[5] Fit & Priority Agent
    ├─ interest-keyword-expand
    ├─ fit-score-rank
    └─ deadline-priority-rank
    ↓ (적합도 & 우선순위)
[6] Notion Dashboard Agent → notion-dashboard-sync Skill
    ↓ (Notion에 카드 생성, 상태 감지)
[7] 사용자가 Notion에서 Accept 선택
    ↓
[8] accept-state-sync Skill (Accept 감지)
    ↓
[9] Calendar Scheduler Agent
    ├─ calendar-freebusy-check
    └─ calendar-event-create
    ↓ (일정 생성)
[10] Kakao Report Agent → kakao-brief-generate Skill
     ↓ (매일 보고 메시지)
[11] 사용자 알림 (메시지 파일 또는 Telegram/이메일)
```

---

## 📋 각 Spec의 주요 내용

### Agent 정의

각 Agent markdown에는:
- **목표**: 한 문장 정의
- **맥락**: 대상과 사용 목적
- **범위**: 포함/제외 사항
- **제약**: 반드시 지켜야 할 조건
- **출력 형식**: 파일명, 섹션 순서, 분량
- **성공 기준**: 체크리스트 형태의 검증 항목

### Skill Specs

각 Skill의 **spec.md**에는:
- **목표**: 명확한 작업 정의
- **맥락**: 사용 시기와 목적
- **범위**: 책임 범위
- **제약**: 입력 형식, 언어, 시간 제한
- **입출력 예시**: 실제 JSON 형식
- **성공 기준**: 체크리스트

---

## 🎯 설계 원칙

1. **설명 가능한 추천**: 점수와 이유를 함께 제시
2. **임의 생성 금지**: 불명확한 정보는 "확인 필요"로 표시
3. **근거 기록**: 모든 추출 정보에 source_method, evidence, confidence 포함
4. **충돌 감지**: 다른 방식에서 다른 값이 나오면 conflict 플래그
5. **중복 방지**: 같은 공고는 한 번만 처리
6. **사용자 우선**: Recommended 상태는 Calendar에 반영하지 않음, Accept만 반영

---

## 🚀 다음 단계

### MVP 구현 체크리스트

- [ ] Profile Agent 테스트 (프로필 JSON 생성)
- [ ] Source Collector Agent 테스트 (3–5개 사이트 수집)
- [ ] Multi-pass Parser 3단계 파싱 테스트 (샘플 5개 공고)
- [ ] Fit & Priority Agent 테스트 (점수 계산)
- [ ] Notion Dashboard Agent 테스트 (카드 생성 및 상태 동기화)
- [ ] Calendar Scheduler Agent 테스트 (충돌 검사 및 일정 생성)
- [ ] Kakao Report Agent 테스트 (메시지 파일 생성)

### 향후 확장

- 실제 Kakao 채널 API 연동
- 더 많은 공고 사이트 추가
- OCR 정확도 개선 (한글 특화)
- 사용자 피드백 기반 추천 모델 개선
- 자동 지원서 작성 (선택사항)
- 팀원 자동 매칭 (선택사항)

---

## 📝 문서 참고

- **기획서**: `Campus_Career_AI_기획_구체화안_동료공유용.docx`
- **양식 템플릿**: `spec_template.md`
- **이 요약**: `CAMPUS_CAREER_AI_PROJECT_SUMMARY.md`

각 Agent와 Skill의 상세 내용은 `./.claude/agents/*.md`, `./.claude/skills/*/spec.md`를 참고하세요.
