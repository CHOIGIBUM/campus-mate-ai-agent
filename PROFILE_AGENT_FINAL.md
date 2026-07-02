# Profile Agent - 최종 설계 완료 보고서

## ✅ 완성된 항목 (5가지)

### 1️⃣ Profile Agent spec.md 작성 ✓
- **위치:** `./.claude/skills/profile-build/spec.md`
- **내용:**
  - 5단계 온보딩 흐름 상세 정의
  - 필드별 검증 규칙 (필수/권장/선택)
  - user_id 생성 규칙: user_YYYYMMDD_### (timestamp 기반)
  - email로 기존 프로필 자동 검색
  - 에러 처리 정책
  - Update(수정) 프로세스
  - 성공 기준 8개

### 2️⃣ profile-build Skill spec.md 업데이트 ✓
- **위치:** `./.claude/skills/profile-build/spec.md`
- **변경사항:**
  - Profile Agent와의 연동 명확화
  - 입력 데이터 구조 정의
  - version 관리 규칙 추가
  - user_id 중복 검사 로직 정의

### 3️⃣ 선택지 데이터 JSON 파일 생성 ✓
- **위치:** `./data/choices/`
- **파일 목록:**
  ```
  ├─ schools.json (26개 대학교)
  ├─ interests.json (20개 관심 분야)
  ├─ positions.json (15개 희망 직무)
  ├─ activity_types.json (5개 활동 유형)
  └─ regions.json (17개 지역)
  ```
- **특징:** 자유입력 옵션 지원 ([기타] 선택시)

### 4️⃣ Profile Agent profile-agent.md ✓
- **위치:** `./.claude/agents/profile-agent.md`
- **상태:** 이미 작성됨 (5단계 흐름과 일치)

### 5️⃣ profile-build Skill SKILL.md (기존) ✓
- **위치:** `./.claude/skills/profile-build/SKILL.md`
- **상태:** 이미 작성됨

---

## 🎯 최종 설계 내용

### 온보딩 5단계 흐름

```
Step 1: 기본 정보 (필수)
  ├─ Q1. 이름 [텍스트]
  ├─ Q2. 이메일 [이메일] → 기존 프로필 검색
  ├─ Q3. 대학교 [선택/자유입력]
  ├─ Q4. 학과 [선택/자유입력]
  └─ Q5. 학년 [라디오]

Step 2: 관심 분야 & 직무 (권장, 최소 각 1개)
  ├─ Q6. 관심 분야 [체크박스, 최소 1개]
  └─ Q7. 희망 직무 [체크박스, 최소 1개]

Step 3: 활동 선호도 (권장, 최소 1개)
  ├─ Q8. 활동 유형 [체크박스, 최소 1개]
  └─ Q9. 활동 지역 [체크박스, 0~5개]

Step 4: 시간 & 알림 (시간은 선택, 알림은 필수)
  ├─ Q10. 주간 투자 시간 [숫자, 0~168, 선택]
  └─ Q11. 카카오 보고 시간 [시간선택, 필수]

Step 5: 확인 (필수)
  └─ 입력 정보 검토 → [확인] [수정]
```

### user_id 생성 규칙

```
형식: user_{YYYYMMDD}_{sequence}
예시:
  - user_20260702_001 (2026년 7월 2일 첫 번째)
  - user_20260702_002 (2026년 7월 2일 두 번째)

sequence는 당일 생성된 프로필 순번
날짜가 바뀌면 sequence 초기화
```

### 필드 분류

| 필드 | 분류 | 입력 방식 | 검증 |
|------|------|---------|------|
| name | 필수 | 텍스트 | 1~50자 |
| email | 필수 | 텍스트 | 이메일 형식, 기존 검색 |
| school | 필수 | 선택/자유 | schools.json 또는 자유입력 |
| major | 필수 | 선택/자유 | majors.json 또는 자유입력 |
| year | 필수 | 라디오 | ["1학년", ..., "박사"] |
| report_time | 필수 | 시간선택 | HH:MM 형식 |
| interests | 권장 | 체크박스 | 최소 1개, 최대 10개 |
| positions | 권장 | 체크박스 | 최소 1개, 최대 5개 |
| activity_types | 권장 | 체크박스 | 최소 1개, 최대 5개 |
| regions | 선택 | 체크박스 | 0~5개 |
| available_hours_per_week | 선택 | 숫자 | 0~168 |

