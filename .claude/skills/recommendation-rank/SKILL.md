---
name: recommendation-rank
description: >-
  검증된 사용자 프로필과 구조화 공고를 비교해 제한적 키워드 확장, 0–100 적합도 breakdown, 긴급/중요/참고 우선순위와 근거 문장을 계산한다. 점수는 설명 가능한 정렬 휴리스틱이며 합격 가능성으로 표현하지 않는다.
user-invocable: false
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - Edit
---

# Recommendation Rank

Read [scoring-rubric.md](references/scoring-rubric.md) before changing score weights.

## Inputs

- validated `UserProfile`
- structured `Opportunity`
- current `Asia/Seoul` date or an injected test date

## Step 1 — Conservative search terms

Use the user's major, interests, activity types, career goal, and explicit keywords.

- preserve original terms
- split common separators
- remove duplicates
- add only nearby aliases with clear meaning
- do not infer sensitive traits or broad interests
- cap expansion to avoid semantic drift

Atomic command:

```bash
campus-mate-skill interest-keyword-expand --profile <profile.json>
```

## Step 2 — Fit score

Compare the profile against title, summary, eligibility, submission, benefits, organization, and opportunity type.

Requirements:

- score range: 0–100
- category breakdown must sum to the score
- reasons must cite observed profile and notice attributes
- parse confidence remains separate
- unknown eligibility is not treated as eligible
- score is not a probability of winning or acceptance

Atomic command:

```bash
campus-mate-skill fit-score-rank \
  --profile <profile.json> \
  --opportunity <opportunity.json>
```

## Step 3 — Deadline priority

Assign `긴급`, `중요`, or `참고` using fit and days until deadline.

- near deadline + sufficiently strong fit may be `긴급`
- strong direct match may be `중요`
- relevant but lower urgency or incomplete timing may be `참고`
- never fabricate a missing deadline
- a past deadline is not actionable

Atomic command:

```bash
campus-mate-skill deadline-priority-rank \
  --profile <profile.json> \
  --opportunity <opportunity.json>
```

## Output contract

```json
{
  "score": 86,
  "priority": "중요",
  "reasons": ["관심 분야 AI와 직접 일치", "대학생 참가 가능"],
  "breakdown": {"major": 20, "interest": 35, "career": 15, "eligibility": 10, "timing": 6},
  "days_until_deadline": 18
}
```

## Quality gates

- breakdown sum equals score
- reasons are grounded
- score and parse confidence are not conflated
- `NeedsReview` may be ranked but cannot be automatically scheduled
- production date is not hard-coded

## Implementation

- `src/campus_mate/services/keywords.py`
- `src/campus_mate/services/recommendation.py`
- `tests/test_recommendation.py`
