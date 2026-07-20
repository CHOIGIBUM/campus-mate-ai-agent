---
name: html-opportunity-parse
description: >-
  JSON-LD, Next.js 상태, 화면 HTML에서 공고 필드와 원문 근거를 추출한다.
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

# HTML 공고 파싱

## 출처 순서

1. JSON-LD
2. Next.js 상태 (`__NEXT_DATA__` 등)
3. 화면 HTML의 라벨·텍스트

## 추출 필드

- 제목
- 주최기관
- 마감일·행사일
- 참가 자격
- 제출물
- 혜택
- 포스터 URL

## 규칙

- 필드별 원문 발췌를 저장합니다.
- 날짜를 보수적으로 정규화합니다.
- 누락 정보를 추론하지 않습니다.
- 원문의 의미를 변경하지 않습니다.

## 출력

`values`, `evidence`, `warnings`를 포함한 `ParseCandidate`.

## 구현·검증

- `src/campus_mate/parsing/html.py`
- `python -m pytest tests/test_html_parser.py -q`
