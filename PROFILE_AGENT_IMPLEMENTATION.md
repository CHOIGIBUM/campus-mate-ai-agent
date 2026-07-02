# Profile Agent - 실제 코드 구현 완료

## ✅ 완성된 파일 목록

### Core Implementation
```
./.claude/runners/profile-agent/
├── profile_agent.py        (11,772자) - Profile Agent 메인 로직 (5단계 온보딩)
├── utils.py                (8,892자)  - 유틸리티 함수 (검증, 파일 I/O, 선택지 로드)
├── main.py                 (725자)    - 메인 엔트리 포인트
└── test_profile_agent.py   (9,032자)  - 자동화된 테스트 (4가지 시나리오)

./.claude/skills/profile-build/
├── profile_build.py        (6,997자)  - Skill 구현 (JSON 생성 및 저장)
└── SKILL.md                          - Skill 문서

./data/choices/
├── schools.json            (26개 대학교)
├── majors.json             (40개 학과)
├── interests.json          (20개 관심 분야)
├── positions.json          (15개 희망 직무)
├── activity_types.json     (5개 활동 유형)
└── regions.json            (17개 활동 지역)
```

---

## 🎯 코드 구조 및 기능

### 1️⃣ utils.py - 유틸리티 함수 모음

**주요 함수:**
```python
load_choices()                 # 모든 선택지 JSON 로드
validate_name(name)            # 이름 검증 (1~50자)
validate_email(email)          # 이메일 검증
validate_year(year)            # 학년 검증
validate_time(time_str)        # 시간 형식 검증 (HH:MM)
validate_hours(hours_str)      # 주간 시간 검증 (0~168)
validate_selection()           # 선택지 배열 검증
find_existing_profile(email)   # email로 기존 프로필 검색
generate_user_id()             # user_id 자동 생성 (timestamp 기반)
show_choices()                 # 선택지 표시 및 선택 받기
print_profile_summary()        # 프로필 정보 요약 출력
```

### 2️⃣ profile_build.py - Skill 구현

**ProfileBuildSkill 클래스:**
```python
execute(input_data, user_id)   # 메인 실행 메서드
_validate_input()              # 입력 데이터 재검증
_find_existing_profile()       # email로 기존 파일 검색
_create_schema()               # 표준 JSON 스키마 생성
_save_profile()                # JSON 파일 저장 (신규/수정 모두 처리)
load_profile(user_id)          # 프로필 로드
```

**출력 JSON 구조:**
```json
{
  "user_id": "user_20260702_001",
  "basic_info": {
    "name", "email", "school", "major", "year"
  },
  "interests": {
    "fields", "keywords_base"
  },
  "career_goal": {
    "positions", "skills"
  },
  "preferences": {
    "activity_types", "regions", "available_hours_per_week"
  },
  "availability": {
    "report_time", "timezone"
  },
  "metadata": {
    "created_at", "updated_at", "version", "source"
  }
}
```

### 3️⃣ profile_agent.py - Profile Agent 메인 로직

**ProfileAgent 클래스:**
```python
run()                          # 전체 5단계 흐름 실행

step_1_basic_info()            # Step 1: 기본 정보 수집
                               # - 이름, 이메일, 학교, 학과, 학년
                               # - email로 기존 프로필 검색

step_2_interests_and_positions() # Step 2: 관심 분야 & 직무
                                 # - 관심 분야 (최소 1개, 최대 10개)
                                 # - 희망 직무 (최소 1개, 최대 5개)

step_3_activity_preferences()  # Step 3: 활동 선호도
                               # - 활동 유형 (최소 1개)
                               # - 활동 지역 (선택사항)

step_4_time_and_notification() # Step 4: 시간 & 알림
                               # - 주간 투자 시간 (선택사항)
                               # - 카카오 보고 시간 (필수)

step_5_confirmation()          # Step 5: 확인 및 저장
                               # - 프로필 요약 표시
                               # - Skill 호출하여 저장
```

---

## 🧪 테스트 결과

### 테스트 실행
```bash
python3 ./.claude/runners/profile-agent/test_profile_agent.py
```

### 테스트 케이스 (✅ 모두 통과)

```
✅ PASS | 신규 프로필 생성
  - user_id 자동 생성 확인
  - 필드 정확성 검증
  - JSON 구조 검증
  - 버전 1 확인

✅ PASS | 기존 프로필 수정
  - email로 기존 프로필 검색
  - version 자동 증가 (1→2)
  - updated_at 갱신
  - 수정 내용 저장 확인

✅ PASS | 검증 에러 처리
  - 이메일 형식 오류 감지
  - 필수 필드 누락 감지
  - 적절한 에러 메시지 반환

✅ PASS | 파일 저장 확인
  - 파일 생성 확인
  - JSON 파싱 가능성 검증
  - 저장된 내용 일치 확인
```

---

## 🚀 실행 방법

### 1️⃣ 대화형 온보딩 (사용자 입력)
```bash
python3 ./.claude/runners/profile-agent/main.py
```

