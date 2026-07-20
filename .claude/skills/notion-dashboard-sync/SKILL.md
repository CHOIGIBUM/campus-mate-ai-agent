---
name: notion-dashboard-sync
description: >-
  Notion data source schema를 확인하고 안정적인 ID·URL 기반 비파괴 upsert를 수행하며 사용자 상태·메모·Calendar event ID를 보존한다.
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

# Notion 현황판 동기화

먼저 [Notion schema 설명](references/notion-schema.md)을 읽습니다.

## 실행 전 확인

- Notion 인증정보가 설정되어 있는지
- Integration이 data source에 접근할 수 있는지
- 저장 backend가 `notion`인지

## Schema 확인

```bash
campus-mate --storage notion notion ensure-schema
```

## Upsert 규칙

- 안정적인 ID 또는 원문 URL로 기존 항목을 찾습니다.
- 신규 항목은 만들고, 기존 항목은 자동 관리 필드만 안전하게 갱신합니다.
- `Accept`, `Hold`, `Reject`, `Scheduling`, `Scheduled` 상태를 보존합니다.
- 수동 메모와 event ID를 보존합니다.
- 전체 페이지를 일괄 archive·delete하지 않습니다.

## 실패 처리

Rate limit 또는 API 오류가 발생하면 제한된 retry를 수행한 뒤 동기화 오류를 기록합니다. 로컬 산출물은 삭제하지 않습니다.

## 검증

```bash
python -m pytest tests/test_notion_repository.py -q
```
