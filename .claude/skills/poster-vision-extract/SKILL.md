---
name: poster-vision-extract
description: >-
  포스터 이미지에서 HTML/OCR 이후에도 누락된 공고 필드를 추출하고 vision evidence를 반환한다. Vision 결과만으로 모호한 핵심 필드를 확정하지 않는다.
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

# Poster Vision Extract

## Preconditions

- poster image URL/path exists
- `CAMPUS_MATE_VISION_API_KEY` and model configured
- missing fields justify the call, or `--all-passes` requested

## Requested fields

Only missing/high-value fields such as deadline, eligibility, benefits, event date, organization.

## Output constraints

- JSON-compatible values
- evidence excerpt/description
- confidence
- no chain-of-thought
- no inferred information not visible in the image

## Failure handling

Unavailable model, download failure, or invalid JSON → warning and continue with other passes.

## Implementation

`src/campus_mate/parsing/vision.py`
