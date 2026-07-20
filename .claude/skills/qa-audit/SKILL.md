---
name: qa-audit
description: >-
  Campus Mate 실행 결과 또는 코드 변경을 검증하는 품질 게이트. Agent 인계와 산출물 완전성, 공고 상태 규칙, 중복 방지, Agent·Skill 구조, 테스트, lint, compile, secret scan을 확인하고 PASS·FAIL 보고서를 작성한다.
user-invocable: false
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - Edit
---

# QA 검증

## 실행 결과 검증

- 필수 단계 산출물이 존재하는지
- 인계 결과의 상태와 경로가 올바른지
- `NeedsReview` 항목이 일정화되지 않았는지
- `Accept`가 아닌 Calendar 요청이 0건인지
- `Scheduled` 항목에 확인된 event ID가 있는지
- 반복 실행으로 공고나 일정 종류가 중복되지 않는지
- 일부 실패 시 성공 결과가 보존됐는지

## 코드 검증

```bash
python -m pytest -q
python scripts/validate_harness.py
python scripts/scan_secrets.py .
python -m compileall -q src scripts .claude/hooks
ruff check src tests scripts .claude/hooks
```

## 보고서

다음 항목을 포함한 간결한 보고서를 작성합니다.

- 실행한 검사
- 검사별 `PASS` 또는 `FAIL`
- 경고
- 정확한 실패 원인과 복구 방법
- 최종 상태: `PASS`, `PASS-WITH-WARNINGS`, `FAIL`

실제 설정된 환경에서 실행하지 않은 Notion, Slack, Calendar, Timely, OCR, Vision 연동을 통과했다고 표현하지 않습니다.
