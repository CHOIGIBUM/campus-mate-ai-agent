# spec.md — deadline-priority-rank Skill

## 목표
적합도 점수와 마감일 정보를 기반으로 우선순위(긴급/중요/참고)를 결정한다.

## 맥락
**대상:** fit_score, deadline, 기준일(오늘)  
**사용 목적:** Fit & Priority Agent에서 호출하여 우선순위 분류

## 범위

**포함:**
- 긴급: D-7 이내 AND fit_score ≥75점
- 중요: fit_score ≥70점 OR 관심 분야 직접 관련
- 참고: 나머지
- D-day 계산

**제외:**
- 점수 계산 (fit-score-rank가 담당)

## 입력 예시

```json
{
  "fit_score": 88,
  "submission_deadline": "2026-07-07T23:59:00+09:00",
  "today": "2026-07-02"
}
```

## 출력 예시

```json
{
  "priority": "긴급",
  "d_day": 5,
  "priority_reason": "D-5이며 D-7 이내 AND fit_score >= 75"
}
```

## 성공 기준

- [ ] 긴급/중요/참고가 정확히 분류된다
- [ ] D-day가 정확히 계산된다
