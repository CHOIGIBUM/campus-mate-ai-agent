# spec.md — interest-keyword-expand Skill

## 목표
사용자 프로필의 관심 분야(예: "의료AI", "데이터 분석")를 확장하여 공고 검색 시 사용할 키워드 집합을 생성한다.

## 맥락
**대상:** 사용자 프로필의 interests.fields  
**사용 목적:** 공고 파싱 결과와 비교할 때 더 많은 관련 공고를 매칭하기 위해 키워드 확장

## 범위

**포함:**
- 기본 키워드 입력 (사용자 입력)
- 유사/상위 키워드 추가 (예: "의료AI" → "헬스케어", "병원", "진료", "의료 빅데이터")
- 영문 키워드 추가 (예: "의료AI" → "medical AI", "healthcare AI", "biomedical")
- 관련 직무 추가 (예: "데이터 분석" → "데이터 엔지니어", "BI", "데이터 과학")
- 최대 50개 키워드 까지 확장

**제외:**
- 메인 프로필 수정
- 공고 매칭 자체

## 입력 예시

```json
{
  "user_id": "user_20260702_001",
  "base_fields": ["의료AI", "데이터 분석", "AI Agent"]
}
```

## 출력 예시

```json
{
  "user_id": "user_20260702_001",
  "expanded_keywords": {
    "의료AI": [
      "의료AI", "헬스케어", "의료 기술", "바이오", "병원", "진료",
      "medical AI", "healthcare", "biomedical", "health tech"
    ],
    "데이터 분석": [
      "데이터 분석", "빅데이터", "데이터 엔지니어", "BI", "분석",
      "data analysis", "data science", "business intelligence"
    ],
    "AI Agent": [
      "AI Agent", "자동화", "LLM", "챗봇", "자율 시스템",
      "agent", "automation", "agentic"
    ]
  },
  "all_keywords_flattened": [
    "의료AI", "헬스케어", "의료 기술", "바이오", ...
  ]
}
```

## 성공 기준

- [ ] 각 기본 키워드당 최소 5개 이상 확장 키워드 생성
- [ ] 한글과 영문 키워드 모두 포함
- [ ] 관련 분야 유사어 포함
- [ ] 중복 제거 (소문자/대문자 통일)
