---
name: source-watchlist-crawl
description: >-
  지원되는 공고 소스의 목록 페이지를 순회해 URL을 정규화·중복 제거하고 수집 성공·실패를 기록한다. 현재 완전 지원 소스는 Linkareer이다.
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

# 공고 소스 순회 수집

## 지원 소스

패키지에 포함된 운영용 어댑터는 현재 `linkareer` 하나입니다.

## 절차

1. `src/campus_mate/sources/`에 해당 수집 어댑터가 실제로 존재하는지 확인합니다.
2. 설정된 최대 수집 개수와 timeout을 적용합니다.
3. HTTP(S) URL을 찾고 정규화합니다.
4. 중복 URL을 제거합니다.
5. URL별 실패를 서로 격리합니다.
6. 수집 결과 보고서를 저장하거나 확인합니다.

## 명령

```bash
campus-mate collect --source linkareer --limit 8 \
  --report artifacts/collection-report.json
```

이 통합 명령은 파싱·점수 계산·저장까지 이어집니다. 수집 단계만 검토할 때는 생성된 보고서를 확인합니다.

## 금지 사항

- 미지원 사이트를 지원한다고 표현하기
- 로그인이나 anti-bot 제어를 우회하기
- 명확한 제한 없이 요청량을 늘리기
