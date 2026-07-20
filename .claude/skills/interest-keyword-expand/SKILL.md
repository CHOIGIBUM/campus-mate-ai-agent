---
name: interest-keyword-expand
description: >-
  사용자 전공·관심·희망 직무 키워드를 제한적으로 확장하여 공고 텍스트 매칭에 사용한다. 과도한 동의어 확장으로 무관한 점수를 만들지 않는다.
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

# Interest Keyword Expand

## Input

Major, interests, career goal, user keywords.

## Rules

- split compound expressions and common separators
- add only domain-near aliases with clear meaning
- preserve original terms
- cap expansion to avoid broad semantic drift
- do not add demographic or sensitive inferences

## Output

Deduplicated search term list used by recommendation scoring.

Implementation begins with `UserProfile.search_terms`; additional expansion must remain transparent and tested.
