---
name: recommendation-rank
description: >-
  검증된 사용자 프로필과 구조화 공고를 비교해 제한적 키워드 확장, 0–100 적합도 세부 점수, 긴급·중요·참고 우선순위와 근거 문장을 계산한다. 점수는 설명 가능한 정렬 기준이며 합격 가능성으로 표현하지 않는다.
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

점수 가중치를 변경하기 전에 [점수 기준표](references/scoring-rubric.md)를 읽습니다.

## 입력

- 검증된 `UserProfile`
- 구조화된 `Opportunity`
- 현재 `Asia/Seoul` 날짜 또는 테스트에서 주입한 날짜

## 1단계 — 보수적인 검색어 생성

사용자의 전공, 관심 분야, 활동 유형, 희망 직무, 직접 입력한 키워드를 사용합니다.

- 원래 표현을 유지합니다.
- 일반적인 구분자를 기준으로 나눕니다.
- 중복을 제거합니다.
- 의미가 명확히 가까운 별칭만 추가합니다.
- 민감한 특성이나 지나치게 넓은 관심사를 추론하지 않습니다.
- 의미가 흐려지지 않도록 확장 수를 제한합니다.

검색어만 확인하는 명령:

```bash
campus-mate-skill interest-keyword-expand --profile <profile.json>
```

## 2단계 — 적합도 점수

프로필을 공고의 제목, 요약, 참가 자격, 제출물, 혜택, 주최기관, 공고 유형과 비교합니다.

필수 조건:

- 점수 범위: 0–100
- 항목별 세부 점수 합은 총점과 같아야 함
- 추천 이유는 확인된 프로필·공고 속성에 근거해야 함
- 파싱 신뢰도는 적합도 점수와 분리
- 참가 자격 미확인은 참가 가능으로 처리하지 않음
- 점수를 수상·선발 확률로 표현하지 않음

점수만 확인하는 명령:

```bash
campus-mate-skill fit-score-rank \
  --profile <profile.json> \
  --opportunity <opportunity.json>
```

## 3단계 — 마감 우선순위

적합도와 마감일까지 남은 기간을 함께 고려해 `긴급`, `중요`, `참고`를 지정합니다.

- 마감이 임박하고 적합도가 충분히 높으면 `긴급`이 될 수 있습니다.
- 직접적인 일치가 강하면 `중요`가 될 수 있습니다.
- 관련성은 있지만 급하지 않거나 일정 정보가 부족하면 `참고`로 둡니다.
- 누락된 마감일을 추측하지 않습니다.
- 이미 지난 마감일은 실행 가능한 추천으로 처리하지 않습니다.

우선순위만 확인하는 명령:

```bash
campus-mate-skill deadline-priority-rank \
  --profile <profile.json> \
  --opportunity <opportunity.json>
```

## 출력 계약

```json
{
  "score": 86,
  "priority": "중요",
  "reasons": ["관심 분야 AI와 직접 일치", "대학생 참가 가능"],
  "breakdown": {"major": 20, "interest": 35, "career": 15, "eligibility": 10, "timing": 6},
  "days_until_deadline": 18
}
```

## 품질 기준

- 세부 점수 합이 총점과 같음
- 추천 이유가 실제 정보에 근거함
- 적합도와 파싱 신뢰도를 혼동하지 않음
- `NeedsReview` 항목은 순위를 계산할 수 있지만 자동 일정화할 수 없음
- 운영 날짜를 코드에 고정하지 않음

## 구현

- `src/campus_mate/services/keywords.py`
- `src/campus_mate/services/recommendation.py`
- `tests/test_recommendation.py`