**대화 흐름:**
```
Step 1: 기본 정보
  Q1. 이름을 입력하세요: 최기범
  Q2. 이메일 주소를 입력하세요: user@example.com
  Q3. 대학교를 선택하세요: 1 (강원대학교)
  Q4. 학과를 입력하세요: AI융합학과
  Q5. 학년을 선택하세요: 2 (2학년)

Step 2: 관심 분야 & 직무
  관심 분야 선택: 1, 2, 3 (의료AI, 데이터 분석, AI Agent)
  희망 직무 선택: 1, 4 (AI 개발자, ML Engineer)

Step 3: 활동 선호도
  활동 유형 선택: 1, 2 (해커톤, 공모전)
  활동 지역 선택: 1, 2, 3 (온라인, 강원, 서울)

Step 4: 시간 & 알림
  주간 투자 시간: 5
  카카오 보고 시간: 08:00

Step 5: 확인 및 저장
  입력 정보 요약 표시
  저장 확인: y
  → ✅ 프로필 저장 완료!
```

### 2️⃣ 프로그래매틱 실행 (Python 코드)
```python
from profile_agent import ProfileAgent

agent = ProfileAgent()
agent.run()
```

### 3️⃣ 자동화된 테스트
```bash
python3 ./.claude/runners/profile-agent/test_profile_agent.py
```

---

## 📊 생성된 프로필 파일

### 경로
```
./data/profiles/user_profile_user_20260702_001.json
./data/profiles/user_profile_user_20260702_002.json
...
```

### 샘플 파일 내용
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
    "fields": ["의료AI", "데이터 분석", "AI Agent"],
    "keywords_base": ["의료AI", "데이터 분석", "AI Agent"]
  },
  "career_goal": {
    "positions": ["AI 개발자", "ML Engineer"],
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
    "created_at": "2026-07-02T12:40:33",
    "updated_at": "2026-07-02T12:40:33",
    "version": 1,
    "source": "profile_agent_onboarding"
  }
}
```

---

## ✨ 주요 특징

### 입력 검증
- ✅ 이름: 1~50자, 한글/영문/숫자/기호
- ✅ 이메일: RFC 기준 형식 검증
- ✅ 학년: 정의된 목록에서만 선택
- ✅ 시간: HH:MM 형식 정확히 검증
- ✅ 배열: 최소/최대 개수 검증
- ✅ 선택지: 정의된 목록 또는 자유입력

### 사용자 경험
- 5단계로 단계별 진행 (이탈 방지)
- 각 단계별 확인 피드백
- 수정 단계 선택 가능
- 기존 프로필 자동 감지 (email 기반)
- 명확한 에러 메시지

### 데이터 관리
- user_id 자동 생성 (timestamp 기반)
- version 관리 (수정할 때마다 증가)
- created_at vs updated_at 구분
- 메타데이터 자동 기록
- JSON 형식으로 저장 (인간이 읽을 수 있는 형태)

---

## 🎓 구현 기술 스택

**언어:** Python 3.7+
**핵심 라이브러리:**
- `json` - JSON 직렬화/역직렬화
- `pathlib` - 파일 경로 관리
- `datetime` - 타임스탬프
- `re` - 정규식 검증

**의존성:** 표준 라이브러리만 사용 (외부 라이브러리 불필요)

---

## 🔧 다음 단계

### Phase 1: 통합 테스트 (완료)
- ✅ 신규 프로필 생성
- ✅ 기존 프로필 수정
- ✅ 검증 에러 처리
- ✅ 파일 저장 확인

### Phase 2: 실제 사용 (진행)
```bash
# 대화형 실행
python3 ./.claude/runners/profile-agent/main.py
```

### Phase 3: Source Collector 연동 (예정)
- `./data/profiles/user_profile_*.json` 로드
- user_id와 프로필 정보 전달

---

## 📝 에러 처리

모든 에러 케이스가 처리됩니다:

```python
# 이메일 형식 오류
❌ 올바른 이메일 형식이 아닙니다. (예: user@example.com)

# 필수 필드 누락
❌ 입력 검증 실패: 필수 필드 누락

# 선택지 최소 개수 미달
❌ 최소 1개 이상 선택해주세요.

# 파일 저장 실패
❌ 파일 저장 실패: [error_details]
```

---

## 🎉 완성 요약

✅ **Profile Agent 완전 구현**
- 5단계 온보딩 흐름
- 완벽한 입력 검증
- 자동 user_id 생성
- email 기반 프로필 검색
- 수정 모드 자동 감지
- 표준 JSON 스키마 생성
- 파일 저장/로드

✅ **자동화된 테스트**
- 신규 프로필 생성 테스트
- 기존 프로필 수정 테스트
- 검증 에러 처리 테스트
- 파일 저장 검증

✅ **선택지 데이터**
- 6개 JSON 파일 (학교, 학과, 관심분야, 직무, 활동유형, 지역)
- 총 103개 기본 선택지
- 자유입력 옵션 지원

---

## 📞 사용 예시

```bash
# 1. 대화형 온보딩
$ python3 ./.claude/runners/profile-agent/main.py

# 2. 테스트 실행
$ python3 ./.claude/runners/profile-agent/test_profile_agent.py

# 3. 생성된 프로필 확인
$ cat ./data/profiles/user_profile_user_20260702_001.json
```

모든 기능이 정상 작동하며, 다음 단계로 Source Collector Agent를 연동할 수 있습니다! 🚀
