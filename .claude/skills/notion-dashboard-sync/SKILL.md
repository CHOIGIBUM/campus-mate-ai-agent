---
name: notion-dashboard-sync
description: >-
  Notion schema를 확인하고 안정적인 ID·URL 기반 upsert를 수행하며 사용자 상태·메모·Calendar event ID를 보존한다.
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

[Notion 스키마](references/notion-schema.md)를 적용합니다.

## 사전 조건

- Notion 인증정보 설정
- Integration의 data source 접근 권한
- storage backend가 `notion`

## 절차

1. 누락된 schema 속성만 추가합니다.
2. 안정적인 ID 또는 원문 URL로 기존 페이지를 찾습니다.
3. 신규 페이지를 생성하거나 자동 관리 필드만 갱신합니다.
4. `Accept`, `Hold`, `Reject`, `Scheduling`, `Scheduled`를 보존합니다.
5. 수동 메모와 Calendar event ID를 보존합니다.
6. 오류 상태를 저장합니다.

## 명령

```bash
campus-mate --storage notion notion ensure-schema
```

## 실패 처리

- rate limit·API 오류: 제한된 retry
- 최종 실패: 동기화 오류 저장
- 로컬 산출물 유지
- 전체 페이지 삭제 금지

## 검증

```bash
python -m pytest tests/test_notion_repository.py -q
```
