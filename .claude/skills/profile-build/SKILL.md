---
name: profile-build
description: >-
  Campus Mate 사용자 온보딩과 프로필 수정을 수행한다. 기존 프로필을 읽고 필수 누락값만 질문한 뒤 UserProfile 계약으로 정규화·검증·저장하고 추천에 사용할 제한적 검색어를 생성한다.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - Edit
---

# Profile Build

## Inputs

Dialogue-derived values or a JSON object.

Required fields:

- `school`
- `grade`
- `major`
- `interests` with at least one value

Optional fields:

- activity types
- career goal
- explicit keywords
- preferred regions
- available times

## Interactive procedure

1. Read `data/user_profile.json` when it exists.
2. Summarize current values before asking questions.
3. Ask only for missing or intentionally changed fields.
4. Do not collect phone numbers, resident identifiers, or unrelated sensitive data.
5. Convert comma-separated values to arrays.
6. Trim whitespace and remove case-insensitive duplicates.
7. Preserve the user's wording; do not invent official department names.
8. Validate through `UserProfile`.
9. Save and show a concise confirmation summary.

## Commands

```bash
campus-mate profile init
campus-mate profile import --file <profile.json>
campus-mate profile show
```

## Search terms

Generate search terms from major, interests, career goal, and explicit keywords.

- preserve original terms
- split common separators
- add only clearly related aliases
- cap expansion to prevent semantic drift
- do not infer sensitive traits

Atomic inspection command:

```bash
campus-mate-skill interest-keyword-expand --profile <profile.json>
```

## Output

- `data/user_profile.json`
- profile summary
- search term list
- changed field list

On failure, identify the exact missing or invalid field. Never create a silent default profile.

## Implementation

- `src/campus_mate/services/onboarding.py`
- `src/campus_mate/services/keywords.py`
- `src/campus_mate/models.py::UserProfile`
- `tests/test_onboarding.py`
