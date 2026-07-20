---
name: notion-dashboard-sync
description: >-
  Notion data source schema를 확인하고 stable ID/URL 기반 비파괴 upsert를 수행하며 사용자 상태·메모·calendar event IDs를 보존한다.
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

# Notion Dashboard Sync

Read [notion-schema.md](references/notion-schema.md).

## Preflight

- Notion credentials exist
- integration has access to the data source
- storage backend is notion

## Schema

```bash
campus-mate --storage notion notion ensure-schema
```

## Upsert rules

- match by stable ID or source URL
- create new, update safe automated fields
- preserve Accept/Hold/Reject/Scheduling/Scheduled
- preserve manual notes and event IDs
- never mass archive/delete

## Failure handling

Rate limit/API failure → bounded retry, then sync error. Do not remove local artifacts.

## Verify

```bash
python -m pytest tests/test_notion_repository.py -q
```
