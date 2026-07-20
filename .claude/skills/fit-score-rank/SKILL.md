---
name: fit-score-rank
description: >-
  프로필과 공고를 비교해 0–100 적합도 breakdown과 grounded recommendation reasons를 계산한다. 상세 배점과 설명 규칙을 제공한다.
user-invocable: false
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - Edit
  - Agent
  - Skill
---

# Fit Score Rank

Read [scoring-rubric.md](references/scoring-rubric.md).

## Procedure

1. Build profile search terms.
2. Compare major/interests/career/activity/eligibility/region.
3. Calculate each category.
4. Clamp total to 0–100.
5. Generate 2–4 reasons using matched observed terms.
6. Keep uncertainty explicit.

## Invariants

- breakdown sum equals score
- score is not success probability
- parse confidence is separate
- unknown eligibility is not treated as eligible

## Verify

```bash
python -m pytest tests/test_recommendation.py -q
```
