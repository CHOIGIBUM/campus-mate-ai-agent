---
name: deadline-priority-rank
description: >-
  마감까지 남은 일수와 적합도를 함께 고려해 긴급/중요/참고를 결정하고 날짜가 없거나 지난 공고를 안전하게 처리한다.
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

# Deadline Priority Rank

## Inputs

- fit score
- deadline
- current KST date or injected test date

## Rules

- urgent: near deadline with sufficiently strong fit
- important: high fit or direct interest match
- reference: relevant but lower urgency or incomplete timing
- missing deadline: never fabricate; mark timing uncertainty
- past deadline: do not present as actionable recommendation

Implementation: `src/campus_mate/services/recommendation.py`.