### 출력 JSON 구조

```json
{
  "user_id": "user_20260702_001",
  "basic_info": {
    "name": "최기범",
    "email": "user@example.com",
    "school": "강원대학교",
    "major": "AI융합학과",
    "year": "2학년"
  },
  "interests": {
    "fields": ["의료AI", "데이터 분석"],
    "keywords_base": ["의료AI", "데이터 분석"]
  },
  "career_goal": {
    "positions": ["AI 개발자"],
    "skills": []
  },
  "preferences": {
    "activity_types": ["해커톤", "공모전"],
    "regions": ["온라인", "강원", "서울"],
    "available_hours_per_week": 5
  },
  "availability": {
    "report_time": "08:00",
    "timezone": "Asia/Seoul"
  },
  "metadata": {
    "created_at": "2026-07-02T20:00:00+09:00",
    "updated_at": "2026-07-02T20:00:00+09:00",
    "version": 1,
    "source": "profile_agent_onboarding"
  }
}
```

### 프로필 수정 프로세스

```
1. email 입력
2. ./data/profiles/ 검색
3. 기존 프로필 발견
   └─ "이전 프로필이 있네요. 수정하시겠어요?"
      ├─ [Yes] → Step 1~5 다시 진행
      │          version += 1, updated_at 갱신
      └─ [No] → email 중복 경고, 새 프로필로 진행
```

---

## 📂 파일 구조 확인

```
✓ ./.claude/runners/profile-agent/
  ├─ profile-agent.md
  └─ spec.md (✅ 새로 작성)

✓ ./.claude/skills/profile-build/
  ├─ SKILL.md (기존)
  └─ spec.md (✅ 업데이트됨)

✓ ./data/choices/ (✅ 새로 생성)
  ├─ schools.json (26개)
  ├─ interests.json (20개)
  ├─ positions.json (15개)
  ├─ activity_types.json (5개)
  └─ regions.json (17개)

✓ ./data/profiles/ (런타임에 생성)
  └─ user_profile_*.json
```

---

## 🎓 구현 준비 항목

### 필요한 코드 구현 (Python 또는 Node.js)

#### Profile Agent
```
1. 5단계 대화 UI 구현
   - Step별 질문 표시
   - 입력 필드 렌더링
   - 선택지 로드 (./data/choices/*.json)

2. 입력 검증 함수
   - name 검증 (1~50자)
   - email 검증 (형식)
   - year 검증 (리스트 확인)
   - time 검증 (HH:MM 형식)

3. 프로필 검색 함수
   - email로 ./data/profiles/ 검색
   - 기존 파일 발견 시 수정 흐름으로 분기

4. profile-build Skill 호출
   - 입력 데이터 패킹
   - Skill 실행
   - 결과 파일 저장 확인
```

#### profile-build Skill
```
1. 입력 데이터 재검증 (Profile Agent에서 온 데이터)

2. user_id 생성
   - 현재 날짜로 디렉토리 검색
   - 기존 파일 count + 1 = sequence

3. JSON 스키마 생성
   - 필드별 처리 (None, 빈 배열 처리)
   - timezone 추가
   - metadata 생성

4. 파일 저장
   - 기존 파일 있으면: version += 1
   - 새 파일이면: version = 1
   - ./data/profiles/ 저장

5. 에러 처리
   - user_id 생성 실패 → 재시도
   - 파일 저장 실패 → 에러 메시지
```

### 테스트 시나리오

