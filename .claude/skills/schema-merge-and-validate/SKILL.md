---
name: schema-merge-and-validate
description: >-
  HTML/OCR/Vision ParseCandidate를 필드별 우선순위와 confidence로 병합하고 conflicts, warnings, parse confidence, NeedsReview 여부를 결정한다.
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

# Schema Merge and Validate

## Merge policy

Read [field-precedence.md](references/field-precedence.md).

1. Merge per field, not per whole document.
2. Prefer structured/HTML evidence.
3. Keep every evidence item even when not selected.
4. Detect incompatible dates/text.
5. Normalize into `Opportunity`.
6. Set warnings and review state.

## Required gate

- title
- source
- source_url
- opportunity_id

## Scheduling gate

A conflicting or missing deadline must not produce an automatic deadline event.

## Verify

```bash
python -m pytest tests/test_multipass.py -q
```
