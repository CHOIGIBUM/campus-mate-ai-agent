---
name: qa-audit
description: >-
  Campus Mate run 또는 코드 변경의 품질 게이트. handoff와 artifact 완전성, 상태 불변식, 중복 방지, Agent·Skill 구조, tests, lint, compile, secret scan을 검증하고 PASS/FAIL 보고서를 작성한다.
user-invocable: false
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - Edit
---

# QA Audit

## Run-level checks

- required phase artifacts exist
- handoff status and paths are valid
- `NeedsReview` items are not scheduled
- non-Accept calendar requests are zero
- `Scheduled` items have confirmed event IDs
- repeated runs do not duplicate records or event kinds
- partial failures preserve successful results

## Code-level checks

```bash
python -m pytest -q
python scripts/validate_harness.py
python scripts/scan_secrets.py .
python -m compileall -q src scripts .claude/hooks
ruff check src tests scripts .claude/hooks
```

## Report

Write a concise report with:

- checks run
- PASS/FAIL per check
- warnings
- exact failure and recovery action
- final `PASS`, `PASS-WITH-WARNINGS`, or `FAIL`

Never claim Notion, Slack, Calendar, Timely, OCR, or Vision passed unless the configured environment actually executed that integration.