#### 시나리오 1: 신규 프로필 생성
```
1. Profile Agent 실행
2. 5단계 모두 입력
3. 이메일 기존 파일 없음
4. user_profile_20260702_001.json 생성
5. JSON 검증 (모든 필드 확인)

기대 시간: ~2분
```

#### 시나리오 2: 기존 프로필 수정
```
1. Profile Agent 실행
2. 이메일 입력
3. user_profile_20260702_001.json 발견
4. "수정하시겠어요?" 선택
5. 관심 분야만 변경
6. version = 2, updated_at 갱신

기대 시간: ~2분
```

#### 시나리오 3: 에러 처리
```
1. email 형식 오류
   → "이메일 형식이 맞지 않습니다" 경고 + 재입력
   
2. 권장 필드 미입력
   → "최소 1개 이상 선택해주세요" 경고 + 계속/수정

3. 필수 필드 누락
   → 에러 + Step 반복

4. 파일 저장 실패
   → "저장 중 오류가 발생했습니다. 다시 시도해주세요"
```

---

## ✨ 주요 특징

| 특징 | 설명 |
|------|------|
| **5단계 흐름** | 사용자 이탈 방지, 단계별 피드백 |
| **email 기반 검색** | 기존 프로필 자동 감지, 수정 모드 전환 |
| **timestamp 기반 user_id** | 생성 날짜 추적 가능, 중복 불가 |
| **선택지 외부화** | JSON으로 관리, 유지보수 용이 |
| **자유입력 옵션** | 선택지 + [기타]로 확장성 제공 |
| **version 관리** | 프로필 수정 이력 추적 가능 |

---

## 📋 다음 단계 (구현)

### Phase 1: 기본 구현 (Day 1~2)
```
[ ] Profile Agent UI 구현 (5단계)
    ├─ Step별 질문 표시
    ├─ 선택지 로드 (JSON)
    └─ 입력 필드 렌더링

[ ] profile-build Skill 구현
    ├─ 입력 재검증
    ├─ user_id 생성
    └─ JSON 파일 저장
```

### Phase 2: 검증 & 테스트 (Day 3)
```
[ ] 신규 프로필 생성 테스트
[ ] 기존 프로필 수정 테스트
[ ] 에러 처리 테스트
[ ] JSON 파일 검증
```

### Phase 3: 통합 테스트 (Day 4)
```
[ ] 전체 5단계 흐름 테스트
[ ] 데이터 저장 확인
[ ] 다음 Agent(Source Collector) 입력 형식 검증
```

---

## 🎉 완성 기준

MVP 완성으로 인정하는 조건:
- [ ] 5단계 모두 구현되고 동작함
- [ ] 각 단계별 검증이 정상 작동함
- [ ] user_id가 user_YYYYMMDD_### 형식으로 생성됨
- [ ] email로 기존 프로필 검색 가능
- [ ] JSON 파일이 ./data/profiles/에 정상 저장됨
- [ ] 신규/수정 모두 테스트 성공
- [ ] 선택지 JSON이 정상 로드됨
- [ ] 에러 처리 모두 테스트 성공

---

## 📞 구현 중 참고

**입력 데이터 예시:**
```python
profile_input = {
    "name": "최기범",
    "email": "kichulme@example.com",
    "school": "강원대학교",
    "major": "AI융합학과",
    "year": "2학년",
    "interests": ["의료AI", "데이터 분석"],
    "positions": ["AI 개발자"],
    "activity_types": ["해커톤", "공모전"],
    "regions": ["온라인", "강원"],
    "available_hours_per_week": 5,
    "report_time": "08:00"
}
```

**user_id 예시:**
```
user_20260702_001  ← 2026년 7월 2일 첫 번째
user_20260702_002  ← 2026년 7월 2일 두 번째
user_20260703_001  ← 2026년 7월 3일 첫 번째
```

**선택지 로드:**
```python
import json

with open('./data/choices/schools.json') as f:
    schools = json.load(f)['schools']
    
# schools = ["강원대학교", "강원도립대학교", ..., "포항공과대학교"]
```

