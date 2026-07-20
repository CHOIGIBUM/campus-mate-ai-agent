---
name: recommendation-rank
description: >-
  검증된 프로필과 공고를 비교해 적합도 세부 점수, 총점, 마감 우선순위, 추천 이유를 생성한다.
user-invocable: false
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - Edit
---

# 추천 순위 계산

[점수 기준표](references/scoring-rubric.md)를 적용합니다.

## 입력

- `UserProfile`
- `Opportunity`
- KST 기준 날짜 또는 테스트 주입 날짜

## 절차

1. 전공, 관심 분야, 활동 유형, 희망 직무, 직접 입력 키워드로 검색어를 생성합니다.
2. 명확한 동의어만 제한적으로 추가합니다.
3. 전공·관심·직무·자격·마감·지역 항목별 점수를 계산합니다.
4. 세부 점수 합으로 총점을 계산합니다.
5. 적합도와 마감일까지의 기간으로 우선순위를 정합니다.
6. 확인된 속성으로 추천 이유를 생성합니다.

## 제약

- 점수 범위는 0–100입니다.
- 세부 점수 합은 총점과 같아야 합니다.
- 누락된 자격·마감일을 추정하지 않습니다.
- 적합도와 파싱 신뢰도를 분리합니다.
- 점수를 수상·선발 확률로 표현하지 않습니다.

## 출력

```json
{
  "score": 86,
  "priority": "중요",
  "reasons": ["관심 분야 AI와 직접 일치", "대학생 참가 가능"],
  "breakdown": {
    "major": 20,
    "interest": 35,
    "career": 15,
    "eligibility": 10,
    "timing": 6
  },
  "days_until_deadline": 18
}
```

## 구현·검증

- `src/campus_mate/services/keywords.py`
- `src/campus_mate/services/recommendation.py`
- `python -m pytest tests/test_recommendation.py -q`
