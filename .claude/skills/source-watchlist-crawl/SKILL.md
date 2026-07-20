---
name: source-watchlist-crawl
description: >-
  Linkareer 목록 페이지에서 공고 URL을 수집하고 정규화·중복 제거·실패 격리를 수행한다.
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

# 공고 소스 수집

## 지원 어댑터

- `linkareer`

## 절차

1. 어댑터 존재 여부를 확인합니다.
2. `limit`과 timeout을 적용합니다.
3. HTTP(S) URL을 수집하고 정규화합니다.
4. URL과 안정적인 ID로 중복을 제거합니다.
5. 항목별 조회 실패를 격리합니다.
6. 결과 JSON을 저장합니다.

## 명령

```bash
campus-mate collect --source linkareer --limit 8 \
  --report artifacts/collection-result.json
```

## 출력

- 발견 URL
- 정규화 URL
- 조회 성공 페이지
- 실패 URL과 오류 유형
- 처리 건수

## 제약

- 허용되지 않은 어댑터를 실행하지 않습니다.
- 로그인·anti-bot 제어를 우회하지 않습니다.
- 요청량 제한을 해제하지 않습니다.
