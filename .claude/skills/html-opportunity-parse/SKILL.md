---
name: html-opportunity-parse
description: >-
  공고 상세 페이지의 JSON-LD, Next.js state, visible HTML에서 제목·기관·날짜·자격·제출물·혜택·포스터를 추출하고 field evidence를 생성한다.
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

# HTML Opportunity Parse

## Evidence order

1. JSON-LD
2. Next.js state (`__NEXT_DATA__` or equivalent)
3. visible HTML labels and text blocks

## Output

A `ParseCandidate` with `values`, `evidence`, and warnings.

## Rules

- Preserve raw excerpt for each field.
- Parse dates conservatively.
- Do not infer missing eligibility or benefits.
- Normalize, but do not replace source meaning.

## Implementation

- `src/campus_mate/parsing/html.py`
- `tests/test_html_parser.py`

## Verify

```bash
python -m pytest tests/test_html_parser.py -q
```
