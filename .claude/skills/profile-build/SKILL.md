---
name: profile-build
description: >-
  사용자 프로필 입력을 UserProfile 계약에 맞게 정규화·검증하고 저장한다. profile-manager가 사용하는 도메인 스킬이다.
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

# Profile Build Contract

## Input

JSON object or dialogue-derived values.

## Required

- school
- grade
- major
- interests (one or more)

## Normalization

- comma-separated strings → arrays
- trim whitespace
- case-insensitive duplicate removal
- keep user wording; do not hallucinate official department names

## Validation

Use `UserProfile` in `src/campus_mate/models.py` or:

```bash
campus-mate profile import --file <file>
```

## Output

Validated `data/user_profile.json` and summary. On failure, list the exact missing or invalid field.
