# spec.md — profile-build Skill

## 목표
Profile Agent로부터 입력받은 사용자 정보를 검증하고, 표준 JSON 스키마로 정규화하여 파일로 저장한다.

---

## 맥락

**대상:** Profile Agent의 5단계 온보딩 완료 후 Step 5에서 호출

**사용 목적:** 구조화된 프로필 JSON을 생성하여 모든 개인화 추천, Calendar 역산, Notion/Kakao의 기초 제공

---

## 범위

**포함:**
- 입력 필드 검증 (형식, 길이, 범위 재확인)
- 데이터 정규화 (timezone 추가, 대소문자 통일 등)
- user_id 중복 검사 및 version 관리
- JSON 스키마 생성: basic_info, interests, career_goal, preferences, availability, metadata
- 파일 저장: `./data/profiles/user_profile_{user_id}.json`
- 기존 프로필 수정 시 version 증가 및 updated_at 갱신

**제외:**
- 검색 키워드 생성 (interest-keyword-expand Skill)
- 개인정보 암호화
- 선택지 검증 (Profile Agent에서 이미 완료)

---

## 제약

**입력 데이터 구조:**
```python
input_data = {
    # 필수
    "name": str,              # 1~50자
    "email": str,             # 이메일 형식
    "school": str,            # schools.json 또는 자유입력
    "major": str,             # majors.json 또는 자유입력
    "year": str,              # ["1학년", ..., "박사"]
    "report_time": str,       # "HH:MM" 형식
    
    # 권장 (최소 각 1개 이상)
    "interests": [str],       # 1~10개
    "positions": [str],       # 1~5개
    "activity_types": [str],  # 1~5개
    
    # 선택
    "regions": [str],         # 0~5개
    "available_hours_per_week": int | None
}
```

**timezone:** 항상 "Asia/Seoul"로 설정
**version:** 신규 프로필 = 1, 수정마다 +1

---

## 입력 예시

```python
input_data = {
    "name": "최기범",
    "school": "강원대학교",
    "major": "AI융합학과",
    "year": "2학년",
    "interests": ["의료AI", "데이터 분석", "AI Agent"],
    "positions": ["AI 개발자", "데이터 분석가"],
    "activity_types": ["해커톤", "공모전", "교육"],
    "regions": ["강원", "서울"],
    "available_hours_per_week": 5,
    "report_time": "08:00"
}
```

---

## 출력 예시

```json
{
  "user_id": "user_20260702_001",
  "basic_info": {
    "name": "최기범",
    "school": "강원대학교",
    "major": "AI융합학과",
    "year": "2학년"
  },
  "interests": {
    "fields": ["의료AI", "데이터 분석", "AI Agent"],
    "keywords_base": ["의료AI", "데이터 분석", "AI Agent"]
  },
  "career_goal": {
    "positions": ["AI 개발자", "데이터 분석가"],
    "skills": []
  },
  "preferences": {
    "activity_types": ["해커톤", "공모전", "교육"],
    "regions": ["강원", "서울"],
    "online_offline": "both",
    "available_hours_per_week": 5
  },
  "availability": {
    "report_time": "08:00",
    "timezone": "Asia/Seoul"
  },
  "metadata": {
    "created_at": "2026-07-02T20:00:00+09:00",
    "updated_at": "2026-07-02T20:00:00+09:00",
    "version": 1
  }
}
```

---

## 성공 기준

- [ ] 입력된 모든 필드가 정확히 JSON에 저장된다
- [ ] 학년, 지역, 시간 등이 표준화되어 저장된다
- [ ] 파일명에 user_id가 포함되고, 같은 사용자는 같은 user_id를 유지한다
- [ ] JSON이 올바른 형식이고 파싱 가능하다
