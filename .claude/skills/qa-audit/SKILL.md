---
name: qa-audit
description: >-
  Agent 인계, 산출물, 공고 상태, 중복 방지, Harness 구조, 테스트, lint, compile, secret scan을 검증한다.
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

## 워크플로 검증

- 필수 단계 산출물 존재
- 인계 객체의 입력·출력 경로 유효
- `NeedsReview` Calendar 요청 없음
- 비승인 공고 Calendar 요청 없음
- `Scheduled` 항목에 성공 event ID 존재
- 재실행 중복 공고·일정 없음
- 일부 실패 시 성공 결과 보존

## 코드 검증

```bash
python -m pytest -q
python scripts/validate_harness.py
python scripts/scan_secrets.py .
python -m compileall -q src scripts .claude/hooks
ruff check src tests scripts .claude/hooks
```

## 출력

`08_qa/qa-result.json`

```json
{
  "status": "PASS",
  "checks": [],
  "warnings": [],
  "errors": []
}
```

상태:

- `PASS`
- `PASS-WITH-WARNINGS`
- `FAIL`

검증 상태는 실제 실행한 검사 결과로만 결정합니다.
