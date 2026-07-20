---
name: source-watchlist-crawl
description: >-
  지원되는 공고 소스의 목록 페이지를 순회해 URL을 정규화·중복 제거하고 수집 성공/실패를 기록한다. 현재 완전 지원 source는 Linkareer이다.
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

# Source Watchlist Crawl

## Supported source

`linkareer` only in the packaged production adapter.

## Procedure

1. Verify source adapter exists under `src/campus_mate/sources/`.
2. Apply configured limit and timeout.
3. Discover and normalize HTTP(S) URLs.
4. Remove duplicates.
5. Keep per-URL failure isolation.
6. Write or inspect the collection report.

## Command

```bash
campus-mate collect --source linkareer --limit 8 \
  --report artifacts/collection-report.json
```

The integrated command continues through parse/score/upsert; use the report to review the collection portion.

## Do not

- claim unsupported sites
- bypass login or anti-bot controls
- increase load without a clear limit
