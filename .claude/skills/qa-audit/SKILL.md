---
name: qa-audit
description: >-
  Campus Mate run 또는 코드 변경의 품질 게이트. handoff/artifact 완전성, 상태 불변식, 중복 방지, tests, harness structure, secret scan을 검증하고 PASS/FAIL 보고서를 작성한다.
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

# QA Audit

## Run-level checks

- required phase artifacts exist
- handoff status and paths are valid
- NeedsReview items are not scheduled
- non-Accept calendar requests are zero
- Scheduled items have event IDs
- repeated run does not duplicate records

## Code-level checks

```bash
python -m pytest -q
python scripts/validate_harness.py
python scripts/scan_secrets.py .
python -m compileall -q src scripts
```

## Report

Write a Markdown report with:

- checks run
- PASS/FAIL per check
- warnings
- exact failures and recovery action
- final `PASS`, `PASS-WITH-WARNINGS`, or `FAIL`

Never claim an external integration passed unless it was executed in the configured account.
